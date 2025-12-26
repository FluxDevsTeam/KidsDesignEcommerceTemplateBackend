from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import validate_email

User = get_user_model()


class Subscriber(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('unsubscribed', 'Unsubscribed'),
        ('bounced', 'Bounced'),
    ]

    email = models.EmailField(unique=True, validators=[validate_email])
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='newsletter_subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    preferences = models.JSONField(default=dict, help_text="User preferences for newsletter content")
    subscribed_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return f"{self.email} ({self.status})"


class NewsletterCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('archived', 'Archived'),
    ]

    RECIPIENT_FILTER_CHOICES = [
        ('all', 'All Subscribers'),
        ('active', 'Active Only'),
        ('custom', 'Custom'),
    ]

    subject = models.CharField(max_length=300)
    content = models.TextField(help_text="HTML content for the newsletter")
    plain_text_content = models.TextField(blank=True, help_text="Plain text version")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    recipients_filter = models.CharField(max_length=20, choices=RECIPIENT_FILTER_CHOICES, default='active')
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Stats fields
    total_sent = models.PositiveIntegerField(default=0)
    open_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    bounce_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} ({self.status})"

    @property
    def open_rate(self):
        if self.total_sent == 0:
            return 0
        return (self.open_count / self.total_sent) * 100

    @property
    def click_rate(self):
        if self.total_sent == 0:
            return 0
        return (self.click_count / self.total_sent) * 100