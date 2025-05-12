from django.utils.functional import SimpleLazyObject
from ..ecommerce_admin.models import OrganizationSettings, DeliverySettings, DeveloperSettings

organisation_settings = SimpleLazyObject(lambda: OrganizationSettings.objects.first())
delivery_settings = SimpleLazyObject(lambda: DeliverySettings.objects.first())
developer_settings = SimpleLazyObject(lambda: DeveloperSettings.objects.first())

# organisation details
available_states = SimpleLazyObject(lambda: organisation_settings.available_states)
warehouse_city = SimpleLazyObject(lambda: organisation_settings.warehouse_state)
admin_email = SimpleLazyObject(lambda: organisation_settings.admin_email)
brand_logo = SimpleLazyObject(lambda: organisation_settings.brand_logo)

# delivery
fee_per_km = SimpleLazyObject(lambda: delivery_settings.fee_per_km)
base_fee = SimpleLazyObject(lambda: delivery_settings.base_fee)
weight_fee = SimpleLazyObject(lambda: delivery_settings.weigh_fee)
size_fee = SimpleLazyObject(lambda: delivery_settings.size_fee)


backend_base_route = SimpleLazyObject(lambda: developer_settings.backend_base_route)
frontend_base_route = SimpleLazyObject(lambda: developer_settings.frontend_base_route)
order_route_frontend = SimpleLazyObject(lambda: developer_settings.order_route_frontend)
payment_failed_url = SimpleLazyObject(lambda: developer_settings.payment_failed_url)
