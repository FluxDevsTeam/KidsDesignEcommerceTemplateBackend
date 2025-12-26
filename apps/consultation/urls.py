from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiConsultationPackage, ApiConsultation

router = DefaultRouter()
router.register("packages", ApiConsultationPackage, basename="consultation_package")
router.register("", ApiConsultation, basename="consultation")

urlpatterns = [
    path("", include(router.urls)),
]