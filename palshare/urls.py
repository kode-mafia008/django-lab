"""Routes for the UI shell — `TemplateView` only, on purpose.

This app has no `views.py`, no `models.py` and no `forms.py`. It is the UI
half of PalShare, built so that the people writing the backend can hand
their querysets to a page that already exists.

Every route below renders a template and nothing else. When a real view is
ready, replace the `TemplateView.as_view(...)` on that one line with it — the
name, the URL and the template all stay the same, so no template edit is
needed and nothing else in the app breaks.
"""

from django.urls import path
from django.views.generic import TemplateView

from . import demo

app_name = "palshare"


def page(template, **context):
    """One page of the shell, pre-filled with placeholder data.

    `extra_context` is the seam: it is what a real view's `get_context_data`
    will return. Delete the argument and the page still renders — every
    template has an empty state.
    """
    # Shell-wide context: the header, the left nav and the right rail need
    # these on every page. When the backend lands, this becomes a context
    # processor rather than three lines here.
    context.setdefault("current_user", demo.CURRENT_USER)
    context.setdefault("weather", demo.WEATHER)
    context.setdefault("suggestions", demo.PEOPLE[1:4])
    return TemplateView.as_view(template_name=f"palshare/{template}", extra_context=context)


urlpatterns = [
    # Auth
    path("login/", page("login.html"), name="login"),
    path("register/", page("register.html"), name="register"),

    # Feed and posts
    path("", page("feed.html", posts=demo.POSTS, people=demo.PEOPLE), name="feed"),
    path("posts/new/", page("post_form.html", heading="New post"), name="post-create"),
    path("posts/<int:pk>/", page("post_detail.html", post=demo.POSTS[0],
                                 comments=demo.COMMENTS), name="post-detail"),
    path("posts/<int:pk>/edit/", page("post_form.html", heading="Edit post",
                                      post=demo.POSTS[0]), name="post-edit"),

    # Profile and the follow graph
    path("u/<str:username>/", page("profile.html", profile=demo.PROFILE,
                                   posts=demo.POSTS), name="profile"),
    path("u/<str:username>/edit/", page("profile_edit.html", profile=demo.PROFILE),
         name="profile-edit"),
    path("u/<str:username>/connections/", page("connections.html", people=demo.PEOPLE),
         name="connections"),

    # Saved, search
    path("saved/", page("saved.html", posts=demo.POSTS[:2]), name="saved"),
    path("search/", page("search.html", people=demo.PEOPLE, posts=demo.POSTS[:2]),
         name="search"),

    # Messaging
    path("inbox/", page("inbox.html", conversations=demo.CONVERSATIONS), name="inbox"),
    path("inbox/<int:pk>/", page("thread.html", conversation=demo.CONVERSATIONS[0],
                                 thread_messages=demo.MESSAGES), name="thread"),

    # Integrations
    path("assistant/", page("assistant.html", turns=demo.AI_TURNS), name="assistant"),

    # Settings (public / private profile lives here)
    path("settings/", page("settings.html", profile=demo.PROFILE), name="settings"),
]
