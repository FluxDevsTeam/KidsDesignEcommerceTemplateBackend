from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentSummaryViewSet, PaymentInitiateViewSet, PaymentSuccessViewSet, PaymentWebhookViewSet

router = DefaultRouter()
router.register("summary", PaymentSummaryViewSet, basename="payment-summary")
router.register("initiate", PaymentInitiateViewSet, basename="payment-initiate")
router.register("success", PaymentSuccessViewSet, basename="payment-success")
router.register("webhook", PaymentWebhookViewSet, basename="payment-webhook")

urlpatterns = [
    path("", include(router.urls)),
]
