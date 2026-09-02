from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = "blog"

router = DefaultRouter()

router.register(r"authors", views.AuthorViewSet, basename="author")
router.register(r"blogs", views.BlogViewSet, basename="blog")

urlpatterns = [
    path("", views.author_list, name="author-list"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),
    path("api/", include(router.urls)),
]