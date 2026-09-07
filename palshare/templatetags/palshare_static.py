"""Refresh local assets after edits while retaining production static storage."""

from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def versioned_static(path):
    """Add the file modification time to development asset URLs."""
    url = static(path)
    if not settings.DEBUG:
        return url
    filename = finders.find(path)
    if not filename:
        return url
    try:
        version = Path(filename).stat().st_mtime_ns
    except OSError:
        return url
    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.append(("v", str(version)))
    return urlunsplit(parts._replace(query=urlencode(query)))
