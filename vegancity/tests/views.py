from django.test import TestCase
from django.test.client import RequestFactory

from vegancity import views
from vegancity.models import Vendor, Neighborhood
from vegancity.tests.utils import get_user


class ViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user()


class VendorViewTest(ViewTestCase):

    def test_valid_new_vendor_redirects(self):
        request = self.factory.post('/vendors/add',
                                    {'name': 'test123',
                                     'address': '123 Main st'})
        request.user = self.user

        response = views.new_vendor(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(1,
                         Vendor.objects.filter(name="test123").count())

    def test_invalid_new_vendor_does_not_save(self):
        request = self.factory.post('/vendors/add',
                                    {'name': 'test123'})
        request.user = self.user

        response = views.new_vendor(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(0,
                         Vendor.objects.filter(name="test123").count())


class HomeViewTest(ViewTestCase):
    def test_home_view_empty(self):
        request = self.factory.get('')
        request.user = self.user
        ctx = views._get_home_context(request)
        self.assertEqual(ctx['random_unreviewed'], None)
        self.assertEqual(list(ctx['top_5']), [])
        self.assertEqual(list(ctx['recently_added']), [])
        self.assertEqual(list(ctx['recently_active']), [])
        self.assertEqual(list(ctx['neighborhoods']), [])
        self.assertEqual(list(ctx['cuisine_tags']), [])
        self.assertEqual(list(ctx['feature_tags']), [])

    def test_home_view_with_unapproved(self):
        Vendor.objects.create(name="the test vendor")
        request = self.factory.get('')
        request.user = self.user
        ctx = views._get_home_context(request)
        self.assertEqual(ctx['random_unreviewed'], None)
        self.assertEqual(list(ctx['top_5']), [])
        self.assertEqual(list(ctx['recently_added']), [])
        self.assertEqual(list(ctx['recently_active']), [])
        self.assertEqual(list(ctx['neighborhoods']), [])
        self.assertEqual(list(ctx['cuisine_tags']), [])
        self.assertEqual(list(ctx['feature_tags']), [])

    def test_home_view_with_sane_values(self):
        Neighborhood.objects.create(name="West Philly")
        n2 = Neighborhood.objects.create(name="South Philly")
        t1 = Vendor.objects.create(name="test 1", approval_status="approved")
        t2 = Vendor.objects.create(name="test 2", approval_status="approved",
                                   neighborhood=n2)
        request = self.factory.get('')
        request.user = self.user
        ctx = views._get_home_context(request)
        self.assertEqual(list(ctx['top_5']), [])
        self.assertEqual(list(ctx['recently_added']), [t2, t1])
        self.assertEqual(list(ctx['neighborhoods']), [n2])
