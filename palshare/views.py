"""The HTML half of the app. The other half is `api.py`.

Every page renders through the serializers in `serializers.py`, so the page and
the API cannot disagree about what a post is. The usual alternative — pass the
queryset to the template and let it call model attributes — works fine until
the API adds a field the page needs, and then there are two definitions.

Not one template was changed to make these views work. The URL names, the
context keys and the markup are all exactly what the shell was built with;
`demo.py` said what the shapes were, and these views produce them.
"""

from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .integrations import ask_assistant, current_weather
from .models import Comment, Conversation, Message, Post, Profile
from .queries import (
    conversations_for,
    may_see_posts,
    people,
    saved_posts,
    search as search_query,
    suggestions_for,
    visible_posts,
)
from .serializers import (
    CommentSerializer,
    MessageSerializer,
    PersonRowSerializer,
    PersonSerializer,
    PostSerializer,
    display_name,
    initial,
)

PAGE_SIZE = 20

# `@login_required` alone would send people to `settings.LOGIN_URL`, which is
# the admin login — a different app's front door. PalShare has its own.
signed_in = login_required(login_url="palshare:login")


def profile_of(user):
    """Every user in this app has a Profile; some of them do not know it yet.

    `get_or_create` rather than a signal: a signal fires on every `User` save
    in the whole project, including the blog app's, and this is the only place
    that needs the row.
    """
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def shell(request, **context):
    """The three things every signed-in page needs: the header, the nav and
    the right rail.

    `urls.py` used to set these from `demo.py`, one page at a time. If a fourth
    thing turns up, this becomes a context processor.
    """
    user = request.user
    context.setdefault("current_user", {
        "username": user.username,
        "name": display_name(user),
        "avatar": initial(user),
    })
    # `None` when the key is missing or the API is down. The widget has an
    # empty state and renders it.
    context.setdefault("weather", current_weather())
    context.setdefault("suggestions", PersonRowSerializer(
        suggestions_for(user), many=True, context={"request": request}).data)
    return context


def posts_page(request, queryset):
    """One page of posts, serialized, plus the `page_obj` the pager reads."""
    page = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))
    return {
        "posts": PostSerializer(page.object_list, many=True,
                                context={"request": request}).data,
        "page_obj": page,
    }


# --- auth -----------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("palshare:feed")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect("palshare:feed")
    # `login.html` renders its own one-line error whenever `form.errors` is
    # truthy, which is why the real form goes into the context rather than a
    # hand-rolled flag.
    return render(request, "palshare/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("palshare:feed")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        if not username or not password:
            error = "Pick a username and a password."
        elif User.objects.filter(username__iexact=username).exists():
            error = "That username is taken."
        else:
            user = User.objects.create_user(username, email=email, password=password)
            Profile.objects.create(user=user)
            auth_login(request, user)
            return redirect("palshare:feed")
    return render(request, "palshare/register.html", {"error": error})


# --- feed and posts -------------------------------------------------------

@signed_in
@require_http_methods(["GET", "POST"])
def feed(request):
    """The composer at the top of this page posts back to this URL.

    `_composer.html` is included with `action=""`, which means "this page" —
    so the POST arrives here and the redirect afterwards is what stops a
    refresh from posting twice.
    """
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            Post.objects.create(author=request.user, text=text)
        return redirect("palshare:feed")

    posts = visible_posts(request.user)
    if request.GET.get("filter") == "following":
        posts = posts.exclude(author=request.user)
    return render(request, "palshare/feed.html",
                  shell(request, active="feed", **posts_page(request, posts)))


@signed_in
@require_http_methods(["GET", "POST"])
def post_create(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            post = Post.objects.create(
                author=request.user,
                text=text,
                followers_only=bool(request.POST.get("private")),
            )
            return redirect("palshare:post-detail", pk=post.pk)
        messages.error(request, "A post needs some text.")
    return render(request, "palshare/post_form.html",
                  shell(request, heading="New post"))


@signed_in
@require_http_methods(["GET", "POST"])
def post_edit(request, pk):
    # `visible_posts`, not `Post.objects`: a post you cannot see is a 404, not
    # a 403 — the second one confirms the row exists.
    post = get_object_or_404(visible_posts(request.user), pk=pk)
    if post.author_id != request.user.id:
        # Day 10's rule, on the HTML side. `IsAuthorOrReadOnly` says the same
        # thing to the API.
        return HttpResponseForbidden("You can only change things you created.")
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            post.text = text
            post.followers_only = bool(request.POST.get("private"))
            post.save(update_fields=["text", "followers_only", "updated_at"])
            return redirect("palshare:post-detail", pk=post.pk)
        messages.error(request, "A post needs some text.")
    return render(request, "palshare/post_form.html", shell(
        request,
        heading="Edit post",
        post=PostSerializer(post, context={"request": request}).data,
    ))


@signed_in
@require_http_methods(["GET", "POST"])
def post_detail(request, pk):
    post = get_object_or_404(visible_posts(request.user), pk=pk)
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            Comment.objects.create(post=post, author=request.user, text=text)
            # `F()`, not `post.comment_count + 1`: two people commenting at
            # once both read the same number and both write it back.
            Post.objects.filter(pk=post.pk).update(comment_count=F("comment_count") + 1)
        return redirect("palshare:post-detail", pk=post.pk)

    comments = (Comment.objects
                .filter(post=post, parent__isnull=True)
                .select_related("author")
                .prefetch_related("replies__author"))
    return render(request, "palshare/post_detail.html", shell(
        request,
        post=PostSerializer(post, context={"request": request}).data,
        comments=CommentSerializer(comments, many=True,
                                   context={"request": request}).data,
    ))


@signed_in
def saved(request):
    return render(request, "palshare/saved.html", shell(
        request, active="saved", **posts_page(request, saved_posts(request.user))))


# --- profile and the follow graph ----------------------------------------

@signed_in
def profile(request, username):
    # Fetched through `people()` so the header's Follow button reads the same
    # annotation every user row in the app reads, rather than its own query.
    owner = get_object_or_404(people(request.user), username=username)
    profile_of(owner)  # `may_see_posts` reads `owner.profile`

    context = shell(request, active="profile", posts=[],
                    profile=PersonSerializer(owner, context={"request": request}).data)
    if may_see_posts(request.user, owner):
        context.update(posts_page(request, visible_posts(request.user).filter(author=owner)))
    return render(request, "palshare/profile.html", context)


@signed_in
@require_http_methods(["GET", "POST"])
def profile_edit(request, username):
    if username != request.user.username:
        return HttpResponseForbidden("You can only edit your own profile.")
    user = request.user
    profile = profile_of(user)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        first, _, last = name.partition(" ")
        user.first_name, user.last_name = first, last
        user.save(update_fields=["first_name", "last_name"])
        profile.bio = request.POST.get("bio", "").strip()
        profile.save(update_fields=["bio"])
        # The file input on this form is ignored until Part 6 lands MEDIA_ROOT
        # and the upload validator. Saving the file without either is how you
        # get an unvalidated upload directory.
        messages.success(request, "Profile updated.")
        return redirect("palshare:profile", username=user.username)
    return render(request, "palshare/profile_edit.html", shell(
        request, profile=PersonSerializer(user, context={"request": request}).data))


@signed_in
def connections(request, username):
    owner = get_object_or_404(User, username=username)
    tab = request.GET.get("tab", "followers")
    # `owner.followers` is the Follow rows where owner is followed, so the
    # people are on the other end of each row. Read the related_names in
    # models.py before changing this line; they are the opposite of what they
    # look like.
    if tab == "following":
        queryset = User.objects.filter(followers__follower=owner)
    else:
        queryset = User.objects.filter(following__following=owner)
    return render(request, "palshare/connections.html", shell(
        request,
        people=PersonRowSerializer(people(request.user, queryset), many=True,
                                   context={"request": request}).data,
    ))


# --- search ---------------------------------------------------------------

@signed_in
def search(request):
    results = search_query(request.user, request.GET.get("q", ""))
    return render(request, "palshare/search.html", shell(
        request,
        active="search",
        query=results["query"],
        people=PersonRowSerializer(results["people"], many=True,
                                   context={"request": request}).data,
        posts=PostSerializer(results["posts"], many=True,
                             context={"request": request}).data,
    ))


# --- messaging ------------------------------------------------------------

def when(moment):
    """A time for today, a date for anything older. `demo.py` showed both."""
    local = timezone.localtime(moment)
    if local.date() == timezone.localdate():
        return date_filter(local, "H:i")
    return date_filter(local, "j M")


@signed_in
def inbox(request):
    conversations = [{
        "id": row["conversation"].pk,
        "person": PersonRowSerializer(row["other"], context={"request": request}).data,
        "last_message": row["last"].text if row["last"] else "",
        "unread": row["unread"],
        "updated_at": when(row["conversation"].updated_at),
    } for row in conversations_for(request.user)]
    return render(request, "palshare/inbox.html",
                  shell(request, active="inbox", conversations=conversations))


@signed_in
@require_http_methods(["GET", "POST"])
def thread(request, pk):
    # Filtering by participant is the permission check: a conversation you are
    # not in does not exist as far as this view is concerned.
    conversation = get_object_or_404(
        Conversation.objects.filter(participants=request.user).prefetch_related("participants"),
        pk=pk)
    other = next((p for p in conversation.participants.all() if p.pk != request.user.pk),
                 request.user)

    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            Message.objects.create(conversation=conversation, sender=request.user, text=text)
            # `Meta.ordering` sorts the inbox by `updated_at`, which only means
            # anything if sending a message touches it.
            conversation.save(update_fields=["updated_at"])
        return redirect("palshare:thread", pk=conversation.pk)

    unread = conversation.messages.exclude(sender=request.user).filter(read_at__isnull=True)
    unread.update(read_at=timezone.now())

    thread_messages = conversation.messages.select_related("sender")
    return render(request, "palshare/thread.html", shell(
        request,
        active="inbox",
        conversation={
            "id": conversation.pk,
            "person": PersonRowSerializer(other, context={"request": request}).data,
        },
        # Never `messages`: django.contrib.messages owns that name, and
        # base.html renders whatever is in it as flash messages.
        thread_messages=MessageSerializer(thread_messages, many=True,
                                          context={"request": request}).data,
    ))


# --- integrations ---------------------------------------------------------

@signed_in
@require_http_methods(["GET", "POST"])
def assistant(request):
    """The conversation lives in the session, not the database.

    Nothing in the schema stores assistant turns, and inventing a table for a
    demo feature is how a schema grows things nobody maintains.
    """
    turns = request.session.get("assistant_turns", [])
    error = None

    if request.method == "POST":
        prompt = request.POST.get("prompt", "").strip()
        if prompt:
            turns = turns + [{"role": "you", "text": prompt}]
            reply = ask_assistant(prompt)
            if reply is None:
                error = "The assistant is unavailable right now. Try again in a moment."
            else:
                turns.append({"role": "assistant", "text": reply})
            request.session["assistant_turns"] = turns[-20:]

    return render(request, "palshare/assistant.html",
                  shell(request, active="assistant", turns=turns, error=error))


# --- settings -------------------------------------------------------------

@signed_in
@require_http_methods(["GET", "POST"])
def settings_view(request):
    profile = profile_of(request.user)
    if request.method == "POST":
        if "logout" in request.POST:
            # Logout is a POST for a reason: a GET logout can be triggered by
            # any <img> tag on any page on the internet.
            auth_logout(request)
            return redirect("palshare:login")
        profile.is_private = bool(request.POST.get("is_private"))
        profile.save(update_fields=["is_private"])
        messages.success(request, "Settings saved.")
        return redirect("palshare:settings")
    return render(request, "palshare/settings.html", shell(
        request, active="settings",
        profile=PersonSerializer(request.user, context={"request": request}).data))
