from django.utils.functional import SimpleLazyObject
from ..ecommerce_admin.models import OrganizationSettings

organisation_settings = SimpleLazyObject(lambda: OrganizationSettings.objects.first())
available_states = SimpleLazyObject(lambda: organisation_settings.available_states)
warehouse_city = SimpleLazyObject(lambda: organisation_settings.warehouse_state)
