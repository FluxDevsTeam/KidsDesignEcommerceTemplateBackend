from django.db import models

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
    available_states = models.JSONField(default=list)
    warehouse_state = models.CharField(max_length=50, choices=STATE_CHOICES)

    def __str__(self):
        return self.warehouse_state

    def clean(self):
        from django.core.exceptions import ValidationError
        if not isinstance(self.available_states, list):
            raise ValidationError("available_states must be a list")
        valid_states = [state[0] for state in STATE_CHOICES]
        invalid_states = [state for state in self.available_states if state not in valid_states]
        if invalid_states:
            raise ValidationError(f"Invalid states: {invalid_states}")