from django import forms as dj_forms

from django.contrib.gis.admin.options import GeoModelAdmin

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

import models
import forms

#####################################
## MODEL ADMIN CLASSES
#####################################


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'author', 'approval_status',
                    'suggested_feature_tags', 'suggested_cuisine_tags',

                    )
    list_filter = ('approval_status', 'unlisted_vegan_dish')
    form = forms.AdminEditReviewForm


class VendorVeganDishInline(admin.TabularInline):
    model = models.Vendor.vegan_dishes.through
    extra = 0


class AdminVendorForm(dj_forms.ModelForm):
    class Meta:
        model = models.Vendor


class VendorAdmin(GeoModelAdmin):
    readonly_fields = ('location', 'submitted_by')
    list_display = ('name', 'approval_status',
                    'created', 'submitted_by', 'neighborhood')
    list_filter = ('approval_status', 'submitted_by')
    ordering = ('name',)
    form = AdminVendorForm


class UserProfileInline(admin.StackedInline):
    model = models.UserProfile


class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]


class VeganDishAdmin(admin.ModelAdmin):
    inlines = (VendorVeganDishInline,)
    list_display = ('name',)
    list_display_links = ('name',)

#####################################
## ADMIN REGISTRATION
#####################################

admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)
admin.site.register(models.UserProfile)

admin.site.register(models.Vendor, VendorAdmin)
admin.site.register(models.Review, ReviewAdmin)
admin.site.register(models.VeganDish, VeganDishAdmin)
admin.site.register(models.CuisineTag)
admin.site.register(models.FeatureTag)
admin.site.register(models.Neighborhood)
