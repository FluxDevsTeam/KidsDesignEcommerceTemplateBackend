from django.db import models


class AdminSettings(models.Model):
    available_states = models.CharField()
    