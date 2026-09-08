"""Routes for PalShare.

This file used to be `TemplateView.as_view(template_name=..., extra_context=...)`
on every line, with `demo.py` supplying the context. Each of those lines has now
been swapped for a real view — and that is all that changed. Every URL, every
route name and every template is exactly what it was, which is why no template
needed editing when the backend landed.

`demo.py` is still here for one more commit, as the written contract these views
are checked against. It has no importer left; delete it once the room has seen
the two side by side.
"""

from django.urls import path

from . import views

app_name = "palshare"

urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),

    # Feed and posts
    path("", views.feed, name="feed"),
    path("posts/new/", views.post_create, name="post-create"),
    path("posts/<int:pk>/", views.post_detail, name="post-detail"),
    path("posts/<int:pk>/edit/", views.post_edit, name="post-edit"),

    # The one-row-or-none actions. POST only, and every one of them returns
    # you to the page whose button you pressed.
    path("posts/<int:pk>/like/", views.post_like, name="post-like"),
    path("posts/<int:pk>/save/", views.post_save, name="post-save"),
    path("posts/<int:pk>/share/", views.post_share, name="post-share"),
    path("comments/<int:pk>/like/", views.comment_like, name="comment-like"),
    path("posts/<int:pk>/react/", views.post_react, name="post-react"),

    # Profile and the follow graph
    path("u/<str:username>/", views.profile, name="profile"),
    path("u/<str:username>/edit/", views.profile_edit, name="profile-edit"),
    path("u/<str:username>/connections/", views.connections, name="connections"),
    path("u/<str:username>/follow/", views.user_follow, name="user-follow"),
    path("u/<str:username>/message/", views.message_user, name="message-user"),

    # Saved, search
    path("saved/", views.saved, name="saved"),
    path("search/", views.search, name="search"),

    # Messaging
    path("inbox/", views.inbox, name="inbox"),
    path("inbox/<int:pk>/", views.thread, name="thread"),
    path("messages/<int:pk>/edit/", views.message_edit, name="message-edit"),
    path("messages/<int:pk>/unsend/", views.message_unsend, name="message-unsend"),

    # Integrations
    path("assistant/", views.assistant, name="assistant"),

    # Settings (public / private profile lives here)
    path("settings/", views.settings_view, name="settings"),
]
