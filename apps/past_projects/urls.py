from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiProjectCategory, ApiPastProject

router = DefaultRouter()
router.register("categories", ApiProjectCategory, basename="project_category")
router.register("", ApiPastProject, basename="past_project")

urlpatterns = [
    path("", include(router.urls)),
]