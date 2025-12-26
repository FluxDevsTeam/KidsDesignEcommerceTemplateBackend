from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiPackageTag, ApiPackage

router = DefaultRouter()
router.register("tags", ApiPackageTag, basename="package_tag")
router.register("", ApiPackage, basename="package")

urlpatterns = [
    path("", include(router.urls)),
]