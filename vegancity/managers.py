import random

from django.contrib.gis.db import models
from django.db.models import Count

from djorm_pgfulltext.models import SearchManagerMixIn, SearchQuerySet
from django.contrib.gis.db.models.query import GeoQuerySet
from vegancity.fields import StatusField as SF


##########################################################>
# Managers for models that relate to vendor
##########################################################>


class SearchByVendorQuerySet(SearchQuerySet, GeoQuerySet):
    def vendor_search(self, *args, **kwargs):
        from models import Vendor
        qs = self.search(*args, **kwargs).values_list('vendor', flat=True)
        # TODO: not sure why this has to be casted to a list, but
        # caused an error without it
        vendors = Vendor.objects.approved().filter(pk__in=list(qs))
        return vendors

    def with_vendors(self, vendors=None):
        qs = self.filter(vendor__approval_status=SF.APPROVED)

        if not (vendors is None):
            qs = qs.filter(vendor__in=vendors)

        qs = (qs
              .distinct()
              .annotate(vendor_count=Count('vendor'))
              .filter(vendor_count__gt=0)
              .order_by('-vendor_count'))

        return qs


class SearchByVendorManager(SearchManagerMixIn, models.Manager):
    def get_queryset(self):
        return SearchByVendorQuerySet(model=self.model, using=self._db)

    # TODO: use a better pass-thru mechanism to avoid
    # repeating these qs methods on the manager

    def vendor_search(self, *args, **kwargs):
        return self.get_queryset().vendor_search(*args, **kwargs)

    def with_vendors(self, *args, **kwargs):
        return self.get_queryset().with_vendors(*args, **kwargs)


class ReviewManager(SearchByVendorManager):
    def approved(self):
        return self.get_queryset().filter(approval_status=SF.APPROVED)

    def pending_approval(self):
        """returns all reviews that are not approved, which are
        otherwise impossible to get in a normal query (for now)."""
        normal_qs = self.get_queryset()
        pending = normal_qs.filter(approval_status=SF.PENDING)
        return pending


class VendorQuerySet(GeoQuerySet, SearchQuerySet):
    def pending_approval(self):
        """returns all vendors that are not approved, which are
        otherwise impossible to get in a normal query."""
        return self.filter(approval_status=SF.PENDING)

    def approved(self):
        return self.filter(approval_status=SF.APPROVED)

    def without_reviews(self):
        from models import Review
        review_vendors = (Review
                          .objects.approved()
                          .values_list('vendor_id', flat=True))
        return self.all().exclude(pk__in=review_vendors)

    def with_reviews(self):
        return self.filter(review__approval_status=SF.APPROVED)\
                   .distinct()\
                   .annotate(review_count=Count('review'))\
                   .order_by('-review_count')

    def get_random_unreviewed(self):
        try:
            return random.choice(self.without_reviews())
        except IndexError:
            return None


class VendorManager(SearchManagerMixIn, models.GeoManager):
    def get_queryset(self):
        return VendorQuerySet(model=self.model, using=self._db)

    # TODO: use a better pass-thru mechanism to avoid
    # repeating these qs methods on the manager
    def search(self, *args, **kwargs):
        return self.get_queryset().search(*args, **kwargs)

    def approved(self):
        return self.get_queryset().approved()

    def pending_approval(self):
        return self.get_queryset().pending_approval()
