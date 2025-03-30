from django.contrib import admin
from apps.products.models import ProductCategory, ProductSubCategory, ProductSize, Product
# Register your models here.
admin.site.register(Product)
admin.site.register(ProductSubCategory)
admin.site.register(ProductSize)
admin.site.register(ProductCategory)
