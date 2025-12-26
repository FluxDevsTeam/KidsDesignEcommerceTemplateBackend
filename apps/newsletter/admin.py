from django.contrib import admin
from .models import Subscriber, NewsletterCampaign


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'status', 'subscribed_at', 'last_active_at']
    list_filter = ['status', 'subscribed_at']
    search_fields = ['email', 'user__username', 'user__email']
    readonly_fields = ['subscribed_at', 'last_active_at']


@admin.register(NewsletterCampaign)
class NewsletterCampaignAdmin(admin.ModelAdmin):
    list_display = ['subject', 'status', 'recipients_filter', 'sent_at', 'total_sent', 'open_count', 'click_count']
    list_filter = ['status', 'recipients_filter', 'sent_at']
    search_fields = ['subject', 'content']
    readonly_fields = ['sent_at', 'created_at', 'updated_at', 'total_sent', 'open_count', 'click_count', 'bounce_count']
    actions = ['send_campaign']

    def send_campaign(self, request, queryset):
        for campaign in queryset:
            if campaign.status != 'sent':
                from .tasks import send_newsletter_campaign
                send_newsletter_campaign.delay(campaign.id)
                campaign.status = 'sent'
                campaign.sent_at = timezone.now()
                campaign.save()
        self.message_user(request, f"Initiated sending for {queryset.count()} campaign(s)")

    send_campaign.short_description = "Send selected campaigns"