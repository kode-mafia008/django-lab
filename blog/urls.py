from django.urls import path
from .views import ping, Home
from django.contrib import admin

urlpatterns = [
    path("ping/", ping),
    path("admin/", admin.site.urls),
    path("", Home)
]       