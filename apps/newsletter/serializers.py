from rest_framework import serializers
from .models import Subscriber, NewsletterCampaign


class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ['id', 'email', 'user', 'status', 'preferences', 'subscribed_at', 'last_active_at']
        read_only_fields = ['id', 'subscribed_at', 'last_active_at']


class SubscriberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = ['email', 'user', 'preferences']

    def create(self, validated_data):
        email = validated_data.get('email')
        user = validated_data.get('user')

        # Check if subscriber already exists
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults={'user': user, 'preferences': validated_data.get('preferences', {})}
        )

        if not created and subscriber.status == 'unsubscribed':
            subscriber.status = 'active'
            subscriber.save()

        return subscriber


class NewsletterCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterCampaign
        fields = ['id', 'subject', 'content', 'plain_text_content', 'status', 'recipients_filter', 'sent_at', 'created_at', 'updated_at', 'total_sent', 'open_count', 'click_count', 'bounce_count']
        read_only_fields = ['id', 'sent_at', 'created_at', 'updated_at', 'total_sent', 'open_count', 'click_count', 'bounce_count']


class NewsletterCampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterCampaign
        fields = ['subject', 'content', 'plain_text_content', 'status', 'recipients_filter']


class NewsletterCampaignListSerializer(serializers.ModelSerializer):
    open_rate = serializers.SerializerMethodField()
    click_rate = serializers.SerializerMethodField()

    class Meta:
        model = NewsletterCampaign
        fields = ['id', 'subject', 'status', 'recipients_filter', 'sent_at', 'created_at', 'total_sent', 'open_count', 'click_count', 'bounce_count', 'open_rate', 'click_rate']

    def get_open_rate(self, obj):
        return round(obj.open_rate, 2)

    def get_click_rate(self, obj):
        return round(obj.click_rate, 2)