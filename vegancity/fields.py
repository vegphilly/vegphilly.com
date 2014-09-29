# Copyright (C) 2014 Steve Lamb

# This file is part of Vegancity.

# Vegancity is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Vegancity is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Vegancity.  If not, see <http://www.gnu.org/licenses/>.

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
