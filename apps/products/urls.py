from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ApiProductCategory, ApiProductSubCategory, ApiProduct, ApiProductSize

router = DefaultRouter()
router.register("sub-category", ApiProductSubCategory, basename="product_sub_category")
router.register("category", ApiProductCategory, basename="product_category")
router.register("item", ApiProduct, basename="product_items")
router.register("size", ApiProductSize, basename="product_size")

product_router = NestedDefaultRouter(router, 'item', lookup='item')
product_router.register('size', ApiProductSize, basename='product_size')

urlpatterns = [
    path("", include(router.urls)),
    path("", include(product_router.urls))
]
