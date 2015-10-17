from django.conf.urls import url
from django.contrib.auth.models import User
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.utils import trailing_slash
from vegancity import models
from .search import master_search

from tastypie.api import Api


def build_api():
    v1_api = Api(api_name='v1')
    v1_api.register(VendorResource())
    v1_api.register(ReviewResource())
    return v1_api


class VendorResource(ModelResource):
    reviews = fields.ToManyField('vegancity.api.ReviewResource',
                                 'review_set',
                                 null=True)
    neighborhood = fields.ToOneField('vegancity.api.NeighborhoodResource',
                                     'neighborhood',
                                     null=True,
                                     full=True)
    cuisine_tags = fields.ToManyField('vegancity.api.CuisineTagResource',
                                      'cuisine_tags',
                                      related_name='vendors',
                                      null=True,
                                      full=True)
    feature_tags = fields.ToManyField('vegancity.api.FeatureTagResource',
                                      'feature_tags',
                                      related_name='vendors',
                                      null=True,
                                      full=True)
    veg_level = fields.ToOneField('vegancity.api.VegLevelResource',
                                  'veg_level',
                                  related_name='vendors',
                                  null=True,
                                  full=True)

    food_rating = fields.IntegerField(null=True, readonly=True)
    atmosphere_rating = fields.IntegerField(null=True, readonly=True)

    def prepend_urls(self):
        url_template = r'^(?P<resource_name>%s)/search%s$'

        url_body = url_template % (self._meta.resource_name, trailing_slash())

        response_url = url(url_body, self.wrap_view('get_search'),
                           name='api_get_search')

        return [response_url]

    def get_search(self, request, **kwargs):
        raw_results = master_search(request.GET.get('q', ''))
        vendors = []

        results, status_code = raw_results
        for result in results:
            bundle = self.build_bundle(obj=result, request=request)
            bundle = self.full_dehydrate(bundle)
            vendors.append(bundle)

        ctx = {'vendors': vendors}

        return self.create_response(request, ctx)

    def dehydrate_food_rating(self, bundle):
        return bundle.obj.food_rating()

    def dehydrate_atmosphere_rating(self, bundle):
        return bundle.obj.atmosphere_rating()

    class Meta:
        queryset = models.Vendor.objects.approved().all()
        resource_name = 'vendors'
        fields = ['id', 'name', 'address', 'website', 'phone',
                  'notes', 'resource_uri']


class ReviewResource(ModelResource):
    vendor = fields.ToOneField('vegancity.api.VendorResource', 'vendor')
    author = fields.ToOneField('vegancity.api.UserResource',
                               'author',
                               null=True,
                               full=True)

    class Meta:
        queryset = models.Review.objects.approved().all()
        resource_name = 'reviews'
        fields = [
            'id', 'atmosphere_rating', 'food_rating', 'title', 'content',
            'created', 'modified', 'suggested_feature_tags',
            'suggested_cuisine_tags'
        ]


class CuisineTagResource(ModelResource):

    class Meta:
        queryset = models.CuisineTag.objects.all()
        resource_name = 'cuisine_tag'
        fields = ['description', 'id']


class NeighborhoodResource(ModelResource):

    class Meta:
        queryset = models.Neighborhood.objects.all()
        resource_name = 'neighborhood'
        fields = ['name']


class FeatureTagResource(ModelResource):

    class Meta:
        queryset = models.FeatureTag.objects.all()
        resource_name = 'feature_tag'
        fields = ['description', 'id']


class UserResource(ModelResource):

    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        fields = ['id', 'username', 'first_name', 'last_name']


class VegLevelResource(ModelResource):

    class Meta:
        queryset = models.VegLevel.objects.all()
        resource_name = 'veg_level'
        fields = ['name', 'description']
