from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView, 
    SpectacularSwaggerView
)


urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML pages
    path("blogs/", include("blog.urls")),
    path("accounts/" ,include("accounts.urls")),

    # PalShare
    path("palshare/", include("palshare.urls")),

    # JSON API
    path("api/", include("blog.api_urls")),
    path("api/palshare/", include("palshare.api_urls")),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
]

# Uploaded files, served by Django itself — for development only. It is
# single-threaded, it does no caching and it reads the file into the response,
# so in production the web server serves MEDIA_ROOT and this block does
# nothing (`static()` returns [] when DEBUG is False).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
