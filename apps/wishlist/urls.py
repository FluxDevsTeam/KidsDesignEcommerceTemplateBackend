from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiWishlist
router = DefaultRouter()
router.register("", ApiWishlist, basename="wishlist")

urlpatterns = [
    path("", include(router.urls))
]