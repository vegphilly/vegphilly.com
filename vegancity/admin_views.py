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

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.contrib.admin.views.decorators import staff_member_required

import models

from djqscsv import render_to_csv_response


@staff_member_required
def pending_approval_count(request):
    pending_vendor_count = models.Vendor.objects.pending_approval().count()
    pending_review_count = models.Review.objects.pending_approval().count()
    return HttpResponse(str(pending_vendor_count + pending_review_count))


@staff_member_required
def pending_approval(request):
    pending_vendors = models.Vendor.objects.pending_approval()
    pending_reviews = models.Review.objects.pending_approval()
    ctx = {
        'pending_vendors': pending_vendors,
        'pending_reviews': pending_reviews,
    }
    return render_to_response("admin/pending_approval.html", ctx,
                              context_instance=RequestContext(request))


@staff_member_required
def mailing_list(request):
    mailing_list_users = models.User\
                               .objects.filter(userprofile__mailing_list=True)\
                                       .values('username',
                                               'first_name',
                                               'last_name',
                                               'email')

    return render_to_csv_response(mailing_list_users,
                                  append_datestamp=True,
                                  filename='vegphilly_ml')


@staff_member_required
def vendor_list(request):
    vendors = models.Vendor.objects.approved()\
                           .values('name',
                                   'address',
                                   'neighborhood__name',
                                   'phone',
                                   'website',
                                   'veg_level__name',
                                   'notes')

    return render_to_csv_response(vendors,
                                  append_datestamp=True,
                                  filename='vegphilly_vendors')
