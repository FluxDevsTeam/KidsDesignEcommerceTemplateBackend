from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApiAdminOrder, OrderDashboard, ApiOrganizationSettings, ApiDeliverySettings, ApiDeveloperSettings, ApiOrganizationStates

router = DefaultRouter()
router.register("order", ApiAdminOrder, basename="admin_order_page")

urlpatterns = [
    path("", include(router.urls)),
    path('dashboard/', OrderDashboard.as_view({'get': 'retrieve'}), name='admin_dashboard_page'),
    path('organisation-settings/', ApiOrganizationSettings.as_view({'get': 'list', 'patch': 'partial_update'}), name='admin_settings'),
    path('delivery-settings/', ApiDeliverySettings.as_view({'get': 'list', 'patch': 'partial_update'}), name='delivery_settings'),
    path('developer-settings/', ApiDeveloperSettings.as_view({'get': 'list', 'patch': 'partial_update'}), name='developer_settings'),
    path('user/organisation-settings/', ApiOrganizationStates.as_view({'get': 'list'}), name='states_list'),
]
