from django.core.exceptions import ImproperlyConfigured
import os

APP_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

HOSTNAME = "www.vegphilly.com"

DEBUG = True
TEMPLATE_DEBUG = DEBUG
TEST_HEADLESS = True

ADMINS = ()

MANAGERS = ADMINS

AUTH_PROFILE_MODULE = "vegancity.UserProfile"

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'vegphilly',
        'USER': 'postgres',
    }
}

GOOGLE_ANALYTICS_TRACKING_ID = ''

TIME_ZONE = None

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static/')

STATIC_URL = '/static/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = tuple()

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

SECRET_KEY = 'insecure'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

GLOBAL_MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'vegancity.context_processors.globals',
)

ROOT_URLCONF = 'vegancity.urls'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

UNMANAGED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.gis',
    'south',
    'gunicorn',
)

MANAGED_APPS = (
    'vegancity',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': ("[%(asctime)s] %(levelname)s "
                       "[%(name)s:%(lineno)s] %(message)s"),
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'search': {
            'format': ("[%(asctime)s] %(levelname)s "
                       "%(message)s::user::"
                       "%(request_user)s\n"

                       "[%(asctime)s] %(levelname)s "
                       "%(message)s::ip_address::"
                       "%(request_ip)s\n"

                       "[%(asctime)s] %(levelname)s "
                       "%(message)s::current_query::"
                       "%(current_query)s\n"

                       "[%(asctime)s] %(levelname)s "
                       "%(message)s::previous_query::"
                       "%(previous_query)s\n"

                       "[%(asctime)s] %(levelname)s "
                       "%(message)s::selected_neighborhood_id::"
                       "%(selected_neighborhood_id)s\n"

                       "[%(asctime)s] %(levelname)s "
                       "%(message)s::selected_cuisine_tag_id::"
                       "%(selected_cuisine_tag_id)s\n"

                       "[%(asctime)s] %(levelname)s "
                       "%(message)s::checked_feature_filters::"
                       "%(checked_feature_filters)s\n"),
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'general': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/vegphilly/django-general.log',
            'maxBytes': 500000,
            'backupCount': 2,
            'formatter': 'simple',
        },
        'request': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/vegphilly/django-request.log',
            'maxBytes': 500000,
            'backupCount': 2,
            'formatter': 'simple',
        },
        'sql': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/vegphilly/django-sql.log',
            'maxBytes': 500000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'vegancity-general': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/vegphilly/vegancity-general.log',
            'maxBytes': 500000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'vegancity-search': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/vegphilly/vegancity-search.log',
            'maxBytes': 500000,
            'backupCount': 2,
            'formatter': 'search',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['general'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.request': {
            'handlers': ['request'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.db.backends': {
            'handlers': ['sql'],
            'level': 'WARN',
            'propagate': False,
        },
        'vegancity': {
            'handlers': ['vegancity-general'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'vegancity-search': {
            'handlers': ['vegancity-search'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

TEST_RUNNER = 'vegancity.tests.VegancityTestRunner'

###################################
# CUSTOM
###################################

# LOCATION_BOUNDS is the bounding box within which all data should live.
# This is used for a few different geospatial queries. Specify the
# southwest corner followed by the northeast corner in the format
# "sw_lat,sw_lng|ne_lat,ne_lng"
LOCATION_BOUNDS = "39.9269547,-75.2519587|39.988524,-75.106326"

# A string used to narrow down google maps searches. Consult
# the google maps javascript api v3 for more details.
LOCATION_COMPONENTS = "country:US|locality:Philadelphia"

# Used to specify where the map will center.
DEFAULT_CENTER = (39.946385, -75.1785634)

# Replace these with a valid gmail account login that
# can be used to send administrative emails
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587

DEVELOPMENT_APPS = tuple()
DEVELOPMENT_MIDDLEWARE_CLASSES = tuple()

try:
    from settings_local import *  # NOQA
except ImportError:
    pass

INSTALLED_APPS = UNMANAGED_APPS + MANAGED_APPS + DEVELOPMENT_APPS

MIDDLEWARE_CLASSES = GLOBAL_MIDDLEWARE_CLASSES + DEVELOPMENT_MIDDLEWARE_CLASSES

if EMAIL_HOST_USER == '' or EMAIL_HOST_PASSWORD == '':
    error_message = ("No valid email login configured. Please specify "
                     "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD "
                     "in your settings_local.py file.")
    raise ImproperlyConfigured(error_message)

POSTGIS_VERSION = (2, 0, 3)
