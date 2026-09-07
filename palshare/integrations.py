"""Calls to computers we do not control.

Written on the standard library so the project stays dependency-free. If you
prefer `requests`, `pip install requests`, add it to requirements.txt, and the
shape below is identical — `requests.get(url, timeout=3)` in place of the
urlopen call.

Both functions here return `None` when anything goes wrong, including "no key
is configured". `None` is a supported answer: `_widget_weather.html` and
`assistant.html` both render an empty state, and they were written before
these functions existed.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_TTL = 600  # ten minutes

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "meta/llama-3.1-8b-instruct"


def current_weather(city="Kathmandu"):
    """Never let a third party decide whether our page renders.

    Three defences, and all three are load-bearing:
      * a cache, so one slow call is not one slow call per visitor
      * a timeout, because the default is "wait until the OS gives up"
      * an except that returns None, because the widget has an empty state and
        a 500 does not
    """
    key = f"weather:{city}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    if not settings.WEATHER_API_KEY:
        logger.warning("WEATHER_API_KEY is not set; the widget will show its empty state")
        return None

    query = urllib.parse.urlencode({"q": city, "appid": settings.WEATHER_API_KEY,
                                    "units": "metric"})
    try:
        with urllib.request.urlopen(f"{WEATHER_URL}?{query}", timeout=3) as response:
            payload = json.load(response)
        data = {
            "city": city,
            "temp_c": round(payload["main"]["temp"]),
            "summary": payload["weather"][0]["description"].title(),
            "icon": "⛅",
        }
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError):
        logger.exception("weather lookup failed for %s", city)
        return None

    cache.set(key, data, timeout=WEATHER_TTL)
    return data


def ask_assistant(prompt):
    """Same shape as `current_weather`, with a longer timeout and no cache.

    No cache because two people asking the same question want two answers, and
    a longer timeout because a model is seconds where a weather API is
    milliseconds. That is also why this only ever runs in the assistant's own
    POST and never in the request that renders a page.

    Nothing here forwards a post: a followers-only post is not ours to send to
    somebody else's model. Only what the person typed goes out.
    """
    if not settings.NVIDIA_API_KEY:
        logger.warning("NVIDIA_API_KEY is not set; the assistant will show its error state")
        return None

    body = json.dumps({
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
    }).encode()
    request = urllib.request.Request(
        NVIDIA_URL,
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {settings.NVIDIA_API_KEY}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
        return payload["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError):
        logger.exception("assistant call failed")
        return None
