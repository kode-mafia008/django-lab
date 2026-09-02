"""The blog app's JSON API routes.

Separate from `blog/urls.py` on two axes:

* **Namespace** — `app_name = "api"`, so these reverse as `api:author-list`
  and `api:blog-list`. `blog/urls.py` owns the `blog:` namespace and its HTML
  page names. Nothing can shadow anything.
* **Mount point** — `config/urls.py` includes this at `api/`, not under the
  `blogs/` prefix the HTML pages live at. So the API is `/api/blogs/`, not
  `/blogs/api/blogs/`.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import AuthorViewSet, BlogViewSet

app_name = "api"

router = DefaultRouter()
router.register("authors", AuthorViewSet, basename="author")
router.register("blogs", BlogViewSet, basename="blog")

urlpatterns = [
    path("", include(router.urls)),
]
