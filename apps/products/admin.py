from django.contrib import admin
from .models import InventoryItem, InventoryCategory, InventorySubCategory

admin.site.register(InventoryItem)
admin.site.register(InventoryCategory)
admin.site.register(InventorySubCategory)
