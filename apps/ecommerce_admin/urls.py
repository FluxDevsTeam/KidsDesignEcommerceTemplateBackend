from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiAdminOrder, OrderDashboard

router = DefaultRouter()
router.register("order", ApiAdminOrder, basename="admin_order_page")

urlpatterns = [
    path("", include(router.urls)),
    path('ecommerce_admin-dashboard/', OrderDashboard.as_view({'get': 'retrieve'}), name='admin_dashboard_page'),
]
