from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = "blog"

router = DefaultRouter()
router.register("authors", views.AuthorViewSet, basename="author")

urlpatterns = [
    path("", views.authors, name="authors"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),

    path("api/", include(router.urls)),
]