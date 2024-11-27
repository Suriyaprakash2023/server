from django.db import models
import random
import string
from django.contrib.auth.models import Group, AbstractUser
from django.db import models, connection
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager

class AlphaNumericFieldfive(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 5  # Set fixed max_length for alphanumeric field
        super().__init__(*args, **kwargs)

    @staticmethod
    def generate_alphanumeric():
        alphanumeric = "".join(
            random.choices(string.ascii_letters + string.digits, k=5)
        )
        return alphanumeric.upper()


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    objects = CustomUserManager()

    username = None
    last_name = None

    email = models.EmailField(_("email address"), unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(max_length=15,unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    image = models.ImageField(blank=True, null=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


    def __str__(self):
        return f"{self.email} - {self.mobile_number}"


groups = [
    "admin",
    "user", # Default group for all users
    "delivary_partner",

]

from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_groups(sender, **kwargs):
    with connection.cursor() as cursor:
        table_names = connection.introspection.table_names(cursor)
        if "auth_group" in table_names:
            for group_name in groups:
                Group.objects.get_or_create(name=group_name)
        else:
            print("auth_group table does not exist, skipping group creation.")



class Item(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    mrp_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    offer_percentage = models.PositiveIntegerField(default=0,blank=True, null=True)
    ratings = models.PositiveIntegerField(default=0,blank=True, null=True )
    category = models.CharField(max_length=100,blank=True, null=True)
    available = models.BooleanField(default=True,blank=True, null=True)
    image = models.ImageField(blank=True,null=True)
    
    # @property
    # def selling_price(self):
    #     discount = (int(self.offer_percentage) / 100) * self.mrp_price
    #     return self.mrp_price - discount

    def __str__(self):
        return f"{self.name} - Selling Price: {self.selling_price}"



class Review(models.Model):
    item = models.ForeignKey(Item, related_name="reviews", on_delete=models.CASCADE)
    name = models.CharField(max_length=100,blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    rating = models.PositiveIntegerField(default=0,blank=True, null=True)
    message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.email}"



class CartItem(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cart_items',blank=True, null=True)
    dish = models.ForeignKey(Item, on_delete=models.CASCADE,blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1,blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically calculate the total price when saving
        self.total_price = self.quantity * self.dish.selling_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.dish.name} (x{self.quantity})"
    


from django.utils.timezone import now
class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='orders',blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0,blank=True, null=True)
    order_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'),('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Canceled', 'Canceled')], default='Pending',blank=True, null=True)
    shipping_time = models.DateTimeField(blank=True, null=True, help_text="Time when the order was shipped.")
    delivery_time = models.DateTimeField(blank=True, null=True, help_text="Time when the order was delivered.")
    delivery_person =models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='delivery_person',blank=True, null=True)
    unique_id = AlphaNumericFieldfive(unique=True, editable=False,null=True, blank=False)
    def update_total_price(self):
        # Calculate the total price based on associated ItemPurchase objects
        self.total_price = sum(item.total_price for item in self.purchases.all())
        self.save()

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = AlphaNumericFieldfive.generate_alphanumeric()
            while Order.objects.filter(unique_id=self.unique_id).exists():
                self.unique_id = AlphaNumericFieldfive.generate_alphanumeric()
        super(Order, self).save(*args, **kwargs)


    def update_status(self, new_status):
        """Update the status and corresponding timestamps."""
        if new_status not in dict(self._meta.get_field('status').choices):
            raise ValueError("Invalid status")

        self.status = new_status

        if new_status == 'Shipped' and not self.shipping_time:
            self.shipping_time = now()
        elif new_status == 'Delivered' and not self.delivery_time:
            self.delivery_time = now()

        self.save()

    def __str__(self):
        return str(self.unique_id)



class ItemPurchase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchases' ,blank=True, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='purchases',blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='purchases',blank=True, null=True)  # Add this field
    quantity = models.PositiveIntegerField(default=1,blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    purchased_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.item.selling_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} purchased {self.quantity} x {self.item.name}"






