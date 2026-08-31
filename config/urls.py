from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from blog.api import AuthorViewSet

router = DefaultRouter()
router.register("authors", AuthorViewSet, basename="author")

urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML pages
    path("", include("blog.urls")),

    # JSON API
    path("api/", include(router.urls)),
    path("api/auth/", include("accounts.urls")),

    # OpenAPI schema and docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]