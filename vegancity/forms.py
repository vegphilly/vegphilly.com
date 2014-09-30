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


from django import forms

import models

from django.contrib.auth.forms import UserCreationForm


class VegUserCreationForm(UserCreationForm):

    "Form used for creating new users."
    email_explanation = ("VegPhilly is currently under development. "
                         "We may use your email to contact you ONLY "
                         "about important changes to your account.")
    email = forms.EmailField(max_length=70,
                             label="Email (temporarily required)",
                             help_text=email_explanation,
                             required=True)
    bio = forms.CharField(label="Bio",
                          required=False,
                          widget=forms.Textarea,
                          help_text=("Entering a bio is optional. "
                                     "It will appear to all VegPhilly "
                                     "users along with your username."))
    mailing_list = forms.BooleanField(label=("Would you like to "
                                             "join our mailing list?"),
                                      required=False)

    def save(self, *args, **kwargs):
        user = super(VegUserCreationForm, self).save(*args, **kwargs)
        user.email = self.cleaned_data['email']
        # this is a total hack. saving twice because email isn't included
        # in the original form. we should do away with this form class
        # garbage and handle this explicitly in a view.
        user.save()

        user_profile = models.UserProfile(user=user)
        user_profile.bio = self.cleaned_data['bio']
        user_profile.mailing_list = self.cleaned_data['mailing_list']
        user_profile.save()
        return user

    def clean(self):
        cleaned_data = super(VegUserCreationForm, self).clean()
        username = cleaned_data.get("username", "")

        # TODO: username-specific validation should be stored at the
        # field level.  this can be done by adding validators to the
        # field instance(?) at form instantiation time.

        if len(username) < 3:
            raise forms.ValidationError(
                "Your username must be at least three characters.")

        if username != username.lower():
            raise forms.ValidationError("Usernames cannot contain capital "
                                        "letters at this time. Please "
                                        "correct this.")

        return cleaned_data


class VegUserEditForm(forms.ModelForm):

    """Form for users to edit their information"""

    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = models.User
        fields = ('first_name', 'last_name',)


class VegProfileEditForm(forms.ModelForm):

    class Meta:
        model = models.UserProfile
        fields = ('bio', 'mailing_list',)


##############################
### Vendor Forms
##############################

class NewVendorForm(forms.ModelForm):
    "Form used for adding new vendors."

    class Meta:
        model = models.Vendor
        exclude = ('approval_status',)
        widgets = {
            'cuisine_tags': forms.CheckboxSelectMultiple,
            'feature_tags': forms.CheckboxSelectMultiple,
        }

##############################
### Review Forms
##############################


class _BaseReviewForm(forms.ModelForm):

    """Base Class for making Review forms.

    This class should not be instantiated directly."""

    def clean(self):
        cleaned_data = super(_BaseReviewForm, self).clean()
        chose_best = cleaned_data.get("best_vegan_dish")
        entered_unlisted = cleaned_data.get("unlisted_vegan_dish")

        if chose_best and entered_unlisted:
            raise forms.ValidationError("Can't have both 'Best Vegan dish' "
                                        "and 'Favorite Vegan Dish'. Please "
                                        "choose one.")

        return cleaned_data

    def filter_dishes(self, vendor):
        self.fields['best_vegan_dish'].queryset = vendor.vegan_dishes.all()

    class Meta:
        model = models.Review


class AdminEditReviewForm(_BaseReviewForm):

    def __init__(self, *args, **kwargs):
        super(AdminEditReviewForm, self).__init__(*args, **kwargs)

        if self.instance.pk:
            self.filter_dishes(self.instance.vendor)


class NewReviewForm(_BaseReviewForm):

    def __init__(self, vendor, *args, **kwargs):
        super(NewReviewForm, self).__init__(*args, **kwargs)
        self.filter_dishes(vendor)

    class Meta(_BaseReviewForm.Meta):
        exclude = ('approval_status', 'author',)
        widgets = {
            'vendor': forms.HiddenInput,
        }
