from django.db import models

# Define state choices from the state_coords dictionary
state_choices = [(state, state) for state in state_coords.keys()]

class AdminSettings(models.Model):
    # Use ListField if you have a custom ListField implementation, otherwise consider alternatives
    available_states = models.CharField(max_length=255, choices=state_choices)  # For multiple selections, you might need a different approach
    warehouse_state = models.CharField(max_length=50, choices=state_choices)

    def __str__(self):
        return self.warehouse_state