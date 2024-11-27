from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(CustomUser)
admin.site.register(Item)
admin.site.register(Order)
admin.site.register(ItemPurchase)
