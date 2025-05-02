from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiOrder

router = DefaultRouter()
router.register("item", ApiOrder, basename="order-item")

urlpatterns = [
    path("", include(router.urls)),
]
