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


import random

from django.contrib.gis.db import models
from django.db.models import Count

from djorm_pgfulltext.models import SearchManagerMixIn


class VendorSearchManagerMixin(SearchManagerMixIn):
    def vendor_search(self, *args, **kwargs):
        from models import Vendor
        qs = self.search(*args, **kwargs).values_list('vendor', flat=True)
        # TODO: not sure why this has to be casted to a list, but
        # caused an error without it
        vendors = Vendor.approved_objects.filter(pk__in=list(qs))
        return vendors


class WithVendorsManagerMixin(object):
    """
    Adds a method for conveniently filtering down to only
    objects with approved vendors.
    """
    def with_vendors(self, vendors=None):
        qs = self.filter(vendor__approval_status='approved')

        if not (vendors is None):
            qs = qs.filter(vendor__in=vendors)

        qs = (qs
              .distinct()
              .annotate(vendor_count=Count('vendor'))
              .filter(vendor_count__gt=0)
              .order_by('-vendor_count'))

        return qs


class VendorSearchManager(VendorSearchManagerMixin, models.GeoManager):
    pass


class WithVendorsManager(WithVendorsManagerMixin,
                         models.Manager):
    pass


class TagManager(WithVendorsManagerMixin,
                 VendorSearchManagerMixin,
                 models.Manager):
    pass


class ReviewManager(VendorSearchManagerMixin, models.Manager):

    "Manager class for handling searches by review."

    def pending_approval(self):
        """returns all reviews that are not approved, which are
        otherwise impossible to get in a normal query (for now)."""
        normal_qs = self.get_query_set()
        pending = normal_qs.filter(approved=False)
        return pending


class ApprovedReviewManager(ReviewManager):

    "Manager for approved reviews only."

    def get_query_set(self):
        "Changing initial queryset to ignore approved."
        normal_qs = super(ApprovedReviewManager, self).get_query_set()
        new_qs = normal_qs.filter(approved=True)
        return new_qs


class VendorManager(SearchManagerMixIn, models.GeoManager):

    "Manager class for handling searches by vendor."

    def pending_approval(self):
        """returns all vendors that are not approved, which are
        otherwise impossible to get in a normal query."""
        return self.filter(approval_status='pending')


class ApprovedVendorManager(VendorManager):

    """Manager for approved vendors only.

    Inherits the normal vendor manager."""

    def get_query_set(self):
        normal_qs = super(VendorManager, self).get_query_set()
        new_qs = normal_qs.filter(approval_status='approved')
        return new_qs

    def without_reviews(self):
        from models import Review
        review_vendors = (Review
                          .approved_objects
                          .values_list('vendor_id', flat=True))
        return self.all().exclude(pk__in=review_vendors)

    def with_reviews(self):
        return self.filter(review__approved=True)\
                   .distinct()\
                   .annotate(review_count=Count('review'))\
                   .order_by('-review_count')

    def get_random_unreviewed(self):
        try:
            return random.choice(self.without_reviews())
        except IndexError:
            return None
