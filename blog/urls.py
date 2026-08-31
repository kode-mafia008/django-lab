from django.urls import path
from .views import author_list, author_detail
from django.contrib import admin

app_name = "blog"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", author_list, name="author-list"),
    path("authors/<int:pk>/", author_detail, name="author-detail")
]       