from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .dashboard import OrderDashboard
from .views import ApiOrder, ApiAdminOrder

router = DefaultRouter()
router.register("admin", ApiAdminOrder, basename="admin_order_page")
router.register("item", ApiOrder, basename="order-item")
# order_router = NestedDefaultRouter(router, "", lookup='order')
# order_router.register("items", ApiOrderItem, basename="order_item")

urlpatterns = [
    path("", include(router.urls)),
    path('admin-dashboard/', OrderDashboard.as_view({'get': 'retrieve'}), name='admin_dashboard_page'),
    # path("", include(order_router.urls)),
]
