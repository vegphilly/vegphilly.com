from mock import Mock
from bs4 import BeautifulSoup

from django.test import TestCase, LiveServerTestCase
from django.test.client import RequestFactory
from vegancity import views, geocode
from vegancity.models import Review, Vendor, Neighborhood

from vegancity.tests.utils import get_user

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from django.conf import settings


class IntegrationTest(TestCase):
    """
    This is currently used as a way to flag tests that should
    be excluded from the normal unit test runner
    """
    pass


class SearchTest(TestCase):

    def setUp(self):
        self.v1 = Vendor.objects.create(
            name="Test Vendor Foo", approval_status='approved')
        self.v2 = Vendor.objects.create(
            name="Test Vendor Bar", approval_status='approved')
        self.v3 = Vendor.objects.create(
            name="Test Vendor Baz", approval_status='approved')
        self.v4 = Vendor.objects.create(
            name="Test Vendor Bart", approval_status='approved')
        self.factory = RequestFactory()
        geocode.geocode_address = Mock(return_value=(100, 100, "South Philly"))

    def test_search_by_name_for_substring(self):
        request = self.factory.get('',
                                   {'current_query': 'Bar', })

        request.user = get_user()

        response = views.vendors(request)

        self.assertEqual(response.content.count("Showing 1 vendors"), 1)

        request = self.factory.get('',
                                   {'current_query': 'Vendor', })
        request.user = get_user()

        response = views.vendors(request)
        self.assertEqual(response.content.count("Showing 4 vendors"), 1)

    def test_search_by_name_approved_only(self):
        self.v4.approval_status = 'quarantined'
        self.v4.save()

        request = self.factory.get('',
                                   {'current_query': 'Vendor', })
        request.user = get_user()

        response = views.vendors(request)
        self.assertEqual(response.content.count("Showing 3 vendors"), 1)

    def test_neighborhoods_field_is_populated(self):
        """ This test was born out of an actual observed bug """

        def count_option_elements():
            request = self.factory.get('')
            request.user = get_user()
            response = views.vendors(request)
            content = BeautifulSoup(response.content)
            neighborhood_element = filter(
                lambda x: x['name'] == 'neighborhood',
                content.find_all('select'))[0]
            return len(neighborhood_element.find_all('option'))

        n1 = Neighborhood.objects.create(name="Foo")

        self.assertEqual(count_option_elements(), 1)

        self.v1.neighborhood = n1
        self.v1.save()

        self.assertEqual(count_option_elements(), 2)


class PageLoadTest(IntegrationTest):

    fixtures = ['public_data.json']

    def setUp(self):
        self.reviews = Review.objects.approved().all()
        self.vendors = Vendor.objects.approved().all()

    def assertNoBrokenTemplates(self, url):
        response = self.client.post(url)
        self.assertEqual(response.content.count("{{"), 0)
        self.assertEqual(response.content.count("}}"), 0)

    def assertCorrectStatusCode(self, url, desired_code):
        response = self.client.get(url)
        self.assertEqual(response.status_code, desired_code)

    def test_orm_links(self):
        "Test Vendors pages using ORM"
        for vendor in self.vendors:
            url = vendor.get_absolute_url()
            self.assertNoBrokenTemplates(url)
            self.assertCorrectStatusCode(url, 200)

    def test_review_links(self):
        "Test review pages using ORM"
        for review in self.reviews:
            url = review.get_absolute_url()
            self.assertNoBrokenTemplates(url)
            self.assertCorrectStatusCode(url, 200)

    def test_other_pages(self):
        PAGES_RETURNING_302 = [
            '/vendors/add/',
            '/accounts/logout/',
        ]

        PAGES_RETURNING_200 = [
            '/',
            '/vendors/',
            '/about/',
            '/accounts/login/',
            '/accounts/register/',
            '/admin/',
        ]

        for url in PAGES_RETURNING_302:
            self.assertNoBrokenTemplates(url)
            self.assertCorrectStatusCode(url, 302)

        for url in PAGES_RETURNING_200:
            self.assertNoBrokenTemplates(url)
            self.assertCorrectStatusCode(url, 200)


class FunctionalSearchTest(LiveServerTestCase):
    def use_xvfb(self):
        from pyvirtualdisplay import Display
        self.display = Display('xvfb',
                               visible=1,
                               size=(1280, 1024))
        self.display.start()
        self.driver = WebDriver()

    def setUp(self):

        try:
            self.driver = WebDriver()
            ui_is_not_available = False
        except WebDriverException:
            ui_is_not_available = True

        if settings.TEST_HEADLESS or ui_is_not_available:
            self.use_xvfb()

        self.driver.implicitly_wait(10)
        super(FunctionalSearchTest, self).setUp()

    def tearDown(self):
        self.driver.quit()
        if hasattr(self, 'display'):
            self.display.stop()

        super(FunctionalSearchTest, self).tearDown()

    def test_simple_homepage_address_search_redirect(self):
        self.driver.get(self.live_server_url)
        input = self.driver.find_element_by_id('vc-search-input')
        input.send_keys('foobar\r')
        summary = self.driver.find_element_by_id('result-description')
        self.assertEqual(summary.text, 'No results for "foobar"')
