from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class Package(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    duration_minutes = models.PositiveIntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - ${self.price}"


class Consultation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations')
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='consultations')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text="Additional notes from the user")
    admin_notes = models.TextField(blank=True, help_text="Internal notes from admin")
    zoom_link = models.URLField(blank=True, help_text="Zoom meeting link")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
        unique_together = ['scheduled_date', 'scheduled_time']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.package.name} on {self.scheduled_date}"

    @property
    def is_past(self):
        from django.utils import timezone
        from datetime import datetime
        scheduled_datetime = timezone.datetime.combine(self.scheduled_date, self.scheduled_time, tzinfo=timezone.get_current_timezone())
        return scheduled_datetime < timezone.now()