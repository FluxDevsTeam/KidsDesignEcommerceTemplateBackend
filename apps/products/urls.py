from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ApiInventoryCategory, ApiInventorySubCategory, ApiInventoryItem, ApiProductSize

router = DefaultRouter()
router.register("sub-category", ApiInventorySubCategory, basename="inventory_sub_category")
router.register("category", ApiInventoryCategory, basename="inventory_category")
router.register("item", ApiInventoryItem, basename="inventory_items")

product_router = NestedDefaultRouter(router, 'item', lookup='item')
product_router.register('size', ApiProductSize, basename='product_size')

urlpatterns = [
    path("", include(router.urls)),
    path("", include(product_router.urls))
]
