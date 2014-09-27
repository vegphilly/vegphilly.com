#!/usr/bin/env python

# Copyright (C) 2012 Steve Lamb

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

import geocode

from vegancity.models import FeatureTag, CuisineTag, Vendor, VeganDish, Review

from django.contrib.gis.geos import Point


def master_search(query, initial_queryset=None):

    master_results = (address_search(query) |
                      Vendor.objects.approved().search(query) |
                      FeatureTag.objects.vendor_search(query) |
                      CuisineTag.objects.vendor_search(query) |
                      VeganDish.objects.vendor_search(query) |
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
