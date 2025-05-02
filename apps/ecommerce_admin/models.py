from django.db import models
from django.core.exceptions import ValidationError

STATE_CHOICES = (
    ("Lagos", "Lagos"),
    ("Ogun", "Ogun"),
    ("Oyo", "Oyo"),
    ("Osun", "Osun"),
    ("Ondo", "Ondo"),
    ("Ekiti", "Ekiti"),
    ("Edo", "Edo"),
    ("Delta", "Delta"),
    ("Kwara", "Kwara"),
    ("Kogi", "Kogi"),
    ("Niger", "Niger"),
    ("Abuja", "Abuja"),
    ("Kaduna", "Kaduna"),
    ("Kano", "Kano"),
    ("Borno", "Borno"),
    ("Yobe", "Yobe"),
    ("Sokoto", "Sokoto"),
    ("Zamfara", "Zamfara"),
    ("Taraba", "Taraba"),
    ("Gombe", "Gombe"),
    ("Bauchi", "Bauchi"),
    ("Adamawa", "Adamawa"),
    ("Katsina", "Katsina"),
    ("Jigawa", "Jigawa"),
    ("Nasarawa", "Nasarawa"),
    ("Benue", "Benue"),
    ("Kebbi", "Kebbi"),
    ("Bayelsa", "Bayelsa"),
    ("Rivers", "Rivers"),
    ("Akwa Ibom", "Akwa Ibom"),
    ("Cross River", "Cross River"),
    ("Enugu", "Enugu"),
    ("Anambra", "Anambra"),
    ("Abia", "Abia"),
    ("Imo", "Imo"),
    ("Ebonyi", "Ebonyi"),
    ("FCT - Abuja", "FCT - Abuja"),
)


class AdminSettings(models.Model):
    singleton = models.BooleanField(default=True, unique=True, editable=False)
    available_states = models.JSONField(default=list)
    warehouse_state = models.CharField(max_length=50, choices=STATE_CHOICES)
    phone_number = models.CharField(max_length=20)
    customer_support_email = models.EmailField()
    admin_email = models.EmailField()
    brand_logo = models.ImageField(upload_to="brand_logo/")
    facebook = models.CharField(max_length=100, null=True, blank=True)
    instagram = models.CharField(max_length=100, null=True, blank=True)
    twitter = models.CharField(max_length=100, null=True, blank=True)
    linkedin = models.CharField(max_length=100, null=True, blank=True)
    tiktok = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.warehouse_state

    def clean(self):
        if not isinstance(self.available_states, list):
            raise ValidationError("available_states must be a list")
        valid_states = [state[0] for state in STATE_CHOICES]
        invalid_states = [state for state in self.available_states if state not in valid_states]
        if invalid_states:
            raise ValidationError(f"Invalid states: {invalid_states}")

    def save(self, *args, **kwargs):
        self.singleton = True
        super().save(*args, **kwargs)


class DeliverySettings(models.Model):
    singleton = models.BooleanField(default=True, unique=True, editable=False)
    fee_per_km = models.CharField(max_length=20)
    base_fee = models.CharField(max_length=20)
    weigh_fee = models.CharField(max_length=20)

    def __str__(self):
        return self.warehouse_state

    def clean(self):
        if not isinstance(self.available_states, list):
            raise ValidationError("available_states must be a list")
        valid_states = [state[0] for state in STATE_CHOICES]
        invalid_states = [state for state in self.available_states if state not in valid_states]
        if invalid_states:
            raise ValidationError(f"Invalid states: {invalid_states}")

    def save(self, *args, **kwargs):
        self.singleton = True
        super().save(*args, **kwargs)


class DeveloperSettings(models.Model):
    singleton = models.BooleanField(default=True, unique=True, editable=False)
    brand_name = models.CharField(max_length=200)
    contact_us = models.CharField(max_length=200)
    terms_of_service = models.CharField(max_length=200)
    backend_base_route = models.CharField(max_length=200)
    frontend_base_route = models.CharField(max_length=200)
    order_route_frontend = models.CharField(max_length=200)
    payment_failed_url = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        self.singleton = True
        super().save(*args, **kwargs)