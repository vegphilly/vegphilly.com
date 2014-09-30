from django.test import TestCase
from django.test.client import RequestFactory

import csv

from itertools import izip_longest

from vegancity.admin_views import (vendor_list, mailing_list,
                                   pending_approval_count)
from vegancity.models import Vendor, Neighborhood, VegLevel, User, UserProfile
from vegancity.tests.utils import get_user
from vegancity.fields import StatusField as SF


class CSVViewTest(TestCase):
    def assertCSVIsCorrect(self, response, expected_data):

        csv_data = csv.reader(response, delimiter=",")

        padded_expected_data = [[], ['\xef\xbb\xbf']] + expected_data

        test_along = izip_longest(csv_data, padded_expected_data)
        for csv_row, expected_row in test_along:
            self.assertEqual(csv_row, expected_row)

    def test_mailing_list(self):
        veggie_lover = User.objects.create(username="veggie_lover",
                                           first_name="veggie",
                                           last_name="lover",
                                           email="vl@example.com",
                                           is_staff=True)
        profile = UserProfile(user=veggie_lover)
        profile.mailing_list = True
        profile.save()

        expected_data = [
            ['username', 'first_name', 'last_name', 'email'],
            ['veggie_lover', 'veggie', 'lover', 'vl@example.com']
        ]

        request = RequestFactory().get('')
        request.user = veggie_lover

        response = mailing_list(request)

        self.assertCSVIsCorrect(response, expected_data)

    def test_vendor_list(self):

        south_philly = Neighborhood.objects.create(name="South Philly")
        west_philly = Neighborhood.objects.create(name="West Philly")
        vegan = VegLevel.objects.create(name="vegan", description="vegan")
        vegetarian = VegLevel.objects.create(name="vegetarian",
                                             description="vegetarian")

        model_rows = [
            ("test vendor 1", "123 Main Street", south_philly, "1234567890",
             "www.example.com", vegan, "A great place to eat"),
            ("test vendor 2", "456 Main Street", west_philly, "0987654321",
             "www.example.com", vegetarian, "The food is ok"),
        ]

        expected_data = [
            ['name', 'address', 'neighborhood__name', 'phone', 'website',
             'veg_level__name', 'notes'],
            ["test vendor 1", "123 Main Street", "South Philly", "1234567890",
             "www.example.com", "vegan", "A great place to eat"],
            ["test vendor 2", "456 Main Street", "West Philly", "0987654321",
             "www.example.com", "vegetarian", "The food is ok"]
        ]

        for row in model_rows:
            Vendor.objects.create(name=row[0],
                                  address=row[1],
                                  neighborhood=row[2],
                                  phone=row[3],
                                  website=row[4],
                                  veg_level=row[5],
                                  notes=row[6],
                                  approval_status=SF.APPROVED)

        request = RequestFactory().get('')
        request.user = get_user(is_staff=True)

        response = vendor_list(request)

        self.assertCSVIsCorrect(response, expected_data)


class PendingApprovalCountTest(TestCase):
    def test_pending_approval_count_none(self):
        request = RequestFactory().get('')
        request.user = get_user(is_staff=True)
        response = pending_approval_count(request)
        self.assertEqual(response.content, "0")

    def test_pending_approval_count_all_approved(self):
        Vendor.objects.create(name="Test Vendor",
                              approval_status=SF.APPROVED)
        request = RequestFactory().get('')
        request.user = get_user(is_staff=True)
        response = pending_approval_count(request)
        self.assertEqual(response.content, "0")

    def test_pending_approval_count_with_pending(self):
        Vendor.objects.create(name="Test Vendor")
        request = RequestFactory().get('')
        request.user = get_user(is_staff=True)
        response = pending_approval_count(request)
        self.assertEqual(response.content, "1")
