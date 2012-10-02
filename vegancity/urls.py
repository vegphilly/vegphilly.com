from django.conf.urls import patterns, include, url
from django.contrib import admin

from settings import INSTALLED_APPS

from vegancity.views import vendor_detail

admin.autodiscover()

# CUSTOM VIEWS
urlpatterns = patterns('vegancity.views',
    url(r'^vendors/$', 'vendors', name="vendors"),
    url(r'^vendors/(?P<vendor_id>\d+)/$', 'vendor_detail', name="vendor_detail"),
    )

# GENERIC VIEWS
urlpatterns += patterns('django.views.generic.simple',
    url(r'^$', 'direct_to_template', {'template': 'vegancity/home.html'}, name='home'),
    url(r'^about/$', 'direct_to_template', {'template': 'vegancity/about.html'}, name='about'),
    )                        

# ADMIN VIEWS
if 'django.contrib.admin' in INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^admin/', include(admin.site.urls)),
    )
