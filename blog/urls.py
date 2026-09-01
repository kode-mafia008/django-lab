from django.urls import path

from . import views
from .views import AuthorListView


app_name = "blog"


urlpatterns = [
    # HTML pages
    path("", views.author_list, name="author-list"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),

    # API
    path("api/authors/", AuthorListView.as_view(), name="author-api"),
]