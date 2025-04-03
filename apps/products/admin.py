from django.contrib import admin
from .models import ProductSize, Product, ProductSubCategory, ProductCategory

admin.site.register(ProductSize)
admin.site.register(Product)
admin.site.register(ProductSubCategory)
admin.site.register(ProductCategory)
