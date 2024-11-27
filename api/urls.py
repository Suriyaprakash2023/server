from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static  
from .views import *
urlpatterns = [
    path('',index,name="index"),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/', UserInfoView.as_view(), name='user'),
    path('add_new_add/', DishCreateView.as_view(), name='add_new_add'),
    path('dishes/', Dishes.as_view(), name='dishes'),
    path('orders/', OrdersView.as_view(), name='orders'),
    path('order-detail/<str:unique_id>/', OrdersView.as_view(), name='orders-detail'),
    path('orders/<str:unique_id>/', OrdersView.as_view(), name='orders-unique_id'),
    path('orders-status/<str:category>/', OrderStatusView.as_view(), name='orders-status'),
    path('dish-details/<str:id>', DishesDetails.as_view(), name='dish-details'),
    path('product-details/<str:id>', ProductDetails.as_view(), name='product-details'),
    path('dishes/<str:category>', CategoryDishesView.as_view(), name='category_dishes'),
    path('new_dishes/', NewDishes.as_view(), name='new_dishes'),
    path('new_orders/', NewOrders.as_view(), name='new_orders'),
    path('shop/', ShopView.as_view(), name='shop'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/<int:cart_item_id>/', CartView.as_view(), name='cart-item-delete'),
    path('purchase-cart-items/', BulkPurchaseView.as_view(), name='purchase-cart-items'),
    path('user-orders/', UserOrdersView.as_view(), name='user-orders'),
    path('user-orders/<int:oredr_id>/', UserOrdersView.as_view(), name='user-orders-update'),
    path('payments/', PaymentView.as_view(), name='payments'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
