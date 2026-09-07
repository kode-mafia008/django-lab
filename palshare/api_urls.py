from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import PostViewSet, UserViewSet

app_name = "palshare-api"

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("users", UserViewSet, basename="user")

urlpatterns = [path("", include(router.urls))]
