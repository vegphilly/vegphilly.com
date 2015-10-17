#!/usr/bin/env python

import geocode

from vegancity.models import FeatureTag, CuisineTag, Vendor, Review

from django.contrib.gis.geos import Point


def master_search(query, initial_queryset=None):

    master_results = (address_search(query) |
                      Vendor.objects.approved().search(query) |
                      FeatureTag.objects.vendor_search(query) |
                      CuisineTag.objects.vendor_search(query) |
                      Review.objects.approved().vendor_search(query))

    if initial_queryset:
        master_results = master_results & initial_queryset

    return master_results


def address_search(query):

        geocode_result = geocode.geocode_address(query)

        if geocode_result is None:
            return Vendor.objects.none()
        latitude, longitude, neighborhood = geocode_result

        point = Point(x=longitude, y=latitude, srid=4326)
        vendors = Vendor.objects.approved().filter(
            location__dwithin=(point, .004))

        return vendors
