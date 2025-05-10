from django.contrib import admin
from .models import DeliverySettings, DeveloperSettings, OrganizationSettings


# Register your models here.
admin.site.register(OrganizationSettings)
admin.site.register(DeveloperSettings)
admin.site.register(DeliverySettings)
