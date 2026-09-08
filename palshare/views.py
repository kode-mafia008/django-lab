"""The HTML half of the app. The other half is `api.py`.

Every page renders through the serializers in `serializers.py`, so the page and
the API cannot disagree about what a post is. The usual alternative — pass the
queryset to the template and let it call model attributes — works fine until
the API adds a field the page needs, and then there are two definitions.

Not one template was changed to make these views work. The URL names, the
context keys and the markup are all exactly what the shell was built with;
`demo.py` said what the shapes were, and these views produce them.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.template.defaultfilters import date as date_filter
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_http_methods

from .integrations import ask_assistant, current_weather
from .models import Comment, Conversation, Follow, Message, Post, Profile, Reaction
from .services import (
    add_comment,
    attach_media,
    edit_message,
    set_avatar,
    set_reaction,
    unsend_message,
    conversation_with,
    toggle_comment_like,
    toggle_follow,
    toggle_like,
    toggle_save,
    toggle_share,
)
from .queries import (
    conversations_for,
    may_see_posts,
    people,
    saved_posts,
    search as search_query,
    visible_comments,
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


def back(request, fallback):
    """Return to the page the button was on.

    `url_has_allowed_host_and_scheme` is not optional: without it, `?next=` is
    an open redirect, and an open redirect on a login-walled page is how a
    phishing link borrows your domain.
    """
    target = request.POST.get("next") or request.META.get("HTTP_REFERER", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                                  require_https=request.is_secure()):
        return redirect(target)
    return redirect(fallback)


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
    # Serialized rather than hand-built. The hand-built dict had three of the
    # four keys `_avatar.html` reads, so the header and the composer showed
    # your initial even after you had uploaded a picture — while every other
    # avatar on the same page showed the picture. A shape assembled twice is a
    # shape that disagrees with itself.
    context.setdefault("current_user",
                       PersonRowSerializer(user, context={"request": request}).data)
    # `None` when the key is missing or the API is down. The widget has an
    # empty state and renders it.
    context.setdefault("weather", current_weather())
    # The one palette, defined on the model, handed to every template that
    # offers emoji — the picker and the reaction bar read the same list.
    context.setdefault("emoji", [value for value, _ in Reaction.EMOJI])
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
        # `_composer.html` has had an "Add media" file input since hour one and
        # this handler read only `text`, so anything attached here was dropped
        # on the floor without a word. Same rule as `post_create`.
        uploads = request.FILES.getlist("media")
        if text or uploads:
            try:
                with transaction.atomic():
                    post = Post.objects.create(author=request.user, text=text)
                    attach_media(post, uploads)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
        return redirect("palshare:feed")

    posts = visible_posts(request.user)
    if request.GET.get("filter") == "following":
        # The tab says Following, so it means posts by people you follow —
        # not "everything except mine", which is what this used to do.
        posts = posts.filter(author__in=Follow.objects.filter(follower=request.user)
                             .values("following"))
    return render(request, "palshare/feed.html",
                  shell(request, active="feed", **posts_page(request, posts)))


@signed_in
@require_http_methods(["GET", "POST"])
def post_create(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        # `getlist`, not `request.FILES["media"]`: the input is `multiple`, and
        # the dict access silently returns the last file of four.
        uploads = request.FILES.getlist("media")
        if text or uploads:
            try:
                # The post and its files are one write. Without the atomic
                # block a rejected file leaves an empty post behind, which is
                # the user having posted something they did not write.
                with transaction.atomic():
                    post = Post.objects.create(
                        author=request.user,
                        text=text,
                        followers_only=bool(request.POST.get("private")),
                    )
                    attach_media(post, uploads)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
            else:
                return redirect("palshare:post-detail", pk=post.pk)
        else:
            # A photo with no caption is a post. Empty is not.
            messages.error(request, "A post needs some text or a file.")
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
        uploads = request.FILES.getlist("media")
        if text or uploads or post.media.exists():
            try:
                with transaction.atomic():
                    post.text = text
                    post.followers_only = bool(request.POST.get("private"))
                    post.save(update_fields=["text", "followers_only", "updated_at"])
                    # Editing adds files, it does not replace them: removing one
                    # is a different action and needs its own control.
                    attach_media(post, uploads)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
            else:
                return redirect("palshare:post-detail", pk=post.pk)
        else:
            messages.error(request, "A post needs some text or a file.")
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
            # `parent` arrives from the Reply form under each comment. The
            # service refuses to nest past one level; the model cannot.
            parent = None
            parent_id = request.POST.get("parent")
            if parent_id:
                parent = get_object_or_404(Comment, pk=parent_id, post=post)
            add_comment(request.user, post, text, parent=parent)
        return redirect("palshare:post-detail", pk=post.pk)

    comments = visible_comments(request.user, post)
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

    # The three tabs were `?tab=` links that no view read, so Media and Likes
    # both rendered the Posts list and the active tab never moved.
    tab = request.GET.get("tab", "posts")
    if tab not in {"posts", "media", "likes"}:
        tab = "posts"

    context = shell(request, active="profile", posts=[], tab=tab,
                    profile=PersonSerializer(owner, context={"request": request}).data)
    if may_see_posts(request.user, owner):
        posts = visible_posts(request.user)
        if tab == "media":
            # `media__isnull=False` alone returns one row per attached file.
            posts = posts.filter(author=owner, media__isnull=False).distinct()
        elif tab == "likes":
            # Posts this person liked, not posts of theirs that were liked —
            # which is what the word means everywhere else it appears in a
            # social app.
            posts = posts.filter(likes__user=owner)
        else:
            posts = posts.filter(author=owner)
        context.update(posts_page(request, posts))
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
        # MEDIA_ROOT and the validator both exist now, so the file input on
        # this form is no longer ignored. It was, silently, which is why the
        # picture never changed and nothing ever said why.
        upload = request.FILES.get("avatar")
        if upload:
            try:
                set_avatar(profile, upload)
            except ValidationError as exc:
                for message in exc.messages:
                    messages.error(request, message)
                return render(request, "palshare/profile_edit.html", shell(
                    request,
                    profile=PersonSerializer(user, context={"request": request}).data))
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
        # `?edit=<id>` opens one bubble as a form. A query parameter rather
        # than JavaScript, for the same reason every other control here is a
        # form: it survives a reload and it works with the keyboard.
        editing=request.GET.get("edit", ""),
        emoji=[value for value, _ in Reaction.EMOJI],
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
                # Two different failures wore one message, so "it does not
                # work" was indistinguishable from "nobody has configured it".
                # The first is a five-second fix and the page now says so.
                if not settings.NVIDIA_API_KEY:
                    error = ("The assistant has no API key. Set NVIDIA_API_KEY in .env "
                             "and restart the server — see .env.example.")
                else:
                    error = "The assistant is unavailable right now. Try again in a moment."
            else:
                turns.append({"role": "assistant", "text": reply})
            request.session["assistant_turns"] = turns[-20:]

    return render(request, "palshare/assistant.html",
                  shell(request, active="assistant", turns=turns, error=error))


# --- the one-row-or-none actions -----------------------------------------
#
# Seven controls in the shell were `<button type="button">` with nothing behind
# them. They are real forms now, and each one posts here, flips a row and
# returns you to the page you were on. No JavaScript: a form works with the
# keyboard, with the back button, and with JavaScript switched off, and the
# whole app already reloads on every write anyway.

@signed_in
@require_POST
def post_like(request, pk):
    toggle_like(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "palshare:feed")


@signed_in
@require_POST
def post_save(request, pk):
    toggle_save(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "palshare:feed")


@signed_in
@require_POST
def post_share(request, pk):
    toggle_share(request.user, get_object_or_404(visible_posts(request.user), pk=pk))
    return back(request, "palshare:feed")


@signed_in
@require_POST
def post_react(request, pk):
    """The emoji bar under a post. One reaction per person, and pressing the
    one you already picked takes it back."""
    post = get_object_or_404(visible_posts(request.user), pk=pk)
    try:
        set_reaction(request.user, post, request.POST.get("emoji") or None)
    except ValidationError as exc:
        for message in exc.messages:
            messages.error(request, message)
    return back(request, reverse("palshare:post-detail", args=[post.pk]))


# --- messages you can take back -------------------------------------------
#
# Both of these are POST-only and both re-check the sender in `services.py`,
# not here: "you may only change your own message" is a rule about messages,
# and a rule that lives in a view is a rule the API gets to disagree with.

@signed_in
@require_POST
def message_edit(request, pk):
    message = get_object_or_404(
        Message.objects.filter(conversation__participants=request.user), pk=pk)
    try:
        edit_message(request.user, message, request.POST.get("text", ""))
    except ValidationError as exc:
        for text in exc.messages:
            messages.error(request, text)
    return redirect("palshare:thread", pk=message.conversation_id)


@signed_in
@require_POST
def message_unsend(request, pk):
    message = get_object_or_404(
        Message.objects.filter(conversation__participants=request.user), pk=pk)
    try:
        unsend_message(request.user, message)
    except ValidationError as exc:
        for text in exc.messages:
            messages.error(request, text)
    return redirect("palshare:thread", pk=message.conversation_id)


@signed_in
@require_POST
def comment_like(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    # You may only like a comment on a post you are allowed to read.
    get_object_or_404(visible_posts(request.user), pk=comment.post_id)
    toggle_comment_like(request.user, comment)
    return back(request, reverse("palshare:post-detail", args=[comment.post_id]))


@signed_in
@require_POST
def user_follow(request, username):
    target = get_object_or_404(User, username=username)
    try:
        toggle_follow(request.user, target)
    except ValueError as error:
        messages.error(request, str(error))
    return back(request, reverse("palshare:profile", args=[target.username]))


@signed_in
@require_POST
def message_user(request, username):
    """The profile's Message button. Opens the one conversation with that
    person, creating it on first use."""
    other = get_object_or_404(User, username=username)
    if other == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect("palshare:inbox")
    conversation = conversation_with(request.user, other)
    return redirect("palshare:thread", pk=conversation.pk)


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
