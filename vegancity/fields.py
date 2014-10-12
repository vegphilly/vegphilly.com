from south.modelsinspector import add_introspection_rules
from django.contrib.gis.db import models

# This field is in its own module to avoid circular import problems.
class StatusField(models.CharField):
    PENDING = 'pending'
    APPROVED = 'approved'
    QUARANTINED = 'quarantined'
    CHOICES = ((PENDING, 'Pending Approval'),
               (APPROVED, 'Approved'),
               (QUARANTINED, 'Quarantined'))

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 100
        kwargs['default'] = self.PENDING
        kwargs['choices'] = self.CHOICES
        return super(StatusField, self).__init__(*args, **kwargs)

add_introspection_rules([], ["^vegancity\.fields\.StatusField"])
