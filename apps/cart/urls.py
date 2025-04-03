from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ApiCart, ApiCartItem

router = DefaultRouter()
router.register("", ApiCart, basename="cart")
cart_router = NestedDefaultRouter(router, "", lookup='cart')
cart_router.register("items", ApiCartItem, basename="cart_item")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(cart_router.urls)),
]
