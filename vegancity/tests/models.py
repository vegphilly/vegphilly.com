from mock import Mock

from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point

from django.test import TestCase

from vegancity import email, geocode
from vegancity.models import Review, Vendor, Neighborhood, VeganDish
from vegancity.tests.utils import get_user


class VendorVeganDishValidationTest(TestCase):

    """
    Tests that trying to delete vegan dish relationships for
    vendors that have reviews will signal an error.
    """

    def setUp(self):
        self.user = get_user()

        self.vendor = Vendor(name="Test Vendor",
                             address="123 Main St")
        self.vendor.save()

        self.vegan_dish1 = VeganDish(name="Tofu Scramble")
        self.vegan_dish1.save()

        self.vegan_dish2 = VeganDish(name="Tempeh Hash")
        self.vegan_dish2.save()

        self.review1 = Review(vendor=self.vendor,
                              author=self.user,
                              content="ahhhh")
        self.review1.save()

        self.vendor.vegan_dishes.add(self.vegan_dish1)
        self.vendor.vegan_dishes.add(self.vegan_dish2)

    def test_can_delete_relationship_without_any_reviews(self):
        self.assertEqual(self.vendor.vegan_dishes.count(), 2)

        self.vendor.vegan_dishes.remove(self.vegan_dish1)

        self.assertEqual(self.vendor.vegan_dishes.count(), 1)

    def test_can_delete_relationship_with_reviews_on_other_vegan_dish(self):
        self.review1.best_vegan_dish = self.vegan_dish1
        self.review1.save()

        self.assertEqual(self.vendor.vegan_dishes.count(), 2)

        self.vendor.vegan_dishes.remove(self.vegan_dish2)

        self.assertEqual(self.vendor.vegan_dishes.count(), 1)

    def test_can_clear_relationship_without_any_reviews(self):
        self.assertEqual(self.vendor.vegan_dishes.count(), 2)

        self.vendor.vegan_dishes.clear()

        self.assertEqual(self.vendor.vegan_dishes.count(), 0)

    def test_cant_clear_relationship_with_any_reviews(self):
        self.review1.best_vegan_dish = self.vegan_dish1
        self.review1.save()

        self.assertRaises(ValidationError, self.vendor.vegan_dishes.clear)

    def test_cant_delete_relationship_with_reviews(self):
        self.review1.best_vegan_dish = self.vegan_dish1
        self.review1.save()

        self.assertRaises(ValidationError,
                          self.vendor.vegan_dishes.remove,
                          self.vegan_dish1)


class WithVendorsManagerTest(TestCase):

    def setUp(self):
        self.n1 = Neighborhood.objects.create(name="Logan Square")
        self.n2 = Neighborhood.objects.create(name="Pilsen")

        self.v1 = Vendor.objects.create(name="Test Vendor",
                                        neighborhood=self.n1,
                                        approval_status='approved')
        self.v2 = Vendor.objects.create(name="Test Vendor 2",
                                        neighborhood=self.n2,
                                        approval_status='approved')

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
                              approval_status='approved')
        Vendor.objects.create(name="Test Vendor 2")
        self.assertEqual(1,
                         Vendor.objects.pending_approval().count())

    def test_pending_approval_all_approved(self):
        Vendor.objects.create(name="Test Vendor 1",
                              approval_status='approved')
        Vendor.objects.create(name="Test Vendor 2",
                              approval_status='approved')
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
        Vendor.objects.create(name='tv1', approval_status='approved')
        Vendor.objects.create(name='tv2', approval_status='approved')
        self.assertVendorCounts(2, 0)

    def test_with_without_reviews_no_approved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        Vendor.objects.create(name='tv2', approval_status='approved')
        Review.objects.create(vendor=v1, author=get_user())
        self.assertVendorCounts(2, 0)

    def test_with_without_review_with_some_approved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        v2 = Vendor.objects.create(name='tv2', approval_status='approved')
        Review.objects.create(vendor=v1, approved=True, author=get_user())
        Review.objects.create(vendor=v2, approved=False, author=get_user())
        self.assertVendorCounts(1, 1)

    def test_with_without_review_with_all_approved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        v2 = Vendor.objects.create(name='tv2', approval_status='approved')
        Review.objects.create(vendor=v1, approved=True, author=get_user())
        Review.objects.create(vendor=v2, approved=True, author=get_user())
        self.assertVendorCounts(0, 2)

    def test_get_random_unreviewed_no_vendors(self):
        self.assertEqual(None,
                         Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_no_unreviewed_vendors(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        Review.objects.create(vendor=v1, approved=True, author=get_user())
        self.assertEqual(None,
                         Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_with_only_unapproved_reviews(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        Review.objects.create(vendor=v1, approved=False, author=get_user())
        self.assertEqual(v1, Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_one_vendor(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        self.assertEqual(v1, Vendor.objects.approved().get_random_unreviewed())

    def test_get_random_unreviewed_multiple_unreviewed_vendor(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        v2 = Vendor.objects.create(name='tv2', approval_status='approved')
        self.assertIn(Vendor.objects.approved().get_random_unreviewed(),
                      [v1, v2])

    def test_get_random_unreviewed_mixed_unreviewed_vendors_and_reviewed(self):
        v1 = Vendor.objects.create(name='tv1', approval_status='approved')
        v2 = Vendor.objects.create(name='tv2', approval_status='approved')
        v3 = Vendor.objects.create(name='tv3', approval_status='approved')
        Review.objects.create(vendor=v1, approved=True, author=get_user())
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
               approved=True,
               food_rating=1,
               atmosphere_rating=1,
               author=self.user).save()

        self.assertEqual(vendor.food_rating(), 1)
        self.assertEqual(vendor.atmosphere_rating(), 1)

        review2 = Review(vendor=vendor,
                         approved=False,
                         food_rating=4,
                         atmosphere_rating=4,
                         author=self.user)
        review2.save()

        self.assertEqual(vendor.food_rating(), 1)
        self.assertEqual(vendor.atmosphere_rating(), 1)

        review2.approved = True
        review2.save()

        # Floored Average
        self.assertEqual(vendor.food_rating(), 2)
        self.assertEqual(vendor.atmosphere_rating(), 2)

        review3 = Review(vendor=vendor,
                         approved=True,
                         food_rating=4,
                         atmosphere_rating=4,
                         author=self.user)
        review3.save()

        # Floored Average
        self.assertEqual(vendor.food_rating(), 3)
        self.assertEqual(vendor.atmosphere_rating(), 3)

    def test_best_vegan_dish_with(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status="approved")
        d1 = VeganDish.objects.create(name="french toast")
        d2 = VeganDish.objects.create(name="tofu scramble")
        v.vegan_dishes.add(d1)
        v.vegan_dishes.add(d2)

        r = Review.objects.create(vendor=v, author=self.user,
                                  approved=True,
                                  best_vegan_dish=d1)
        r = Review.objects.create(vendor=v, author=self.user,
                                  approved=True,
                                  best_vegan_dish=d1)
        r = Review.objects.create(vendor=v, author=self.user,  # NOQA
                                  approved=True,
                                  best_vegan_dish=d2)
        self.assertEqual(v.best_vegan_dish(), d1)

    def test_best_vegan_dish_without(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status="approved")
        self.assertEqual(v.best_vegan_dish(), None)

    def test_approved_reviews_with_approved(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status="approved")
        r = Review.objects.create(vendor=v, author=self.user,
                                  approved=True)
        self.assertIn(r, v.approved_reviews())

    def test_approved_reviews_with_unapproved(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status="approved")
        r = Review.objects.create(vendor=v, author=self.user)
        self.assertNotIn(r, v.approved_reviews())

    def test_approved_reviews_with_none(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status="approved")
        self.assertEqual(v.approved_reviews().count(), 0)

    def test_unicode_method(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status="approved")
        self.assertEqual(str(v), "test vendor")

    def test_validate_pending(self):
        v = Vendor.objects.create(name="test vendor",
                                  address="123 Main Street",
                                  approval_status="approved")
        v.approval_status = "pending"
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
        vendor.approval_status = "approved"
        vendor.save()
        email.send_new_vendor_approval.assert_called_with(vendor)

        # reset mock function to test it doesn't get called again
        email.send_new_vendor_approval.reset_mock()

        # not called when approval status changes away from approved
        vendor.approval_status = "quarantined"
        vendor.save()
        email.send_new_vendor_approval.assert_not_called()

        # not called when approval status is changed back to approved
        vendor.approval_status = "approved"
        vendor.save()
        email.send_new_vendor_approval.assert_not_called()
