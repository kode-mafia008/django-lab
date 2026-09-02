from django.urls import path,include
from . import views


app_name = "blog"


urlpatterns = [
    path("", views.author_list, name="author-list"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),

    # API endpoints(Class-based views)
    path('api/authors',views.AuthorListView.as_view()),
]
