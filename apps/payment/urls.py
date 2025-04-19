from django.urls import path, include
from .views import PaymentSummaryViewSet, PaymentInitiateViewSet, PaymentSuccessViewSet, PaymentWebhookViewSet


urlpatterns = [
    path('summary/', PaymentSummaryViewSet.as_view({'get': 'list'}), name='payment-summary'),
    path('initiate/', PaymentInitiateViewSet.as_view({'post': 'create'}), name='payment-initiate'),
    path('success/', PaymentSuccessViewSet.as_view({'get': 'confirm'}), name='payment-success'),
]
