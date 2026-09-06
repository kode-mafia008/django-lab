"""Rate limiting for the plain-Django HTML pages.

DRF's throttles are enforced by `APIView.initial()`. `blog/views.py` holds
function views that never touch DRF, so `DEFAULT_THROTTLE_CLASSES` does nothing
for them — the same gap `@login_required` had to close for permissions.

This is the smallest honest fix: a decorator over Django's cache framework,
with no new dependency. It counts requests in a **fixed window**, which is
simpler than DRF's sliding window and admits one known weakness — a client can
send `limit` requests at the end of one window and `limit` more at the start of
the next, so the worst-case burst is double the rate. That is an acceptable
trade for a page-read limit; it would not be for a login endpoint, which is why
the login endpoint uses DRF's throttle instead.
"""

import math
import time
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render

# Same spelling DRF uses, so there is one rate syntax in the project.
PERIODS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_rate(rate):
    """`"30/min"` -> `(30, 60)`. Only the first letter of the period is read."""
    count, _, period = rate.partition("/")
    return int(count), PERIODS[period[0]]


def client_key(request, scope):
    """One counter per caller per scope.

    Authenticated callers are counted by primary key, so a shared office IP
    does not make one user's reading throttle everybody else's.

    Anonymous callers are counted by `REMOTE_ADDR` and nothing else.
    `X-Forwarded-For` is supplied by the client and forgeable, so trusting it
    hands an attacker an unlimited supply of fresh counters — read it only
    behind a proxy you control that overwrites the header.
    """
    if request.user.is_authenticated:
        return f"page-throttle:{scope}:user:{request.user.pk}"
    return f"page-throttle:{scope}:ip:{request.META.get('REMOTE_ADDR', 'unknown')}"


def rate_limit(scope, rate):
    """Refuse a view with `429` once `rate` is exceeded for this caller.

        @rate_limit(scope="blog-detail", rate="30/min")
        def blog_detail(request, pk):

    `settings.PAGE_THROTTLE_RATES[scope]` overrides the rate written here, so
    the numbers live with the other security settings and the decorator keeps a
    working default if the setting is missing.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            configured = getattr(settings, "PAGE_THROTTLE_RATES", {})
            limit, window = parse_rate(configured.get(scope, rate))
            key = client_key(request, scope)

            # `add` writes only when the key is absent, so the window opens on
            # the first request and closes by expiry — no cleanup, no cron.
            if cache.add(key, 0, timeout=window):
                cache.set(f"{key}:reset", time.time() + window, timeout=window)
            try:
                used = cache.incr(key)
            except ValueError:
                # The key expired between `add` and `incr`. That is the first
                # request of a new window, not an error.
                cache.set(key, 1, timeout=window)
                cache.set(f"{key}:reset", time.time() + window, timeout=window)
                used = 1

            if used > limit:
                reset_at = cache.get(f"{key}:reset", time.time() + window)
                retry_after = max(1, math.ceil(reset_at - time.time()))
                response = render(
                    request,
                    "blog/throttled.html",
                    {"retry_after": retry_after, "limit": limit},
                    status=429,
                )
                # The one header a well-behaved client actually reads.
                response["Retry-After"] = str(retry_after)
                return response

            return view(request, *args, **kwargs)

        return wrapper

    return decorator
