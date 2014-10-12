import functools
import logging

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.generic import DetailView, TemplateView
from django.conf import settings

import django.contrib.auth.views

from vegancity import forms
from vegancity.models import (Vendor, CuisineTag, FeatureTag,
                              Neighborhood, User, Review)
from vegancity import search
from vegancity.fields import StatusField as SF

search_logger = logging.getLogger('vegancity-search')


def password_change(request):
    response = django.contrib.auth.views.password_change(
        request, "registration/password_change_form.html",
        reverse('my_account'))

    # redirect happens when the form validates and the model saves
    if response.status_code == 302:
        messages.success(request, "Password Changed!")

    return response


def _get_home_context(request):
    vendors = Vendor.objects.approved().all()

    random_unreviewed = (Vendor
                         .objects.approved()
                         .get_random_unreviewed()
                         if request.user.is_authenticated()
                         else None)

    # it would be cooler to include these queries with the model
    # manager, but they are tiled to the presentation logic because
    # they only get id and name, the necessary fields.
    annotated_vendor_select = (
        lambda query_prefix:
        # TODO: remove string values
        Vendor.objects.raw(
            """
            SELECT V.id, V.name
            FROM vegancity_vendor V LEFT OUTER JOIN vegancity_review R
            ON V.id = R.vendor_id
            WHERE V.approval_status = '%(approved)s'
            AND R.approval_status='%(approved)s'
            %(query_prefix)s
            LIMIT 5
            """ % {'approved': SF.APPROVED,
                   'query_prefix': query_prefix}))

    top_5 = annotated_vendor_select(
        """
        AND (NOT R.food_rating IS NULL)
        AND (NOT R.atmosphere_rating IS NULL)
        GROUP BY V.id, V.name
        ORDER BY avg(R.food_rating) DESC, avg(R.atmosphere_rating) DESC,
        count(R.id) DESC, name
        """)

    recently_active = annotated_vendor_select(
        """
        GROUP BY V.id, V.name
        ORDER BY max(R.created) DESC
        """)

    recently_added = (vendors.exclude(created=None)
                      .order_by('-created')[:5])

    most_reviewed = Vendor.objects.approved().with_reviews()[:5]

    neighborhoods = Neighborhood.objects.with_vendors()[:21]

    cuisine_tags = CuisineTag.objects.with_vendors()[:21]

    feature_tags = FeatureTag.objects.with_vendors()[:21]

    ctx = {
        'top_5': top_5,
        'most_reviewed': most_reviewed,
        'recently_added': recently_added,
        'recently_active': recently_active,
        'neighborhoods': neighborhoods,
        'cuisine_tags': cuisine_tags,
        'feature_tags': feature_tags,
        'random_unreviewed': random_unreviewed,
    }

    return ctx


def home(request):
    return render_to_response("vegancity/home.html",
                              _get_home_context(request),
                              context_instance=RequestContext(request))


def user_profile(request, username):
    if username is None:
        if request.user.username == '':
            raise Http404
        else:
            return redirect('user_profile', username=request.user.username)
    else:
        profile_user = get_object_or_404(User, username=username)
        approved_reviews = (Review.objects.approved()
                            .filter(author=profile_user)
                            .order_by('-created'))
        return render_to_response(
            'vegancity/profile_page.html',
            {'profile_user': profile_user,
             'approved_reviews': approved_reviews},
            context_instance=RequestContext(request))


def vendors(request):
    has_get_params = len(request.GET) > 0
    center_latitude, center_longitude = settings.DEFAULT_CENTER
    current_query = request.GET.get('current_query', None)
    previous_query = request.GET.get('previous_query', None)
    selected_neighborhood_id = request.GET.get('neighborhood', '')
    selected_cuisine_tag_id = request.GET.get('cuisine_tag', '')
    selected_feature_tag_id = request.GET.get('feature_tag', '')
    checked_feature_filters = [f for f
                               in FeatureTag.objects.with_vendors()
                               if request.GET.get(f.name) or
                               selected_feature_tag_id == str(f.id)]

    vendors = Vendor.objects.approved().select_related('veg_level').all()

    if selected_neighborhood_id:
        vendors = vendors.filter(neighborhood__id=selected_neighborhood_id)

    if selected_cuisine_tag_id:
        vendors = vendors.filter(cuisine_tags__id=selected_cuisine_tag_id)

    if selected_feature_tag_id:
        vendors = vendors.filter(feature_tags__id=selected_feature_tag_id)

    for f in checked_feature_filters:
        vendors = vendors.filter(feature_tags__id__exact=f.id)

    if current_query:
        vendors = search.master_search(current_query, vendors)

    ctx = {
        'cuisine_tags': CuisineTag.objects.all(),
        'feature_tags': FeatureTag.objects.all().order_by('description'),
        'neighborhoods': Neighborhood.objects.with_vendors().order_by('name'),
        'vendor_count': len(vendors),
        'vendors': vendors,
        'request_user': request.user or None,
        'request_ip': request.META.get('REMOTE_ADDR', None),
        'previous_query': previous_query,
        'current_query': current_query,
        'selected_neighborhood_id': (int(selected_neighborhood_id)
                                     if selected_neighborhood_id else None),
        'selected_cuisine_tag_id': (int(selected_cuisine_tag_id)
                                    if selected_cuisine_tag_id else None),
        'checked_feature_filters': checked_feature_filters,
        'has_get_params': has_get_params,
        'center_latitude': center_latitude,
        'center_longitude': center_longitude,
    }

    if has_get_params:
        search_logger.info('USER_SEARCH', extra=ctx)

    return render_to_response('vegancity/vendors.html', ctx,
                              context_instance=RequestContext(request))


###########################
## data entry views
###########################

def _generic_form_processing_view(request, form_obj, redirect_url,
                                  template_name, pre_save_functions=[],
                                  form_init={}, ctx={}, commit_flag=False):
    """Generic view for form processing.

    Takes a number of arguments pertaining to the form processing
    and data entry process. Returns an HttpResponse and a model
    object.

    Call this function using another form processing view and return
    the HttpResponse.

    request: The HttpRequest that was received by the calling view.

    form_obj: A callable that returns a form object when called with
    no arguments or with a dictionary of POST data.

    redirect_url: A url object pointing to the redirection page in the
    event that the form processing is successful (valid).

    template_name: a string with the name of a template to render the
    form to.

    OPTIONAL:

    pre_save_functions: A list of callables that will be called, in order,
    with the model object, before saving to the database. Defaults to the
    empty list.

    form_init: a dictionary of initial data to be sent to the form if
    validation fails. Defaults to an empty dict.

    ctx: a context dictionary to be rendered into the template. The main
    form object will be placed in this dict with the name 'form'.
    """

    if request.method == 'POST':
        form = form_obj(request.POST)
        obj = None

        if form.is_valid():
            obj = form.save(commit=commit_flag)

            for fn in pre_save_functions:
                fn(obj)

            if commit_flag is False:
                obj.save()
            return HttpResponseRedirect(redirect_url), obj

    else:
        form = form_obj(initial=form_init)
        obj = None

    ctx['form'] = form

    return render_to_response(template_name, ctx,
                              context_instance=RequestContext(request)), obj


def register(request):
    "Register a new user and log them in."

    response, obj = _generic_form_processing_view(
        request, forms.VegUserCreationForm,
        reverse("register_thanks"),
        "vegancity/register.html",
        commit_flag=True)

    # if the registration was successful, log the user in
    if obj:
        new_user = authenticate(
            username=request.POST.get("username"),
            password=request.POST.get("password1"))
        login(request, new_user)

    return response


@login_required
def new_vendor(request):
    "Create a new vendor."

    def apply_submitter(request, vendor):
        vendor.submitted_by = request.user

    apply_submitter = functools.partial(apply_submitter, request)

    response, obj = _generic_form_processing_view(
        request,
        forms.NewVendorForm,
        reverse("vendor_thanks"),
        "vegancity/new_vendor.html",
        [apply_submitter],
        commit_flag=False)

    return response


@login_required
def new_review(request, vendor_id):
    "Create a new vendor-specific review."

    # get vendor, place in ctx dict for the template
    vendor = Vendor.objects.approved().get(id=vendor_id)
    ctx = {'vendor': vendor}

    # Apply the vendor as an argument to the form constructor.
    # This is done so that the form can be instantiated with
    # a single argument like a normal form constructor.
    form = functools.partial(forms.NewReviewForm, vendor)

    # a function for setting the author based on session data
    def apply_author(request, obj):
        obj.author = request.user
        return None

    # Apply the request as an argument to apply_author.
    # As above, this is done so the function can be callable
    # as apply_author(obj)
    apply_author = functools.partial(apply_author, request)

    response, obj = _generic_form_processing_view(
        request,
        form,
        reverse("review_thanks", args=[vendor.id]),
        "vegancity/new_review.html",
        [apply_author],
        {'vendor': vendor},
        ctx)

    return response


@login_required
def account_edit(request):
    """Edit page for user accounts"""

    user = request.user
    user_profile = user.get_profile()

    if request.method == 'POST':
        user_form = forms.VegUserEditForm(request.POST, instance=user)
        profile_form = forms.VegProfileEditForm(request.POST,
                                                instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile saved!')
        return HttpResponseRedirect(reverse('my_account'))
    else:
        user_form = forms.VegUserEditForm(instance=user)
        profile_form = forms.VegProfileEditForm(instance=user_profile)
    return render_to_response('vegancity/account_edit.html',
                              {'user_form': user_form,
                               'profile_form': profile_form},
                              context_instance=RequestContext(request))


def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor.objects.approved(), pk=pk)
    approved_reviews = vendor.approved_reviews()
    return render_to_response('vegancity/vendor_detail.html',
                              {'vendor': vendor,
                               'approved_reviews': approved_reviews},
                              context_instance=RequestContext(request))

###########################
## generic views
###########################


class ConnectView(TemplateView):
    template_name = 'vegancity/connect.html'


class AboutView(TemplateView):
    template_name = 'vegancity/about.html'


class PrivacyView(TemplateView):
    template_name = 'vegancity/privacy.html'


class ReviewThanksView(DetailView):
    template_name = 'vegancity/review_thanks.html'
    model = Vendor

    def get_context_data(self, **kwargs):
        context = super(ReviewThanksView, self).get_context_data(**kwargs)
        context.update({'warning': True})
        return context


class VendorThanksView(TemplateView):
    template_name = 'vegancity/vendor_thanks.html'

    def get_context_data(self, **kwargs):
        context = super(VendorThanksView, self).get_context_data(**kwargs)
        context.update({'warning': True})
        return context


class RegisterThanksView(TemplateView):
    template_name = 'vegancity/register_thanks.html'
