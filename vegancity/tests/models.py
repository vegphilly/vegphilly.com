from mock import Mock

from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point

from django.test import TestCase

from vegancity import email, geocode
from vegancity.models import Review, Vendor, Neighborhood
from vegancity.tests.utils import get_user
from vegancity.fields import StatusField as SF


class WithVendorsManagerTest(TestCase):

    def setUp(self):
        self.n1 = Neighborhood.objects.create(name="Logan Square")
        self.n2 = Neighborhood.objects.create(name="Pilsen")

        self.v1 = Vendor.objects.create(name="Test Vendor",
                                        neighborhood=self.n1,
                                        approval_status=SF.APPROVED)
        self.v2 = Vendor.objects.create(name="Test Vendor 2",
                                        neighborhood=self.n2,
                                        approval_status=SF.APPROVED)

    def assertCounts(self, vendors, with_vendors_count, without_vendors_count):
        self.assertEqual(with_vendors_count,
                         Neighborhood.objects.with_vendors(vendors).count())
        self.assertEqual(without_vendors_count,
                         Neighborhood.objects.with_vendors().count())

    def test_no_vendors_returns_none(self):
        Vendor.objects.all().delete()
        vendors = Vendor.objects.all()
        self.assertCounts(vendors, 0, 0)

    def test_initial_vendors_empty_queryset(self):
        vendors = Vendor.objects.none()
        self.assertCounts(vendors, 0, 2)

    def test_initial_vendors_limited_queryset(self):
        vendors = Vendor.objects.filter(pk=self.v1.pk)
        self.assertCounts(vendors, 1, 2)

    def test_initial_vendors_complete_queryset(self):
        vendors = Vendor.objects.all()
        self.assertCounts(vendors, 2, 2)


class VendorGeocodeTest(TestCase):

    def setUp(self):
        self.user = get_user()

    def test_no_address_no_geocode(self):
        vendor = Vendor(name="Test Vendor")
        vendor.save()

        self.assertEqual(vendor.location, None)
        self.assertEqual(vendor.neighborhood, None)
        self.assertFalse(vendor.needs_geocoding())

    def test_address_causes_geocode(self):
        geocode.geocode_address = Mock(return_value=(100, 100, "South Philly"))
        vendor = Vendor(
            name="Test Vendor",
            address="300 Christian St, Philadelphia, PA, 19147")

        vendor.save()

        self.assertNotEqual(vendor.location, None)
        self.assertNotEqual(vendor.neighborhood, None)

    def test_needs_geocoding(self):
        vendor = Vendor(name="Test Vendor")
        self.assertFalse(vendor.needs_geocoding())

        vendor.address = "300 Christian St, Philadelphia, PA, 19147"
        self.assertTrue(vendor.needs_geocoding())

        vendor.save()
        self.assertFalse(vendor.needs_geocoding())

    def run_apply_geocoding_test(self, geocoder_return_value,
                                 location, neighborhood):
        geocode.geocode_address = Mock(return_value=geocoder_return_value)
        vendor = Vendor(name="Test Vendor", address="123 Main Street")
        vendor.save()
        vendor.apply_geocoding()
        self.assertEqual(vendor.location, location)
        if neighborhood:
            self.assertEqual(vendor.neighborhood.name, neighborhood)
        else:
            self.assertEqual(vendor.neighborhood, neighborhood)

    def test_apply_geocoding_fails_gracefully(self):
        self.run_apply_geocoding_test(
            geocoder_return_value=(None, None, None),
            location=None,
            neighborhood=None)

    def test_apply_geocoding_with_weird_input(self):
        self.run_apply_geocoding_test(
            geocoder_return_value=(None, None, "South Philly"),
            location=None,
            neighborhood=None)

    def test_apply_geocoding_without_neighborhood(self):
        self.run_apply_geocoding_test(
            geocoder_return_value=(100, 100, None),
            location=Point(100, 100, srid=4326),
            neighborhood=None)

    def test_apply_geocoding_with_neighborhood(self):
        self.run_apply_geocoding_test(
            geocoder_return_value=(100, 100, "South Philly"),
            location=Point(100, 100, srid=4326),
            neighborhood="South Philly")


class VendorManagerTest(TestCase):

    def test_pending_approval_no_vendors(self):
        self.assertEqual(0,
                         Vendor.objects.pending_approval().count())

    def test_pending_approval_none_approved(self):
        Vendor.objects.create(name="Test Vendor 1")
        Vendor.objects.create(name="Test Vendor 2")
        self.assertEqual(2,
                         Vendor.objects.pending_approval().count())

    def test_pending_approval_some_approved(self):
        Vendor.objects.create(name="Test Vendor 1",
                              approval_status=SF.APPROVED)
        Vendor.objects.create(name="Test Vendor 2")
        self.assertEqual(1,
                         Vendor.objects.pending_approval().count())

    def test_pending_approval_all_approved(self):
        Vendor.objects.create(name="Test Vendor 1",
                              approval_status=SF.APPROVED)
        Vendor.objects.create(name="Test Vendor 2",
                              approval_status=SF.APPROVED)
        self.assertEqual(0,
                         Vendor.objects.pending_approval().count())


class VendorApprovedManagerTest(TestCase):

    def assertVendorCounts(self, without_count, with_count):
        self.assertEqual(without_count,
                         Vendor.objects.approved().without_reviews().count())
        self.assertEqual(with_count,
                         Vendor.objects.approved().with_reviews().count())

    def test_with_without_reviews_no_vendors(self):
        self.assertVendorCounts(0, 0)

    def test_with_without_reviews_no_reviews(self):
        Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        Vendor.objects.create(name='tv2', approval_status=SF.APPROVED)
        self.assertVendorCounts(2, 0)

    def test_with_without_reviews_no_approved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        Vendor.objects.create(name='tv2', approval_status=SF.APPROVED)
        Review.objects.create(vendor=v1, author=get_user())
        self.assertVendorCounts(2, 0)

    def test_with_without_review_with_some_approved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        v2 = Vendor.objects.create(name='tv2', approval_status=SF.APPROVED)
        Review.objects.create(vendor=v1, approval_status=SF.APPROVED,
                              author=get_user())
        Review.objects.create(vendor=v2, approval_status=SF.PENDING,
                              author=get_user())
        self.assertVendorCounts(1, 1)

    def test_with_without_review_with_all_approved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        v2 = Vendor.objects.create(name='tv2', approval_status=SF.APPROVED)
        Review.objects.create(vendor=v1, approval_status=SF.APPROVED,
                              author=get_user())
        Review.objects.create(vendor=v2, approval_status=SF.APPROVED,
                              author=get_user())
        self.assertVendorCounts(0, 2)

    def test_get_random_unreviewed_no_vendors(self):
        self.assertEqual(None,
                         Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_no_unreviewed_vendors(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        Review.objects.create(vendor=v1,  approval_status=SF.APPROVED,
                              author=get_user())
        self.assertEqual(None,
                         Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_with_only_unapproved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        Review.objects.create(vendor=v1, approval_status=SF.PENDING,
                              author=get_user())
        self.assertEqual(v1, Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_one_vendor(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        self.assertEqual(v1, Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_multiple_unreviewed_vendor(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        v2 = Vendor.objects.create(name='tv2', approval_status=SF.APPROVED)
        self.assertIn(Vendor.objects.approved().get_random_unreviewed(),
                      [v1, v2])

    def test_get_random_unreviewed_mixed_unreviewed_vendors_and_reviewed(self):
        v1 = Vendor.objects.create(name='tv1', approval_status=SF.APPROVED)
        v2 = Vendor.objects.create(name='tv2', approval_status=SF.APPROVED)
        v3 = Vendor.objects.create(name='tv3', approval_status=SF.APPROVED)
        Review.objects.create(vendor=v1, approval_status=SF.APPROVED,
                              author=get_user())
        self.assertIn(Vendor.objects.approved().get_random_unreviewed(),
                      [v2, v3])


class VendorModelTest(TestCase):

    def setUp(self):
        self.user = get_user()

    def test_food_and_atmosphere_rating(self):
        vendor = Vendor(name="Test Vendor")
        vendor.save()

        self.assertEqual(vendor.food_rating(), None)
        self.assertEqual(vendor.atmosphere_rating(), None)

        Review(vendor=vendor,
               approval_status=SF.APPROVED,
               food_rating=1,
               atmosphere_rating=1,
               author=self.user).save()

        self.assertEqual(vendor.food_rating(), 1)
        self.assertEqual(vendor.atmosphere_rating(), 1)

        review2 = Review(vendor=vendor,
                         approval_status=SF.PENDING,
                         food_rating=4,
                         atmosphere_rating=4,
                         author=self.user)
        review2.save()

        self.assertEqual(vendor.food_rating(), 1)
        self.assertEqual(vendor.atmosphere_rating(), 1)

        review2.approval_status = SF.APPROVED
        review2.save()

        # Floored Average
        self.assertEqual(vendor.food_rating(), 2)
        self.assertEqual(vendor.atmosphere_rating(), 2)

        review3 = Review(vendor=vendor,
                         approval_status=SF.APPROVED,
                         food_rating=4,
                         atmosphere_rating=4,
                         author=self.user)
        review3.save()

        # Floored Average
        self.assertEqual(vendor.food_rating(), 3)
        self.assertEqual(vendor.atmosphere_rating(), 3)

    def test_approved_reviews_with_approved(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status=SF.APPROVED)
        r = Review.objects.create(vendor=v, author=self.user,
                                  approval_status=SF.APPROVED)
        self.assertIn(r, v.approved_reviews())

    def test_approved_reviews_with_unapproved(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status=SF.APPROVED)
        r = Review.objects.create(vendor=v, author=self.user)
        self.assertNotIn(r, v.approved_reviews())

    def test_approved_reviews_with_none(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status=SF.APPROVED)
        self.assertEqual(v.approved_reviews().count(), 0)

    def test_unicode_method(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status=SF.APPROVED)
        self.assertEqual(str(v), "test vendor")

    def test_validate_pending(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status=SF.APPROVED)
        v.approval_status = SF.PENDING
        self.assertRaises(ValidationError, v.save)


class VendorEmailTest(TestCase):

    def setUp(self):
        # mock the email function so that we can just see if it's called
        email.send_new_vendor_approval = Mock()
        self.user = get_user()
        self.user.email = "test@test.com"
        self.user.save()

    def test_newly_approved_vendor_gets_emailed(self):
        """
        Test that the email function is called once when a vendor is approved
        and then not again if its approval status changes, even if to approved.
        """

        # not called because it is not yet approved
        vendor = Vendor(name="The Test Vendor",
                        address="123 Main St",
                        submitted_by=self.user)
        vendor.save()
        email.send_new_vendor_approval.assert_not_called()

        # called now because it was approved
        vendor.approval_status = SF.APPROVED
        vendor.save()
        email.send_new_vendor_approval.assert_called_with(vendor)

        # reset mock function to test it doesn't get called again
        email.send_new_vendor_approval.reset_mock()

        # not called when approval status changes away from approved
        vendor.approval_status = SF.QUARANTINED
        vendor.save()
        email.send_new_vendor_approval.assert_not_called()

        # not called when approval status is changed back to approved
        vendor.approval_status = SF.APPROVED
        vendor.save()
        email.send_new_vendor_approval.assert_not_called()
