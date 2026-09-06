---
title: "PalShare — the 12-hour build"
subtitle: "Eleven people, one repository, one social network: contracts, branches, and what done means"
author: "Django Practical Lab — project guide"
date: "Django 5.2 LTS · DRF 3.18 · Simple JWT 5.5 · drf-spectacular 0.30"
---

# What this is

Days 1–10 were one person typing along. This is different: eleven people, twelve hours, one
repository, and a product with a name — **PalShare**.

Everything you learned has to survive contact with ten other developers. The parts of that which
break are never the Django parts. They are: two people editing `views.py` at once, a frontend
waiting on an endpoint that does not exist, a backend guessing what the page needs, and an
integration hour where nothing fits.

This guide is about not doing that.

| # | Feature | Owner | Endpoint | Page |
| --- | --- | --- | --- | --- |
| 1 | Login / logout | backend | `/accounts/login/`, `/accounts/logout/` | `login.html`, `register.html` |
| 2 | Create post — text, images, media | backend | `POST /api/palshare/posts/` | `post_form.html` |
| 3 | Comments / replies | backend | `/api/palshare/posts/<id>/comments/` | `post_detail.html` |
| 4 | Like & share | backend | `POST .../like/`, `.../unlike/` | `_post_card.html` |
| 5 | Follow / unfollow | backend | `POST /api/palshare/users/<name>/follow/` | `profile.html`, `connections.html` |
| 6 | Inbox / messaging | backend | `/api/palshare/conversations/` | `inbox.html`, `thread.html` |
| 7 | Saved posts | backend | `POST .../save/` | `saved.html` |
| 8 | Profile public / private | backend | `/api/palshare/users/<name>/` | `profile.html`, `settings.html` |
| 9 | Search | backend | `/api/palshare/search/?q=` | `search.html` |
| 10 | Weather API | integrations | server-side call, cached | `_widget_weather.html` |
| 11 | AI via NVIDIA API | integrations | server-side call, timeout | `assistant.html` |

## The team

| Role | Who | Owns |
| --- | --- | --- |
| Project manager | Menuka | the board, the clock, the demo running order |
| Team lead | Himanshu | the contract in `demo.py`, review, the integration branch |
| Backend | Kaushal, Ranjan | `models.py`, `serializers.py`, `api.py`, `views.py` |
| UI & frontend | Suraj | `templates/`, `palshare.css` |
| Testing & QA | Bidhya, Barsha, Renisha, Khushi, Sonu, Aditya | the checklist in Part 12, and every bug report |

## Conventions

Same markers as Days 1–10.

| Marker | Meaning |
| --- | --- |
| **TYPE** | Type this exactly. |
| **EXPECT** | What should appear. If you see something else, stop and fix it. |
| **CHECKPOINT** | A verifiable state. The whole team reaches it before anyone moves on. |
| **WHY** | The reasoning. |
| **DOCS** | The official documentation. |

## Start here

**TYPE**

```bash
cd ~/code/django-lab
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
git switch main
git pull origin main
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/palshare/>.

**EXPECT** — a working social network. Feed, profile, post detail, inbox, search, settings, and a
weather widget. Click everything.

Now open `palshare/`. There are no models. There are no views. **Every page you just clicked is a
template with fake data behind it.**

That is the starting position, and it is deliberate.

**CHECKPOINT 0** — everyone has the app running and has clicked all fifteen pages. Nobody starts
typing until the whole room has seen the shell.

\newpage

# Part 1 — Why the UI already exists

A twelve-hour build has one scheduling problem: the frontend cannot start until the backend is
done, and the backend does not know what to build until the frontend says what it needs. Teams
solve this by having the frontend guess, and then spend the integration hour discovering the guess
was wrong.

The shell removes the dependency. It is fifteen pages, eleven partials and one stylesheet, built
against `palshare/demo.py` — a file of dictionaries.

## 1.1 `demo.py` is the contract

Open it. Read the docstring at the top.

```python
"""Placeholder data — and the contract the backend has to satisfy.

This module exists so the UI can be reviewed and clicked through before a
single model is written. It is also the **handoff document**: the shape of
these dictionaries is exactly what each template reads, so a real view is
"correct" when its context matches what is here.
"""
```

That is the whole idea. `POSTS[0]` is not sample data, it is a **specification**:

```python
POSTS = [
    {
        "id": 1,
        "author": PEOPLE[0],
        "age": "2 hours ago",
        "text": "Hour three and PalShare has working authentication. Feed next.",
        "media": [{"kind": "image", "alt": "Screenshot of the login page"}],
        "likes": 24, "comments": 5, "shares": 2,
        "liked": True, "saved": False,
    },
```

A backend view is finished when its context looks like that. Not similar to it — like it.

**WHY a dictionary and not a docstring** — because a docstring drifts and a dictionary renders. If
the contract changes and the pages still work, the change was safe. If they break, you found out in
one second rather than in the integration hour.

## 1.2 `urls.py` is the seam

Every page is one line:

```python
    path("saved/", page("saved.html", posts=demo.POSTS[:2]), name="saved"),
```

`page()` builds a `TemplateView` with `extra_context`. When the real view exists, that one line
becomes:

```python
    path("saved/", views.saved, name="saved"),
```

The URL does not change. The name does not change. The template does not change. **Nothing Suraj
wrote gets edited by anyone doing backend work**, which is the entire point.

## 1.3 The rules that make eleven people work

1. **The contract is owned by one person.** Himanshu. Changing a key in `demo.py` is a conversation
   before it is a commit, because every change invalidates somebody's work in progress.
2. **One feature, one branch, one PR.** `<first_name>/palshare-<feature>` — `kaushal/palshare-posts`,
   `suraj/palshare-profile`. Never two people on one branch.
3. **PRs go to `palshare`, not to `main`.** The integration branch is created in Part 2 and merged to
   `main` once, at hour eleven. `main` stays clean so a broken merge cannot take down everybody.
4. **Nobody edits a file they do not own.** Backend touches `models.py`, `serializers.py`, `api.py`,
   `views.py`, `queries.py`. Frontend touches `templates/` and `palshare.css`. If you need a change
   on the other side of the line, ask — a two-minute conversation beats a merge conflict in
   `views.py` at hour ten.
5. **QA starts at hour two, not hour eleven.** Every page already renders. Test the shell.

**CHECKPOINT 1** — the room can answer: which file is the contract, who owns it, what branch do PRs
target, and what happens to a template when a backend view replaces a `TemplateView`.

> **DOCS** — [Django project structure](https://docs.djangoproject.com/en/5.2/intro/reusable-apps/) ·
> [`TemplateView`](https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/#templateview)

\newpage

# Part 2 — Hour 1: the branch and the models

## 2.1 The integration branch

**Himanshu, once, out loud so everybody sees it:**

```bash
git switch main
git pull origin main
git switch -c palshare
git push -u origin palshare
```

**Everybody else:**

```bash
git fetch origin
git switch -c <first_name>/palshare-<feature> origin/palshare
```

**CHECKPOINT 2a** — every person can print their branch name and it starts with their first name.

## 2.2 The models

One person types this — Kaushal or Ranjan — and pushes it before anybody else starts, because
everything else in the project imports from it.

**TYPE** — `palshare/models.py`:

```python
from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Everything about a user that `auth.User` does not already hold.

    A OneToOne rather than a custom user model: swapping `AUTH_USER_MODEL`
    after the first migration is a rewrite, and this project is twelve hours
    old. `related_name="profile"` makes it `request.user.profile`.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="profile")
    bio = models.TextField(blank=True)
    # FileField, not ImageField: ImageField needs Pillow, and this project has
    # gone ten days without adding a dependency. The extension allowlist in
    # `validate_upload` is the validation ImageField would have given us, and
    # it is validation the person who wrote it understands.
    avatar = models.FileField(upload_to="avatars/", blank=True, null=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="posts")
    text = models.TextField()
    followers_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Counter caches. A feed of 20 posts that counts likes per row is 21
    # queries; this is one. Kept honest by updating them in the like/save
    # endpoints, never by hand.
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author}: {self.text[:40]}"


class Media(models.Model):
    KIND = [("image", "Image"), ("video", "Video")]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="posts/%Y/%m/")
    kind = models.CharField(max_length=5, choices=KIND, default="image")
    alt = models.CharField(max_length=200, blank=True)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="comments")
    # One level of replies, and the model says so: a reply cannot have replies
    # because nothing enforces it here except the serializer refusing.
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                               related_name="replies")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # The database enforces "one like per person per post". Checking in
        # Python instead loses the race between two taps on a slow connection.
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_like_per_user")]


class Save(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="saves")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "post"], name="one_save_per_user")]


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name="following")
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="one_follow_per_pair"),
            # Nobody follows themselves. Cheaper here than in every view that
            # creates a Follow.
            models.CheckConstraint(condition=~models.Q(follower=models.F("following")),
                                   name="no_self_follow"),
        ]


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="sent_messages")
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sent_at"]
```

**TYPE**

```bash
mkdir -p palshare/migrations && touch palshare/migrations/__init__.py
python manage.py makemigrations palshare
python manage.py migrate
```

**EXPECT**

```
Migrations for 'palshare':
  palshare/migrations/0001_initial.py
    + Create model Conversation
    + Create model Message
    + Create model Post
    + Create model Media
    + Create model Comment
    + Create model Profile
    + Create model Follow
    + Create model Like
    + Create model Save
```

## 2.3 The three decisions in that file worth arguing about

**Likes are a model, not a `ManyToManyField`.** `Post.liked_by = M2M(User)` would work, and then the
day somebody asks "when did they like it" the answer is a migration. A join model with a
`created_at` costs nothing now and answers that question for free.

**The uniqueness lives in the database.** `UniqueConstraint`, not `if not Like.objects.filter(...)`.
The Python check has a gap between the read and the write, and on a phone with two bars, a double
tap lands in that gap. The database has no gap.

**`like_count` is stored, not counted.** It is a cache and caches go stale — so exactly two
endpoints are allowed to write it, and they do it with `F()`-style updates in Part 4. If it drifts,
one management command recomputes it. The alternative is `COUNT(*)` per row per page, forever.

**CHECKPOINT 2b** — `python manage.py migrate` is clean on every machine, and `python manage.py
shell -c "from palshare.models import Post; print(Post.objects.count())"` prints `0` for everybody.

> **DOCS** — [Model field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/) ·
> [Constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) ·
> [Many-to-many with a through model](https://docs.djangoproject.com/en/5.2/topics/db/models/#extra-fields-on-many-to-many-relationships)

\newpage

# Part 3 — The serializers, and why the page uses them too

The templates read `post.author.name`, `post.likes`, `post.liked`, `post.age`. The model has
`post.author.first_name`, `post.like_count`, no `liked` at all, and a `created_at` that is a
timestamp rather than a phrase.

Something has to close that gap. **The serializer is that something, for both the API and the
page.**

**TYPE** — `palshare/serializers.py`:

```python
class AuthorSerializer(serializers.ModelSerializer):
    """A user as a byline: the three fields a post card actually shows.

    Deliberately smaller than PersonSerializer. Nesting the big one inside a
    post costs two extra queries per row for follower counts nobody is looking
    at — twenty of them on a ten-post page.
    """

    name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "name"]
```

```python
class PostSerializer(serializers.ModelSerializer):
    """Matches `post` in demo.py — the contract the templates already read."""

    author = AuthorSerializer(read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    likes = serializers.IntegerField(source="like_count", read_only=True)
    comments = serializers.IntegerField(source="comment_count", read_only=True)
    # Read straight off the annotations the viewset adds. A
    # SerializerMethodField that queries is a query per row, and a feed is
    # nothing but rows.
    liked = serializers.BooleanField(read_only=True, default=False)
    saved = serializers.BooleanField(read_only=True, default=False)
    # `created_at` is a timestamp for machines; `age` is a string for people.
    # One name for both is how a UI ends up printing an ISO 8601 string at a
    # human.
    age = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "author", "text", "media", "followers_only",
                  "likes", "comments", "liked", "saved", "age", "created_at", "updated_at"]
        # Everything the server owns. `author` is not in this list because it
        # is not in `fields` as a writable field at all — it is nested and
        # read-only, and the view sets it from the credential.
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_age(self, post):
        return f"{timesince(post.created_at)} ago"
```

with `from django.utils.timesince import timesince` at the top.

**WHY replies are refused in the serializer, not the model** — `Comment.parent` allows any depth,
because a `CheckConstraint` cannot walk a tree. So the rule lives where it can be enforced:

```python
    def validate_parent(self, parent):
        """Replies go one level deep. The model allows more; we do not."""
        if parent and parent.parent_id is not None:
            raise serializers.ValidationError("Reply to the comment, not to a reply.")
        return parent
```

**CHECKPOINT 3** — the room can point at the four fields whose names differ between the model and
the contract, and say which side each one is renamed on.

> **DOCS** — [Serializer fields](https://www.django-rest-framework.org/api-guide/fields/) ·
> [`SerializerMethodField`](https://www.django-rest-framework.org/api-guide/fields/#serializermethodfield) ·
> [`timesince`](https://docs.djangoproject.com/en/5.2/ref/utils/#django.utils.timesince.timesince)

\newpage

# Part 4 — One rule, two consumers

Day 10 ended with a confession: the visibility rule was written twice, once in
`BlogViewSet.get_queryset()` and once in a plain function view, because a DRF permission class
protects a DRF view and nothing else. Two copies of a security rule is one copy too many.

Fix it here, on day one of the project.

**TYPE** — `palshare/queries.py`:

```python
"""Visibility rules, written once.

Day 10 ended with the same rule written twice — once in a DRF `get_queryset`
and once in a plain view — because a permission class protects a DRF view and
nothing else. This module is the fix: both consumers import from here, so
"what may this person see" has exactly one definition.
"""

from django.db.models import Exists, OuterRef, Q

from .models import Follow, Like, Post, Save


def visible_posts(user):
    """Posts `user` may see: their own, everything public, and followers-only
    posts by people they follow."""
    followed = Follow.objects.filter(follower=user).values("following")
    return (
        Post.objects
        .select_related("author")
        .prefetch_related("media")
        .annotate(
            liked=Exists(Like.objects.filter(user=user, post=OuterRef("pk"))),
            saved=Exists(Save.objects.filter(user=user, post=OuterRef("pk"))),
        )
        .filter(Q(author=user) | Q(followers_only=False) | Q(author__in=followed))
    )
```

## 4.1 The API side

**TYPE** — `palshare/permissions.py`:

```python
class IsAuthorOrReadOnly(permissions.BasePermission):
    """Day 10's rule, applied to every object in this app.

    Authentication says who you are; this says which rows you may change.
    Anything else is Broken Object Level Authorization, which is number one on
    the OWASP API list for a reason.
    """

    message = "You can only change things you created."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id is not None and obj.author_id == request.user.id
```

**TYPE** — `palshare/api.py`:

```python
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        return visible_posts(self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        """Idempotent on purpose: liking twice is a no-op, not a 400.

        Double taps happen on every slow connection there has ever been.
        """
        post = self.get_object()
        try:
            Like.objects.create(user=request.user, post=post)
            Post.objects.filter(pk=post.pk).update(like_count=post.like_count + 1)
        except IntegrityError:
            pass  # the unique constraint did its job
        return Response({"liked": True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def unlike(self, request, pk=None):
        post = self.get_object()
        deleted, _ = Like.objects.filter(user=request.user, post=post).delete()
        if deleted:
            Post.objects.filter(pk=post.pk).update(like_count=max(post.like_count - 1, 0))
        return Response({"liked": False}, status=status.HTTP_200_OK)
```

**TYPE** — `palshare/api_urls.py`, and one line in `config/urls.py`:

```python
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import PostViewSet

app_name = "palshare-api"

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")

urlpatterns = [path("", include(router.urls))]
```

```python
    path("api/palshare/", include("palshare.api_urls")),
```

## 4.2 Prove it

**TYPE** — with two accounts, `asha` and `bello`:

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from palshare.models import Profile
for u in ['asha', 'bello']:
    user = User.objects.create_user(u, password='lab-passphrase-2026', first_name=u.title())
    Profile.objects.create(user=user, bio='workshop')
print('two accounts')
"
```

Then, as asha, post something while trying to post it as bello:

**EXPECT** — five results, and every one of them is Day 10 doing its job:

```
=== anonymous ===
  GET /api/palshare/posts/ -> 401

=== create (trying to post as bello) ===
  status: 201 | author in response: asha

=== like is idempotent ===
  like #1: 200 | like_count = 1
  like #2: 200 | like_count = 1
  like #3: 200 | like_count = 1

=== bello cannot edit asha's post ===
  PATCH -> 403 You can only change things you created.

=== followers-only post is invisible until you follow ===
  bello sees: ['Hour four and the feed is li']
  after follow: ['Just for my followers', 'Hour four and the feed is li']
```

## 4.3 The HTML side, and the moment it all pays off

**TYPE** — `palshare/views.py`:

```python
@login_required
def feed(request):
    posts = visible_posts(request.user)[:20]
    return render(request, "palshare/feed.html", {
        "posts": PostSerializer(posts, many=True, context={"request": request}).data,
        "current_user": {"username": request.user.username,
                         "name": request.user.get_full_name() or request.user.username,
                         "avatar": request.user.username[:1].upper()},
        "active": "feed",
    })
```

**TYPE** — and in `palshare/urls.py`, change one line:

```python
    # Swapped for a real view. Same URL, same name, same template.
    path("", views.feed, name="feed"),
```

**EXPECT** — reload <http://127.0.0.1:8000/palshare/>. Real posts, from the database, in the
template Suraj wrote in hour one, **with no edit to any template**:

```
  status: 200 | queries: 4
  template leaks: none
  post cards on the page: 20

=== a card, as rendered from the database ===
  Asha R @asha · 1 minute ago ⋯ post 19 ♥ 0 💬 0 ↻ ☆
```

**WHY the page uses the serializer** — because then the page and the API cannot disagree. One shape,
defined once, consumed twice. The usual alternative is to pass the queryset to the template and let
it call model attributes, which works fine until the API adds a field the page needs and now there
are two definitions of what a post is.

**CHECKPOINT 4** — the feed renders real posts, and `git diff` shows **zero changes** under
`templates/`.

> **DOCS** — [`Exists` subqueries](https://docs.djangoproject.com/en/5.2/ref/models/expressions/#exists-subqueries) ·
> [DRF `@action`](https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing) ·
> [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/)

\newpage

# Part 5 — The N+1, found and fixed in the same hour

The feed above ran in **4 queries**. The first version of it ran in **43**, and the difference is
worth the ten minutes it takes to see it.

## 5.1 Measure first

**TYPE**

```bash
python manage.py shell -c "
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from rest_framework.test import APIClient
settings.DEBUG = True
c = APIClient(); c.force_authenticate(user=User.objects.get(username='bello'))
reset_queries()
r = c.get('/api/palshare/posts/')
print(len(r.data['results']), 'rows in', len(connection.queries), 'queries')
"
```

**EXPECT** — before the fix:

```
10 rows in 43 queries
```

Ten rows. Forty-three queries. Nobody wrote a loop.

## 5.2 Where they came from

| Cause | Cost |
| --- | --- |
| `liked = SerializerMethodField()` doing `post.likes.filter(...)` | 1 query per row |
| `saved = SerializerMethodField()` doing `post.saves.filter(...)` | 1 query per row |
| `PersonSerializer.followers` = `source="followers.count"` | 1 query per row |
| `PersonSerializer.following` = `source="following.count"` | 1 query per row |

Four per row, ten rows, plus the page itself. This is the **N+1 problem**, and it does not look like
a loop — it looks like four perfectly reasonable serializer fields.

## 5.3 The two fixes

**Move per-viewer facts into the queryset.** `Exists()` computes `liked` and `saved` for the whole
page in the one query that fetches it, which is what `annotate()` in `visible_posts()` is doing.

**Stop nesting the big serializer.** A post card shows a name and a username. It does not show
follower counts, so `AuthorSerializer` exists and `PersonSerializer` stays on the profile endpoint
where those numbers are actually on screen.

**EXPECT** — after:

```
10 rows in 3 queries
```

**WHY this matters at eleven people rather than at scale** — nobody in this room has enough data for
43 queries to feel slow. The demo machine will not notice. It is worth fixing anyway, because the
habit of measuring is the deliverable, and because `assertNumQueries` is the only test that catches
a serializer field somebody adds at hour nine.

**CHECKPOINT 5** — somebody has run the query count before and after and said the two numbers out
loud.

> **DOCS** — [`select_related` / `prefetch_related`](https://docs.djangoproject.com/en/5.2/topics/db/optimization/#retrieve-everything-at-once-if-you-know-you-will-need-it) ·
> [`assertNumQueries`](https://docs.djangoproject.com/en/5.2/topics/testing/tools/#django.test.TransactionTestCase.assertNumQueries) ·
> [Database access optimization](https://docs.djangoproject.com/en/5.2/topics/db/optimization/)

\newpage

# Part 6 — Media, and the four ways an upload hurts you

Feature 2 says "text, images & media". An upload is the only place in this app where a stranger
puts a **file** on your server, so it gets its own part.

## 6.1 Settings

**TYPE** — `config/settings.py`:

```python
# Where uploads land, and the URL they are served from. MEDIA_ROOT is a
# directory on disk that must not be inside STATIC_ROOT and must not be in git.
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"
```

**TYPE** — `config/urls.py`, at the bottom:

```python
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    # Development only. In production a real web server serves these, because
    # Django serving user files is slow and puts your app in the path of every
    # image request.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**TYPE** — and `.gitignore` already has `media/`. Check it:

```bash
git check-ignore -v media/
```

## 6.2 The validator

**TYPE** — `palshare/validators.py`:

```python
from pathlib import Path

from django.core.exceptions import ValidationError

ALLOWED = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm"}
MAX_BYTES = 5 * 1024 * 1024


def validate_upload(f):
    """An allowlist and a size limit. Both are required; neither is enough.

    Note what is NOT checked: `f.content_type`. It is sent by the client, so it
    is a claim, not a fact — a .php file arrives quite happily labelled
    image/png. The extension is at least the thing the filesystem will use.
    """
    if f.size > MAX_BYTES:
        raise ValidationError(f"Files must be under {MAX_BYTES // 1024 // 1024} MB.")
    if Path(f.name).suffix.lower() not in ALLOWED:
        raise ValidationError(f"{Path(f.name).suffix or 'That'} files are not allowed.")
```

Then on the model field: `file = models.FileField(upload_to="posts/%Y/%m/", validators=[validate_upload])`.

**EXPECT** — three uploads, all three claiming `Content-Type: image/png`:

```
  holiday.jpg    accepted
  shell.php      refused: .php files are not allowed.
  movie.mp4      refused: Files must be under 5 MB.
```

## 6.3 The four ways this hurts you

| Attack | What stops it |
| --- | --- |
| Upload a 4 GB file and fill the disk | `MAX_BYTES`, plus a limit in the web server in front of Django |
| Upload `shell.php` and request it back | The extension allowlist, and never serving `MEDIA_ROOT` through anything that executes |
| Upload `../../config/settings.py` as a filename | Django's `get_valid_filename` — but do not rely on it alone; `upload_to` with a date pattern keeps everything under one tree |
| Upload an image that is a giant HTML page and get it rendered as your domain | Serve user media from a separate domain in production, so a stored XSS cannot read your cookies |

**WHY the content type is not checked** — because the browser supplies it. Checking it feels like
validation and is closer to reading the attacker's own description of their file.

**CHECKPOINT 6** — a post with an image renders on the feed, and uploading a `.txt` file is refused
with a message a human can read.

> **DOCS** — [Managing files](https://docs.djangoproject.com/en/5.2/topics/files/) ·
> [File uploads](https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/) ·
> [User-uploaded content security](https://docs.djangoproject.com/en/5.2/topics/security/#user-uploaded-content)

\newpage

# Part 7 — Follow, like, save: the same shape three times

Features 4, 5 and 7 are one idea — a row that either exists or does not — and they share three
rules.

**Idempotent.** `POST .../like/` twice is not an error. The second one is a no-op that returns the
same `200`, because the network duplicated the request or the user double-tapped, and neither of
those is a mistake the user should hear about.

**Enforced by the database.** `UniqueConstraint`, caught as `IntegrityError`. Never
`if not exists(): create()` — there is a gap between those two statements and a phone on 3G will
find it.

**Reflected in the same response.** The endpoint returns the new state (`{"liked": true}`), so the
UI never has to guess or re-fetch.

**TYPE** — the follow endpoints, in `palshare/api.py`. Note `lookup_field = "username"`: a
profile URL says `/u/kaushal/`, not `/u/7/`.

```python
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.select_related("profile")
    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    @action(detail=True, methods=["post"])
    def follow(self, request, username=None):
        target = self.get_object()
        if target == request.user:
            # The CheckConstraint would also stop this, with a 500. A 400 with
            # a sentence is the version a person can act on.
            return Response({"detail": "You cannot follow yourself."},
                            status=status.HTTP_400_BAD_REQUEST)
        Follow.objects.get_or_create(follower=request.user, following=target)
        return Response({"following": True})

    @action(detail=True, methods=["post"])
    def unfollow(self, request, username=None):
        Follow.objects.filter(follower=request.user, following=self.get_object()).delete()
        return Response({"following": False})
```

and register it next to the posts route:

```python
router.register("users", UserViewSet, basename="user")
```

**EXPECT**

```
=== follow is idempotent ===
  POST #1: 200 {'following': True} | rows: 1
  POST #2: 200 {'following': True} | rows: 1
  POST #3: 200 {'following': True} | rows: 1

=== you cannot follow yourself ===
  400 {'detail': 'You cannot follow yourself.'}

=== unfollow ===
  200 {'following': False} | rows: 0
```

**EXPECT** — and with the view's check removed, the database still refuses:

```
  IntegrityError: CHECK constraint failed: no_self_follow
```

**WHY both the constraint and the check** — the constraint is the guarantee and the check is the
error message. A database constraint firing is a `500`; a view that checks first turns it into a
`400` with a sentence. You want both: the check for the ninety-nine per cent, the constraint for the
race the check cannot see.

## 7.1 Private profiles

Feature 8. The rule, once, in `queries.py` next to `visible_posts`:

```python
def may_see_posts(viewer, owner):
    """A private account shows its posts to itself and its followers, nobody else."""
    if viewer == owner:
        return True
    if not owner.profile.is_private:
        return True
    return Follow.objects.filter(follower=viewer, following=owner).exists()
```

**EXPECT**

```
  asha sees her own:      True
  bello, not a follower:  False
  bello, now a follower:  True
```

`profile.html` already renders both outcomes — the header always, the posts only when allowed. Look
at the `{% if %}` in it before you write the view; the UI has been waiting for this function since
hour one.

**CHECKPOINT 7** — bello follows asha, sees her followers-only posts, unfollows, stops seeing them.
Bello cannot follow bello.

\newpage

# Part 8 — Messaging

Feature 6, and the only feature with a model shape worth thinking about.

A conversation is between two people, and "open the conversation with bello" must return the same
conversation every time — not a new one per message.

**TYPE** — `palshare/queries.py`:

```python
def conversation_with(me, other):
    """The one conversation between two people, created on first message.

    Two `filter()` calls, not one with two participants: a single filter on a
    ManyToMany matches rows with *either* participant. Chaining them means
    "has me AND has other".
    """
    existing = (Conversation.objects
                .filter(participants=me)
                .filter(participants=other)
                .first())
    if existing:
        return existing
    conversation = Conversation.objects.create()
    conversation.participants.add(me, other)
    return conversation
```

**EXPECT** — open it from both sides and there is still one row:

```
  same both ways: True | conversations in the table: 1
```

**WHY two `.filter()` calls** — `filter(participants__in=[me, other])` returns every conversation
that has *either* person in it, which is every conversation you have ever had. Chaining two filters
across a many-to-many is the documented way to require both, and it is the single most common
many-to-many bug there is.

Three things the templates already expect and the backend must supply:

- **`mine` comes from the server.** `thread.html` says so in its own comment: working it out in the
  template by comparing usernames breaks the day somebody changes their display name.
- **`unread` is a count, per conversation**, for the badge in `inbox.html`.
- **Conversations are ordered by `updated_at`**, newest first, which the model's `Meta.ordering`
  already does — as long as sending a message touches the conversation.

**CHECKPOINT 8** — two browsers, two accounts, one conversation. Sending from either side lands in
the other's inbox with a badge, and neither side sees a duplicate thread.

\newpage

# Part 9 — Search

Feature 9. The smallest feature in the project and the one most likely to be over-built.

```python
def search(user, q):
    q = q.strip()
    if len(q) < 2:
        # Two characters is not a search, it is a table scan. The page has an
        # empty state for exactly this.
        return {"query": q, "people": [], "posts": []}
    return {
        "query": q,
        "people": User.objects.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q)
        )[:10],
        # `visible_posts`, not `Post.objects`: search is the classic way private
        # data leaks, because the detail page checks permissions and the search
        # does not.
        "posts": visible_posts(user).filter(text__icontains=q)[:20],
    }
```

It takes a `user` and a string rather than a `request`, so the API view and the page view can both
call it — the Part 4 rule, applied again.

**EXPECT**

```
  q='dj' -> 1 posts, 0 people
  q='a'  -> {'query': 'a', 'people': [], 'posts': []}
```

Three notes and then move on:

- **`icontains` is a `LIKE '%q%'`** — no index will help it, and on SQLite with a workshop's worth of
  rows that is completely fine. Postgres full-text search is Appendix E, not today.
- **The search box cannot be injected.** The ORM parameterises the query; `q` never becomes SQL. This
  is worth saying out loud once, because it is the one place students expect to have to escape
  something.
- **Search results respect visibility** — note that it filters `visible_posts(request.user)`, not
  `Post.objects`. Search is the classic way private data leaks: the detail page checks permissions
  and the search index does not.

**CHECKPOINT 9** — a followers-only post by somebody you do not follow does **not** appear in your
search results, and does appear in theirs.

\newpage

# Part 10 — The two integrations

Features 10 and 11 have one thing in common that nothing else in this project has: **they depend on
a computer you do not control.** During your demo, at least one of them will be slow or down. Build
for that first and the happy path is free.

## 10.1 Keys

**TYPE** — `.env`, which is gitignored:

```bash
WEATHER_API_KEY=...
NVIDIA_API_KEY=...
```

**TYPE** — `config/settings.py`:

```python
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
```

Day 10 covered why this is not optional. A key pasted into `settings.py` is in git forever, and
`git log -p` finds it after you delete the line.

## 10.2 The shape every integration takes

**TYPE** — `palshare/integrations.py`:

```python
"""Calls to computers we do not control.

Written on the standard library so the project stays dependency-free. If you
prefer `requests`, `pip install requests`, add it to requirements.txt, and the
shape below is identical — `requests.get(url, timeout=3)` in place of the
urlopen call.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_TTL = 600  # ten minutes


def current_weather(city="Kathmandu"):
    """Never let a third party decide whether our page renders.

    Three defences, and all three are load-bearing:
      * a cache, so one slow call is not one slow call per visitor
      * a timeout, because the default is "wait until the OS gives up"
      * an except that returns None, because the widget has an empty state and
        a 500 does not
    """
    key = f"weather:{city}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    if not settings.WEATHER_API_KEY:
        logger.warning("WEATHER_API_KEY is not set; the widget will show its empty state")
        return None

    query = urllib.parse.urlencode({"q": city, "appid": settings.WEATHER_API_KEY, "units": "metric"})
    try:
        with urllib.request.urlopen(f"{WEATHER_URL}?{query}", timeout=3) as response:
            payload = json.load(response)
        data = {
            "city": city,
            "temp_c": round(payload["main"]["temp"]),
            "summary": payload["weather"][0]["description"].title(),
            "icon": "⛅",
        }
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError):
        logger.exception("weather lookup failed for %s", city)
        return None

    cache.set(key, data, timeout=WEATHER_TTL)
    return data
```

**EXPECT** — before anyone has a key, which is most of hour nine:

```
WEATHER_API_KEY is not set; the widget will show its empty state
  current_weather() -> None
```

`None` is a supported answer, not a failure. `_widget_weather.html` renders "Weather is unavailable
right now" and the rest of the page is untouched.

**WHY `KeyError` and `ValueError` are in that except clause** — a third-party API changing its JSON
shape is more likely than it going down, and `payload["main"]["temp"]` on a changed response is a
`KeyError` at hour ten in front of the room. Catch the parse, not just the network.

| Defence | Without it |
| --- | --- |
| `timeout=3` on `urlopen` | One hung TCP connection holds a worker until the OS gives up. Ten of those is the site down |
| `cache.set(..., WEATHER_TTL)` | Every page view is an API call. Free tiers are measured in calls per day |
| `except` → `None` | The weather API's bad afternoon is your bad afternoon, on every page |
| `logger.exception` | You find out from the room, not from the logs |

`_widget_weather.html` and `assistant.html` already render the `None` case. Go and look at them —
the empty states were written before the integrations existed, which is the point.

## 10.3 The AI call specifically

The NVIDIA API is slower than the weather one — seconds, not milliseconds. Two consequences:

1. **It cannot be in the request that renders a page.** The assistant is its own page and its own
   `POST`, so a slow model makes the assistant slow, not the feed.
2. **`assistant.html` has a `pending` state.** Use it.

And the rule that outlives this workshop: **never send a user's private data to a third-party model
without saying so.** Post text that a user marked followers-only is not yours to forward.

**CHECKPOINT 10** — turn your wifi off. The feed still renders, the weather widget shows its empty
state, the assistant says it is unavailable. Nothing 500s.

> **DOCS** — [Django cache framework](https://docs.djangoproject.com/en/5.2/topics/cache/) ·
> [Logging](https://docs.djangoproject.com/en/5.2/topics/logging/) ·
> [`requests` timeouts](https://requests.readthedocs.io/en/latest/user/advanced/#timeouts)

\newpage

# Part 11 — Hour 11: the integration hour

Eleven branches become one app. Budget a full hour and run it in this order.

## 11.1 The migration collision

It will happen. Two people added a migration off the same parent:

**EXPECT**

```
CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph:
(0002_kaushal, 0002_ranjan in palshare).
To fix them run 'python manage.py makemigrations --merge'
```

**TYPE**

```bash
python manage.py makemigrations --merge
```

**EXPECT**

```
Merging palshare
  Branch 0002_kaushal
    + Add field pinned to post
  Branch 0002_ranjan
    + Add field edited to post

Created new merge migration palshare/migrations/0003_merge_0002_kaushal_0002_ranjan.py
```

```bash
python manage.py migrate
```

```
Running migrations:
  Applying palshare.0002_ranjan... OK
  Applying palshare.0002_kaushal... OK
  Applying palshare.0003_merge_0002_kaushal_0002_ranjan... OK
```

**WHY this is not a conflict to be afraid of** — the two migrations touch different columns, so the
merge is a bookkeeping file with no operations in it. It is only frightening when both edited the
same field, and that is a conversation, not a command.

## 11.2 The order

1. **Models first.** Whoever owns `models.py` merges to `palshare`, everybody else rebases.
2. **Then serializers and queries** — everything imports them.
3. **Then endpoints**, one PR at a time, `migrate` after each.
4. **Then the view swaps** — the `TemplateView` → real view lines, which touch only `urls.py`.
5. **Then templates**, which by now should be conflict-free because only one person edits them.
6. **Integrations last.** They depend on nothing and nothing depends on them, so a failure here
   costs the least.

After each merge: `python manage.py check && python manage.py test`. A red build blocks the next
merge — that is the lead's call and it is not negotiable at hour eleven.

## 11.3 Seed data for the demo

An empty app demos badly. One command, run on the demo machine:

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from palshare.models import Post, Profile, Follow
...
"
```

Write it as a management command if there is time, `palshare/management/commands/seed_palshare.py`,
idempotent via `get_or_create`. Do not use a fixture with hardcoded primary keys — they differ on
every machine, and the demo machine is the one that matters.

**CHECKPOINT 11** — `palshare` branch: `check` clean, `test` green, `migrate` clean from an empty
database, and every one of the fifteen pages loads.

\newpage

# Part 12 — QA and the demo

## 12.1 The per-page checklist

QA runs this against every page. It is six lines and it finds more than an hour of clicking.

| Check | Why |
| --- | --- |
| **Empty state** — delete all the rows, load the page | The state every new user starts in |
| **Long text** — a 500-character post, a 40-character username | Layouts break at the edges, not in the middle |
| **375px wide** | More than half of real traffic, and the only width that finds overflow |
| **Not logged in** | Should redirect or refuse — never a `500`, never somebody else's data |
| **Somebody else's row** — put another user's id in the URL | The Day 10 lesson, applied to every new endpoint |
| **Third party off** — kill the wifi | The weather and AI widgets must degrade, not crash |

## 12.2 Bug reports that get fixed

Three lines, always:

```
WHERE   /palshare/u/kaushal/ as bidhya
WHAT    Followers-only posts are visible to a non-follower
EXPECT  Only the profile header, as the private-account empty state
```

No screenshots of the whole screen, no "it's broken". A URL, an account, and the expected state.

## 12.3 The demo, hour 12

Eight minutes, one narrative, one person driving. Rehearse it once.

1. **Register** as a new person. Log in.
2. **Post** something with an image.
3. **Follow** somebody, and watch their posts arrive in the feed.
4. **Like**, **comment**, **reply**, **save**.
5. **Search** for a person, open their **profile**, flip it to private and reload it as somebody else.
6. **Message** them; show the badge in the other browser.
7. **Weather widget** and the **assistant**.
8. Finish on `python manage.py check --deploy` — clean under a production environment.

Two rules: **two browsers, side by side** — half of these features only make sense with two accounts
— and **whatever breaks, keep going**. The room remembers the recovery, not the bug.

**CHECKPOINT 12** — the demo has been run end to end at least once before anybody watches it.

\newpage

# Appendix A — Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `no such column: palshare_post.pinned` | Somebody's migration is not on your branch | `git pull`, then `python manage.py migrate` |
| `Conflicting migrations detected` | Two branches added a migration off one parent | `python manage.py makemigrations --merge` (Part 11.1) |
| `NOT NULL constraint failed: palshare_post.author_id` | A view saved without `author=request.user` | `perform_create`, or `form.save(commit=False)` on the HTML side |
| `RelatedObjectDoesNotExist: User has no profile` | The user was made before `Profile` existed, or by `createsuperuser` | Create profiles in a signal or a data migration; guard with `getattr(user, "profile", None)` |
| `Cannot use ImageField because Pillow is not installed` | `ImageField` needs Pillow | Use `FileField` (Part 2.2), or `pip install Pillow` and add it to `requirements.txt` |
| A page shows every conversation you have ever had | `filter(participants__in=[a, b])` | Two chained `.filter()` calls (Part 8) |
| `is_private` was set but `may_see_posts` still says yes | `user.profile` is cached on the instance; `user.refresh_from_db()` does not refresh a related object | Re-fetch the user: `User.objects.get(pk=user.pk)`. This bit the person writing this guide |
| The feed is slow and nobody wrote a loop | Serializer fields querying per row | `annotate()` with `Exists`, and a smaller nested serializer (Part 5) |
| `403` on every write with a valid token | Day 10's global default is `IsAuthenticated`; the object permission is refusing | You are not the author of that row. That is the feature |
| `429 Too Many Requests` while testing | Day 10's throttles: `5/min` on login, `30/min` on a detail page | Wait a minute, or restart the server to clear the local-memory cache |
| Uploaded images 404 | `MEDIA_URL` not wired in `config/urls.py` | The `if settings.DEBUG:` block in Part 6.1 |
| `{{ post.age }}` renders empty | Context is model instances, not serialized data | `PostSerializer(qs, many=True, context={"request": request}).data` |
| A template prints `{{ something }}` literally | A `{# #}` comment spread over two lines | `{% comment %}` — single-line only is the rule |
| Everybody's `git status` shows `db.sqlite3` | Somebody committed it | It is gitignored; `git rm --cached db.sqlite3` |

\newpage

# Appendix B — Official documentation index

**Django 5.2**

* [Models](https://docs.djangoproject.com/en/5.2/topics/db/models/) ·
  [field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/) ·
  [constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/)
* [Queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/) ·
  [`Q` objects](https://docs.djangoproject.com/en/5.2/topics/db/queries/#complex-lookups-with-q-objects) ·
  [expressions](https://docs.djangoproject.com/en/5.2/ref/models/expressions/)
* [Database optimization](https://docs.djangoproject.com/en/5.2/topics/db/optimization/)
* [Migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/) — read the section on
  merging before hour eleven
* [File uploads](https://docs.djangoproject.com/en/5.2/topics/http/file-uploads/) ·
  [managing files](https://docs.djangoproject.com/en/5.2/topics/files/)
* [Templates](https://docs.djangoproject.com/en/5.2/topics/templates/) ·
  [built-in tags and filters](https://docs.djangoproject.com/en/5.2/ref/templates/builtins/)
* [Cache framework](https://docs.djangoproject.com/en/5.2/topics/cache/) ·
  [logging](https://docs.djangoproject.com/en/5.2/topics/logging/)
* [Security overview](https://docs.djangoproject.com/en/5.2/topics/security/) — everything Day 10
  covered, in one page

**Django REST Framework 3.18**

* [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/) ·
  [routers](https://www.django-rest-framework.org/api-guide/routers/) ·
  [`@action`](https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing)
* [Serializers](https://www.django-rest-framework.org/api-guide/serializers/) ·
  [fields](https://www.django-rest-framework.org/api-guide/fields/) ·
  [relations](https://www.django-rest-framework.org/api-guide/relations/)
* [Permissions](https://www.django-rest-framework.org/api-guide/permissions/) ·
  [throttling](https://www.django-rest-framework.org/api-guide/throttling/) ·
  [pagination](https://www.django-rest-framework.org/api-guide/pagination/)

**The rest**

* [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)
* [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
* [`requests`](https://requests.readthedocs.io/en/latest/) — read the timeouts page, not the quickstart

**This repository**

* `guides/README-day1.md` … `README-day10.md` — the ten days this project stands on
* `guides/README-day10.md` — API security. Every endpoint you write today is bound by it
* `palshare/demo.py` — the contract

\newpage

# Appendix C — Command cheat sheet

```bash
# --- the team's git ------------------------------------------------------
git fetch origin
git switch -c <first_name>/palshare-<feature> origin/palshare   # start work
git add -A && git commit -m "feat(posts): add the like endpoint"
git push -u origin <first_name>/palshare-<feature>
gh pr create --base palshare                                     # never --base main

git switch palshare && git pull                                  # before you rebase
git switch <first_name>/palshare-<feature> && git rebase palshare

# --- migrations ----------------------------------------------------------
python manage.py makemigrations palshare
python manage.py sqlmigrate palshare 0001        # read the SQL before running it
python manage.py migrate
python manage.py makemigrations --merge          # the integration-hour fix
python manage.py showmigrations palshare

# --- the checks the lead runs before every merge -------------------------
python manage.py check
python manage.py check --deploy
python manage.py test

# --- counting queries ----------------------------------------------------
python manage.py shell -c "
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from rest_framework.test import APIClient
settings.DEBUG = True
c = APIClient(); c.force_authenticate(user=User.objects.first())
reset_queries()
r = c.get('/api/palshare/posts/')
print(len(r.data['results']), 'rows in', len(connection.queries), 'queries')
"

# --- exercising the API --------------------------------------------------
TOK=$(curl -s -X POST http://127.0.0.1:8000/accounts/login/ \
      -H "Content-Type: application/json" \
      -d '{"username":"asha","password":"lab-passphrase-2026"}' \
      | python -c "import json,sys; print(json.load(sys.stdin)['access'])")

curl -s http://127.0.0.1:8000/api/palshare/posts/ -H "Authorization: Bearer $TOK" | python -m json.tool
curl -s -X POST http://127.0.0.1:8000/api/palshare/posts/ -H "Authorization: Bearer $TOK" \
     -H "Content-Type: application/json" -d '{"text":"Hello PalShare"}'
curl -s -X POST http://127.0.0.1:8000/api/palshare/posts/1/like/ -H "Authorization: Bearer $TOK"

# --- the four refusals, per Day 10 --------------------------------------
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/palshare/posts/   # 401
```

\newpage

# Appendix D — Trainer notes

## D.1 How to open the day

Do **not** start with the models. Start with the shell: put
<http://127.0.0.1:8000/palshare/> on the projector, click through all fifteen pages, and let the
room believe the app is finished. Then open `palshare/` and show them there is no `models.py`.

That thirty seconds does more for "why contracts matter" than any explanation.

## D.2 The hour-by-hour, mapped to the project plan

| Hour | Plan says | What actually has to happen | Who is blocked |
| --- | --- | --- | --- |
| 1 | Setup, requirements, DB/API structure | Integration branch, `models.py`, migration pushed | everybody, until the migration lands |
| 2–4 | Auth, profiles, UI foundation | Serializers, `queries.py`, auth wiring, profile page | nobody, if hour 1 finished |
| 4–7 | Posts, feed, media, likes, comments | `PostViewSet`, actions, uploads, the first view swap | QA can start here |
| 7–9 | Follow, saved, search, inbox | Three endpoints of the same shape, then messaging | messaging blocks nothing else |
| 9–10 | Weather + NVIDIA | Failure states first, happy path second | keys must exist by hour 8 |
| 10–11 | Integration & bug fixing | Merge in the order in Part 11.2 | everybody |
| 12 | Final testing, demo | Rehearse once, then perform | — |

**If you are behind at hour 9, cut in this order:** the assistant page, then saved posts, then
search, then replies-to-comments. Do not cut the empty states and do not cut the demo rehearsal.

## D.3 Things that reliably go wrong

| At about | What | The fix, ready in advance |
| --- | --- | --- |
| hour 1 | Somebody starts before the migration is pushed | Nobody types until the lead says the model is on `palshare` |
| hour 3 | Two people editing `views.py` | Part 1 rule 4. Say it again |
| hour 5 | "The template doesn't show my field" | The context is model instances, not serialized data |
| hour 6 | Uploads 404 | `MEDIA_URL` block in `config/urls.py` |
| hour 8 | Everything 429s | Day 10's throttles. Restart the server |
| hour 10 | Migration conflict | Part 11.1, one command |
| hour 10 | The API key was committed | It is in git history. Rotate it — do not just delete the line |
| hour 11 | A red build blocks the merge queue | The lead reverts the PR, the author fixes it on their branch |

## D.4 Marking it

If the project is assessed, weight it like this — and say so at hour one:

| Weight | What |
| --- | --- |
| 30% | It runs from a clean clone: `migrate`, `runserver`, register, post, see the post |
| 25% | Authorisation: no endpoint lets one account touch another's data (Day 10 applied) |
| 20% | The contract held: `git log` shows templates were not rewritten to fit the backend |
| 15% | Graceful failure: empty states, third-party APIs off, 375px wide |
| 10% | Git hygiene: one feature per branch, reviewed PRs, no secrets, no `db.sqlite3` |

Note what is not on that list: how many of the eleven features are finished. A team that ships six
solid features beats a team that ships eleven broken ones, and the marking should say so before they
start, not after.

## D.5 The line to repeat all day

> The backend does not decide what the page needs. The page already decided. Read `demo.py`.

\newpage

# Appendix E — Beyond the twelve hours

Where this app is thin, in the order it will hurt.

**Correctness**
* **Notifications.** Likes, comments and follows all want one. A `Notification` model and a signal
  per event, then the badge in the header.
* **`Profile` creation.** Right now nothing guarantees a user has one. A `post_save` signal on
  `User`, plus a data migration for the users who already exist.
* **Counter drift.** `like_count` will disagree with `Like.objects.count()` eventually. A management
  command that recomputes it, run nightly, is twenty lines.

**Scale**
* **Real search.** Postgres `SearchVector` and a GIN index, instead of `icontains`.
* **The feed query.** Fine for a workshop. At ten thousand follows it wants a fan-out-on-write
  design, which is a different guide.
* **Media.** Object storage (`django-storages` + S3) rather than local disk, and a separate domain
  so stored XSS cannot read your cookies.
* **A shared cache.** Day 10's throttles and Part 10's weather cache are both local-memory, which
  means per-process. Redis, the moment there is more than one worker.

**Real-time**
* The inbox is a page you reload. Django Channels and a WebSocket make it a chat — and turn the
  deployment from one process into two.

**Operations**
* Deployment: `DEBUG=0`, a real `SECRET_KEY`, `collectstatic`, gunicorn behind nginx. Day 10's
  `check --deploy` is the checklist.
* `pip-audit` and Dependabot. Most breaches are an unpatched dependency.
* Structured logging on every `403` — a spike is somebody probing you.

**The one to do first**

Tests. There are none in this guide, deliberately — twelve hours is not enough to teach a team to
test and ship at once. But the first commit after the workshop should be
`palshare/tests/test_permissions.py`, asserting the six refusals from Appendix C. Every feature
after that is one `assertNumQueries` and three status codes away from being safe to change.
