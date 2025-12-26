from django.contrib import admin
from .models import Package, PackageTag


@admin.register(PackageTag)
class PackageTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'undiscounted_price', 'is_active', 'is_featured', 'duration_days', 'created_at']
    list_filter = ['is_active', 'is_featured', 'created_at']
    search_fields = ['name', 'description', 'short_description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description')
        }),
        ('Images', {
            'fields': ('image1', 'image2', 'image3', 'image4', 'image5')
        }),
        ('Pricing', {
            'fields': ('price', 'undiscounted_price')
        }),
        ('Tags & Categories', {
            'fields': ('tags',)
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured', 'featured_position', 'duration_days', 'includes', 'requirements')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )