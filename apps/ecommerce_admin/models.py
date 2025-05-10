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


# had to set default for everything so the application doesn't crash and for better understanding as it is a template
class OrganizationSettings(models.Model):
    singleton = models.BooleanField(default=True, unique=True, editable=False)
    available_states = models.JSONField(default=list, help_text='["Ogun", "Lagos"]')
    warehouse_state = models.CharField(max_length=50, choices=STATE_CHOICES, default="Lagos")
    phone_number = models.CharField(max_length=20, default="+0123456789")
    customer_support_email = models.EmailField(default="suskidee@gmail.com")
    admin_email = models.EmailField(default="suskidee@gmail.com")
    brand_logo = models.ImageField(upload_to="brand_logo/", null=True, blank=True)
    facebook = models.URLField(max_length=100, null=True, blank=True)
    instagram = models.URLField(max_length=100, null=True, blank=True)
    twitter = models.URLField(max_length=100, null=True, blank=True)
    linkedin = models.URLField(max_length=100, null=True, blank=True)
    tiktok = models.URLField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"organization settings: {self.admin_email}"

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
    fee_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    weigh_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    size_fee = models.DecimalField(max_digits=10, decimal_places=2, default=5000)

    def __str__(self):
        return "delivery settings"

    def save(self, *args, **kwargs):
        self.singleton = True
        super().save(*args, **kwargs)


class DeveloperSettings(models.Model):
    singleton = models.BooleanField(default=True, unique=True, editable=False)
    brand_name = models.CharField(max_length=200, default="Shop.co")
    contact_us = models.URLField(max_length=200, default="https://ecommercetemplateweb.netlify.app/contact-us")
    terms_of_service = models.URLField(max_length=200, default="https://ecommercetemplateweb.netlify.app/terms-of-service")
    backend_base_route = models.URLField(max_length=200, default="https://ecommercetemplate.pythonanywhere.com/")
    frontend_base_route = models.URLField(max_length=200, default="https://ecommercetemplateweb.netlify.app/")
    order_route_frontend = models.URLField(max_length=200, default="https://ecommercetemplate.pythonanywhere.com/orders")
    payment_failed_url = models.URLField(max_length=200, default="https://ecommercetemplate.pythonanywhere.com/order_failed")

    def __str__(self):
        return "developer settings"

    def save(self, *args, **kwargs):
        self.singleton = True
        super().save(*args, **kwargs)
