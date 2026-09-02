from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.author_list, name="author-list"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),

    # Blog CRUD as HTML pages (Django forms).
    # Named `post-*` rather than `blog-*` so `blog:post-detail` reads as a
    # page and `api:blog-detail` reads as an endpoint.
    path("posts/", views.blog_list, name="post-list"),
    path("posts/new/", views.blog_create, name="post-create"),
    path("posts/<int:pk>/", views.blog_detail, name="post-detail"),
    path("posts/<int:pk>/edit/", views.blog_update, name="post-update"),
    path("posts/<int:pk>/delete/", views.blog_delete, name="post-delete"),

    # The JSON API is not here. See blog/api_urls.py, mounted at /api/.
]
