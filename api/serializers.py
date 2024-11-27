from django.contrib.auth.models import Group
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import *

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('mobile_number', 'email', 'password')  # Include 'email' if it's a unique identifier

    def validate_email(self, value):
        # Check if the email already exists
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        
        # Save the user first to get an ID
        user.save()

        # Add the user to the default 'user' group
        user_group, created = Group.objects.get_or_create(name='user')
        user.groups.add(user_group)
        
        return user



class LoginSerializer(serializers.Serializer):
    mobile_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        mobile_number = data.get("mobile_number")
        password = data.get("password")

        if mobile_number and password:
            try:
                # Find user by mobile number
                user = CustomUser.objects.get(mobile_number=mobile_number)
                # Check if password matches
                if not user.check_password(password):
                    raise serializers.ValidationError("Invalid mobile number or password.")
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Invalid mobile number or password.")
        else:
            raise serializers.ValidationError("Both mobile number and password are required.")

        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ("mobile_number", "name", "email", "address", "city","groups")



class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
             'id','name', 'description', 'mrp_price', 'selling_price', 
            'offer_percentage', 'ratings', 'category', 'image','available'
        ]

class CartItemSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish.name', read_only=True)
    dish_price = serializers.DecimalField(source='dish.selling_price', max_digits=10, decimal_places=2, read_only=True)
    dish_image = serializers.ImageField(source='dish.image', read_only=True)
    # total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'user', 'dish', 'dish_name','dish_image', 'dish_price', 'quantity', 'total_price']
        

class AddtoCartSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish.name', read_only=True)
    dish_price = serializers.DecimalField(source='dish.selling_price', max_digits=10, decimal_places=2, read_only=True)
    dish_image = serializers.ImageField(source='dish.image', read_only=True)
    # total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'user', 'dish', 'dish_name','dish_image', 'dish_price', 'quantity', 'total_price']



class CartItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)


class BulkPurchaseSerializer(serializers.Serializer):
    cart_items = serializers.ListField(
        child=CartItemSerializer(),  # Nested serializer to validate each cart item
        error_messages={'required': 'Cart items are required for bulk purchase.'}
    )

    def validate_cart_items(self, value):
        if not value:
            raise serializers.ValidationError("No cart items provided for purchase.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
     
        order = Order.objects.create(user=user)
        purchases = []
        
        for cart_item_data in validated_data['cart_items']:

            print(cart_item_data['id'],"cart_item_data['id']")
            # Fetch the CartItem
            cart_item = CartItem.objects.filter(id=cart_item_data['id'], user=user).first()
         
            if not cart_item:
                raise serializers.ValidationError(
                    f"Cart item with ID {cart_item_data['id']} not found or doesn't belong to the user."
                )
            
 
            
            # Create purchase entry
            purchase = ItemPurchase.objects.create(
                user = user,
                order=order,
                item=cart_item.dish,
                quantity=cart_item_data['quantity'],
                total_price=cart_item.dish.selling_price * cart_item_data['quantity'],
            )
            purchases.append(purchase)

            # Optionally delete cart items after purchase
            cart_item.delete()

        # Update order total price
        order.update_total_price()

        return order


class ItemPurchaseSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='item.name', read_only=True)  # Dish name from the related Item model
    dish_image = serializers.ImageField(source='item.image', read_only=True)  # Dish image from the related Item model
    dish_category = serializers.CharField(source='item.category', read_only=True)  # Dish image from the related Item model
    dish_ratings = serializers.IntegerField(source='item.ratings', read_only=True)  # Dish ratings from related Item model

    class Meta:
        model = ItemPurchase
        fields = ['dish_name','dish_category','dish_ratings', 'dish_image', 'quantity', 'total_price']
        depth = 1


class OrderSerializer(serializers.ModelSerializer):
    purchases = ItemPurchaseSerializer(many=True, read_only=True)  # Include related ItemPurchase objects

    class Meta:
        model = Order
        fields = ['unique_id', 'total_price', 'status',  'order_at',"shipping_time","delivery_time", 'purchases']


class AdminOrderSerializer(serializers.ModelSerializer):
    purchases = ItemPurchaseSerializer(many=True, read_only=True)  # Include related ItemPurchase objects
    user =UserSerializer(read_only=True)
    delivery_person = UserSerializer(read_only=True)
    class Meta:
        model = Order
        fields = ['unique_id', 'delivery_person','total_price','user', 'status', 'order_at',"shipping_time","delivery_time", 'purchases']