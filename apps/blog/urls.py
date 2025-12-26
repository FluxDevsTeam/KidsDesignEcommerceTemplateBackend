from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiBlogCategory, ApiBlogTag, ApiBlogPost

router = DefaultRouter()
router.register("categories", ApiBlogCategory, basename="blog_category")
router.register("tags", ApiBlogTag, basename="blog_tag")
router.register("posts", ApiBlogPost, basename="blog_post")

urlpatterns = [
    path("", include(router.urls)),
]