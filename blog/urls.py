from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views


app_name = "blog"

router=DefaultRouter()
router.register(r'blogs', views.BlogViewSet, basename='blog')
router.register(r'authors', views.AuthorViewSet, basename='author')



urlpatterns = [
    path("", views.author_list, name="author-list"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),


    path("posts/", views.blog_list, name="post-list"),
    path("posts/new/", views.blog_create, name="post-create"),
    path("posts/<int:pk>/", views.blog_detail, name="post-detail"),
    path("posts/<int:pk>/edit/", views.blog_update, name="post-update"),
    path("posts/<int:pk>/delete/", views.blog_delete, name="post-delete"),

    path('api/',include(router.urls))
]
