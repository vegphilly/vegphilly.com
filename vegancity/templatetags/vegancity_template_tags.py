import re
import hashlib

from urllib import quote_plus

from django import template
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

DEFAULT_USER_ICON = quote_plus(
    "http://%s/static/images/default_user_icon.jpg" % settings.HOSTNAME)


def gravatar_urlify(email_address, size=72):
    if email_address:
        hash = hashlib.md5(email_address).hexdigest()
        return ("http://gravatar.com/avatar/%s?s=%i&d=%s" %
                (hash, size, DEFAULT_USER_ICON))
    else:
        return DEFAULT_USER_ICON


def strip_http(text):
    if text:
        text = re.sub('https?://', '', text)
        if text[-1] == '/':
            text = text[:-1]
        return text
    else:
        return ''


def graphical_rating(rating):
    rating_icons = ('<img class="rating" src="' +
                    settings.STATIC_URL +
                    'images/rating-solid.png">') * rating
    rating_icons += ('<img class="rating" src="' +
                     settings.STATIC_URL +
                     'images/rating-faded.png">') * (4 - rating)
    return rating_icons


def spaces_to_nbsps(obj):
    safe_string = escape(unicode(obj))
    return mark_safe(safe_string.replace(" ", "&nbsp;"))

register = template.Library()
spaces_to_nbsps = register.filter(spaces_to_nbsps, is_safe=True)
strip_http = register.filter(strip_http, is_safe=True)
gravatar_urlify = register.filter(gravatar_urlify, is_safe=True)
graphical_rating = register.filter(graphical_rating, is_safe=True)
