from django.contrib import admin
from .models import DeliverySettings, DeveloperSettings, AdminSettings
# Register your models here.
admin.site.register(AdminSettings)
admin.site.register(DeveloperSettings)
admin.site.register(DeliverySettings)
