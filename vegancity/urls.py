from django.conf.urls import patterns, include, url
from django.contrib import admin
from vegancity import views
from .api import build_api

admin.autodiscover()


urlpatterns = patterns(
    '',
    url(r'^api/', include(build_api().urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/pending_approval/$', 'vegancity.admin_views.pending_approval', name="pending_approval"),
    url(r'^admin/pending_approval/count/$', 'vegancity.admin_views.pending_approval_count', name="pending_approval_count"),
    url(r'^admin/mailing_list/$', 'vegancity.admin_views.mailing_list', name="mailing_list"),
    url(r'^admin/vendor_list/$', 'vegancity.admin_views.vendor_list', name="vendor_list"),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^$', views.home, name='home'),
    url(r'^vendors/$', views.vendors, name="vendors"),
    url(r'^vendors/add/$', views.new_vendor, name="new_vendor"),
    url(r'^vendors/add/thanks/$', views.VendorThanksView.as_view(), name="vendor_thanks"),
    url(r'^vendors/review/(?P<vendor_id>\d+)/$', views.new_review, name="new_review"),
    url(r'^vendors/(?P<pk>\d+)(-[\w\d]+)*/$', views.vendor_detail, name="vendor_detail"),
    url(r'^connect/$', views.ConnectView.as_view(), name='connect'),
    url(r'^about/$', views.AboutView.as_view(), name='about'),
    url(r'^privacy/$', views.PrivacyView.as_view(), name='privacy'),
    url(r'^vendors/review/(?P<pk>\d+)/thanks/$', views.ReviewThanksView.as_view(), name="review_thanks"),

    url(r'^accounts/login/$',  'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'},  name='logout'),
    url(r'^accounts/register/$', 'vegancity.views.register', name='register'),
    url(r'^accounts/register/thanks/$', views.RegisterThanksView.as_view(), name='register_thanks'),
    url(r'^accounts/password/change/$', 'vegancity.views.password_change', name='password_change'),
    url(r'^accounts/password/reset/$', 'django.contrib.auth.views.password_reset', name='password_reset'),
    url(r'^accounts/password/reset/done/$', 'django.contrib.auth.views.password_reset_done', name='password_reset_done'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm'),
    url(r'^accounts/password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete', name='password_reset_complete'),
    url(r'^accounts/profile/$', 'vegancity.views.user_profile', {'username': None}, name='my_account'),
    url(r'^accounts/profile/edit/$', 'vegancity.views.account_edit', name='account_edit'),

    url(r'^users/(?P<username>[a-zA-Z0-9_@.+-]+)/$', 'vegancity.views.user_profile', name='user_profile'),
)
