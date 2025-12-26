from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, time
from .models import Package, Consultation


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['id', 'name', 'description', 'duration_minutes', 'price', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConsultationSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    package_name = serializers.CharField(source='package.name', read_only=True)
    package_price = serializers.DecimalField(source='package.price', max_digits=10, decimal_places=2, read_only=True)
    is_past = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields = ['id', 'user', 'user_name', 'package', 'package_name', 'package_price', 'scheduled_date', 'scheduled_time', 'status', 'notes', 'admin_notes', 'zoom_link', 'created_at', 'updated_at', 'is_past']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_name', 'package_name', 'package_price', 'is_past']

    def get_is_past(self, obj):
        return obj.is_past

    def validate(self, data):
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')

        if scheduled_date and scheduled_time:
            # Check if the date/time is in the past
            scheduled_datetime = timezone.datetime.combine(scheduled_date, scheduled_time, tzinfo=timezone.get_current_timezone())
            if scheduled_datetime <= timezone.now():
                raise serializers.ValidationError("Cannot schedule consultation in the past.")

            # Check for time slot conflicts (assuming consultations are scheduled in 30-min slots)
            # This is a simplified check - in production, you'd want more sophisticated slot management
            existing_consultations = Consultation.objects.filter(
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status__in=['pending', 'confirmed']
            ).exclude(id=getattr(self.instance, 'id', None))

            if existing_consultations.exists():
                raise serializers.ValidationError("This time slot is already booked.")

        return data


class ConsultationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = ['package', 'scheduled_date', 'scheduled_time', 'notes']

    def validate(self, data):
        # Same validation as above
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')

        if scheduled_date and scheduled_time:
            scheduled_datetime = timezone.datetime.combine(scheduled_date, scheduled_time, tzinfo=timezone.get_current_timezone())
            if scheduled_datetime <= timezone.now():
                raise serializers.ValidationError("Cannot schedule consultation in the past.")

            existing_consultations = Consultation.objects.filter(
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                status__in=['pending', 'confirmed']
            )

            if existing_consultations.exists():
                raise serializers.ValidationError("This time slot is already booked.")

        return data

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)