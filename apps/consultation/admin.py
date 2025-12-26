from django.contrib import admin
from .models import Package, Consultation


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_minutes', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['user', 'package', 'scheduled_date', 'scheduled_time', 'status', 'is_past']
    list_filter = ['status', 'scheduled_date', 'package']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'package__name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['confirm_consultations', 'cancel_consultations', 'complete_consultations']

    def confirm_consultations(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} consultation(s) confirmed")

    def cancel_consultations(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} consultation(s) cancelled")

    def complete_consultations(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} consultation(s) completed")

    confirm_consultations.short_description = "Confirm selected consultations"
    cancel_consultations.short_description = "Cancel selected consultations"
    complete_consultations.short_description = "Mark selected consultations as completed"