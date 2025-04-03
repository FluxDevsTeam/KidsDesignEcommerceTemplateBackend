from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import ApiOrder, ApiOrderItem

router = DefaultRouter()
router.register("", ApiOrder, basename="order")
order_router = NestedDefaultRouter(router, "", lookup='order')
order_router.register("items", ApiOrderItem, basename="order_item")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(order_router.urls)),
]
