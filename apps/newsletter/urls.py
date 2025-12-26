from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiNewsletterSubscriber, ApiNewsletterCampaign

router = DefaultRouter()
router.register("subscribers", ApiNewsletterSubscriber, basename="newsletter_subscriber")
router.register("campaigns", ApiNewsletterCampaign, basename="newsletter_campaign")

urlpatterns = [
    path("", include(router.urls)),
]