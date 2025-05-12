from django.urls import path
from .views import PaymentSummaryViewSet, PaymentInitiateViewSet, PaymentVerifyViewSet, PaymentWebhookViewSet

urlpatterns = [
    path('summary/', PaymentSummaryViewSet.as_view({'get': 'list'}), name='payment-summary'),
    path('initiate/', PaymentInitiateViewSet.as_view({'post': 'create'}), name='payment-initiate'),
    path('verify/', PaymentVerifyViewSet.as_view({'get': 'confirm'}), name='verify-payment'),
    path('webhook/', PaymentWebhookViewSet.as_view({'post': 'create'}), name='payment-webhook'),

]
