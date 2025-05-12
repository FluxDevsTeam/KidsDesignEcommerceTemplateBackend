from rest_framework import serializers

from .models import OrganizationSettings, DeliverySettings, DeveloperSettings
from ..orders.models import Order


class PatchOrderSerializer(serializers.ModelSerializer):
    delivery_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[('PAID', 'Paid'), ('SHIPPED', 'Shipped'), ('DELIVERED', 'Delivered'), ('CANCELLED', 'Cancelled')], write_only=True)

    class Meta:
        model = Order
        fields = ["status", "delivery_date"]


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        fields = ["available_states", "warehouse_state", "phone_number", "customer_support_email", "admin_email", "brand_logo", "facebook", "twitter", "linkedin", "tiktok"]


class OrganizationStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        fields = ["available_states"]


class DeliverySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverySettings
        fields = ["base_fee", "fee_per_km", "weigh_fee", "size_fee"]


class DeveloperSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperSettings
        fields = ["brand_name", "contact_us", "terms_of_service", "backend_base_route", "frontend_base_route", "order_route_frontend", "payment_failed_url"]
