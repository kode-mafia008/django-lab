import math, time
from functools import wraps

from django.conf import settings

from django.shortcuts import render
from django.core.cache import cache

PERIODS = {
    "s": 1,
    "m": 60, 
    "h": 3600,
    "d": 86400,
}

def parse_rate(rate):
    count, _, period = rate.partition("/")
    return int(count), PERIODS[period[0]]

def client_key(request, scope):
    if request.user.is_authenticated:
        return f"page-throttle:{scope}:{request.user.pk}"
    return f"page-throttle:{scope}:ip:{request.META.get('REMOTE_ADDR', 'unknown')}"

def rate_limit(rate, scope):
    """ Refuse a view with `429` once `rate` is exceeded for this caller.

        @rate_limit(scope='blog-detail', rate='5/min')
        def blog_detail(request, pk):
            ...
            
    `settings.PAGE_THROTTLE_RATES`, can be used to override the default rate for a given scope.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            configured = getattr(settings, "PAGE_THROTTLE_RATES", {})
            limit, window = parse_rate(configured.get(scope, rate))
            key = client_key(request, scope)
            
            if cache.add(key, 0, timeout=window):
                cache.set(f"{key}:reset", time.time()+window, timeout=window)
            try:
                used = cache.incr(key)
            except ValueError:
                cache.set(key, 1, timeout=window)
                cache.set(f"{key}:reset", time.time()+window, timeout=window)
                used = 1
                
            if used > limit:
                reset_at = cache.get(f"{key}:reset", time.time() + window)
                retry_after = max(1, math.ceil(reset_at - time.time()))
                response = render(
                    request,
                    "blog/throttle.html",
                    {"retry_after": retry_after, "limit": limit},
                    status = 429,
                )
                response["Retry-After"] = str(retry_after)
                return response
            return view(request, *args, **kwargs)
        return wrapper
    return decorator