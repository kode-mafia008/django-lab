---
title: "Day 8 — ViewSets and Routers"
subtitle: "Collapsing one class per operation into one class per resource, and giving it a Blog model to serve"
author: "Django Practical Lab — daily guide series"
date: "Django 5.2 LTS · DRF 3.18 · Simple JWT 5.5 · drf-spectacular 0.30"
---

# What we did today

| # | Task | Command / change | Result |
| --- | --- | --- | --- |
| 1 | Counted the cost of one class per operation | — | Five classes and two colliding `path()`s per resource |
| 2 | Added a second model | `Blog` in `blog/models.py` | A `blogs` table with a foreign key |
| 3 | Made the migration | `makemigrations blog` | `0003_blog.py`, a clean `CreateModel` |
| 4 | Registered it in the admin | `blog/admin.py` | `Blog` rows editable at `/admin/` |
| 5 | Wrote a serializer | `BlogSerializer` in `blog/serializers.py` | Seven fields, three of them read-only |
| 6 | Wrote two viewsets | `BlogViewSet`, `AuthorViewSet` in `blog/views.py` | Six operations each, from three lines each |
| 7 | Generated the URLs | `DefaultRouter` in `blog/urls.py` | Ten routes from two `register()` calls |
| 8 | Retired `AuthorListView` | replaced by `AuthorViewSet` | Authors gain a detail route and `PUT`/`PATCH`/`DELETE` |
| 9 | Hit a name collision and fixed it | `basename='api-author'` | `blog:author-list` points at the page again |
| 10 | Walked it with `curl` | — | `401` → login → `201` → `PATCH` → `204` |

Everything below runs against this repository, starting from `main` at the end of Day 7 — a `blog`
app whose `Author` rows render as HTML pages *and* answer at `/blogs/api/authors`, plus the
`accounts` app and its JWT endpoints.

Today's scope is deliberately narrow: **one model, one serializer, one viewset, one router.** Several
things a real API wants — pagination, search, filtering, per-action permissions, custom actions,
annotated documentation, tests — are named where they become relevant and linked to their official
documentation in **Appendix E**. They are not built today. Read them there when you want more.

## Conventions

Same as Days 1–4.

| Marker | Meaning |
| --- | --- |
| **TYPE** | Type this exactly. |
| **EXPECT** | What should appear. If you see something else, stop and fix it. |
| **CHECKPOINT** | A verifiable state. Nobody moves on until everyone reaches it. |
| **WHY** | The reasoning. Read it before the exam. |
| **DOCS** | The official documentation for what you just did. |

Django links point at `/en/5.2/`, matching `requirements.txt`. Today adds no new package — everything
in it ships inside DRF already.

## Start here

**TYPE**

```bash
cd ~/code/django-lab
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
git switch main
git pull origin main
git switch -c <first_name>/day8
```

**TYPE**

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**EXPECT** — the server starts and <http://127.0.0.1:8000/blogs/> lists authors as HTML.

**CHECKPOINT 0** — you are on branch `<first_name>/day8`, `migrate` is clean, `/blogs/` renders, and:

```bash
python manage.py shell -c "from blog.models import Author; print(Author.objects.count())"
```

prints a number greater than zero. If it prints `0`, add two or three authors in `/admin/` first —
every blog post today needs an author to point at.

Stop the server with `Ctrl-C` before the next part.

\newpage

# Part 1 — Why one class per operation stops scaling

Open `blog/views.py`. Yesterday's API is one class:

```python
class AuthorListView(generics.ListCreateAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]
```

`ListCreateAPIView` is already two operations bolted together — list and create — because they share
the URL `/blogs/api/authors`. Now count what full CRUD costs in that style.

| You want | This style needs | At which URL |
| --- | --- | --- |
| `GET` the collection | `ListAPIView` | `api/blogs` |
| `POST` to the collection | `CreateAPIView` | the **same** URL — collision |
| `GET` one row | `RetrieveAPIView` | `api/blogs/<pk>` |
| `PUT` one row | `UpdateAPIView` | the same URL again |
| `PATCH` one row | `UpdateAPIView` | and again |
| `DELETE` one row | `DestroyAPIView` | and again |

Two problems, and the second is the interesting one.

The obvious problem is repetition: every one of those classes restates `queryset`,
`serializer_class` and `permission_classes`. Change the serializer and you edit five places. Miss
one and `GET` and `POST` disagree about what a blog post is.

The real problem is that **URLs and operations are not one-to-one.** `/blogs/api/blogs/` is not one
endpoint; it is two — a `GET` and a `POST` sharing an address. Django's `path()` maps one URL to one
view, so DRF's answer is combination classes: `ListCreateAPIView` for the collection,
`RetrieveUpdateDestroyAPIView` for the row. That works, and you end up with two classes whose names
are inventories of their own contents.

**WHY this is worth fixing** — the thing that actually varies is neither the URL nor the HTTP verb.
It is the **resource**: "blogs". Six operations belong to it, and they all share one queryset and one
serializer. A class per operation scatters one idea; a class per resource keeps it together and lets
something else derive the URLs. That class is a `ViewSet`, and that something else is a router.

**CHECKPOINT 1** — before typing anything, name the three attributes that get repeated in the table
above. If the room cannot name them, do not move on — the whole day is the fix for that repetition.

> **DOCS** — [Generic views](https://www.django-rest-framework.org/api-guide/generic-views/) ·
> [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/) ·
> [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/)

\newpage

# Part 2 — A model worth serving

`Author` has two fields. A viewset over it demonstrates the mechanics and hides every interesting
question — chiefly what a foreign key does to a serializer. So add a second model.

## 2.1 The `Blog` model

**TYPE** — append to `blog/models.py`, below `Author`:

```python
class Blog(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="blogs")
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "blogs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
```

**WHY `__str__` is not optional in practice** — without it, `Model.__str__` falls back to
`"Blog object (1)"`, and that string is what the admin changelist shows, what the shell prints, and
what any `{{ blog }}` in a template renders. One line, and every one of those becomes the title.

**WHY `related_name="blogs"`** — without it Django names the reverse accessor `blog_set`, and
anything walking from an author to their posts has to say `author.blog_set`. With it you write
`author.blogs`. It also gives you the string `"blogs"` to hand to `prefetch_related` later.

**WHY `on_delete=models.CASCADE`** — deleting an author deletes their posts. That is a decision, not
a default: `PROTECT` would refuse the delete, `SET_NULL` would orphan the posts and require
`null=True`. CASCADE is right here because a post with no author is not something this application
has a page for.

**WHY `auto_now_add` and `auto_now` are different** — `auto_now_add=True` stamps the row once, at
insert, and never again. `auto_now=True` re-stamps on every save. So `created_at` is history and
`updated_at` is state. Part 6 watches them diverge.

**WHY `db_table = "blogs"`** — Day 2's rule. Django would have called it `blog_blog`, which reads
like a typo.

**WHY `ordering = ["-created_at"]`** — newest first is what a blog index wants, and putting it on the
model means every queryset and API response agrees without repeating `order_by()`. Note it is the
*opposite* of `Author.ordering = ["name"]`, and that is fine: ordering belongs to the model.

**WHY the explicit `id = models.AutoField(primary_key=True)`** — this line is doing something, and
not quite what it looks like. Django adds a primary key automatically, and `config/settings.py` sets
`DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'`, so `Blog.id` would have been a **64-bit**
column. Writing `AutoField` explicitly overrides that for this one model and makes it 32-bit. You can
see it in the SQL in 2.3: `"id" integer`, where `authors.id` is `bigint`. It works, and four billion
blog posts is not your problem, but know that the line is an opt-out from a project-wide setting
rather than a no-op. Delete it and you get a `BigAutoField` and one more migration.

## 2.2 Make the migration

**TYPE**

```bash
python manage.py makemigrations blog
```

**EXPECT**

```
Migrations for 'blog':
  blog/migrations/0003_blog.py
    + Create model Blog
```

## 2.3 Read the SQL before you run it

**TYPE**

```bash
python manage.py sqlmigrate blog 0003
```

**EXPECT**

```sql
BEGIN;
--
-- Create model Blog
--
CREATE TABLE "blogs" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "content" text NOT NULL, "published" bool NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "author_id" bigint NOT NULL REFERENCES "authors" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "blogs_author_id_d83be8a6" ON "blogs" ("author_id");
COMMIT;
```

Four things to point at:

- **`"id" integer`** — 32-bit, because of the explicit `AutoField`. Compare `"author_id" bigint`,
  which follows `authors.id` and the project default. Two different integer widths in one table.
- **`"author_id"`** — the field you called `author` is a column called `author_id`. That `_id`
  suffix is why the serializer in Part 3 can accept a plain number for it.
- **`REFERENCES "authors" ("id")`** — the foreign key points at the table you renamed on Day 2, not
  at `blog_author`. `db_table` is doing its job.
- **`CREATE INDEX`** — Django indexes foreign keys without being asked, because `WHERE author_id = ?`
  is the query every reverse lookup makes.

**TYPE**

```bash
python manage.py migrate
echo ".tables" | python manage.py dbshell
```

**EXPECT** — `Applying blog.0003_blog... OK`, and `blogs` in the table list next to `authors`.

## 2.4 Register it in the admin

**TYPE** — `blog/admin.py`, in full:

```python
from django.contrib import admin
from .models import Author, Blog
# Register your models here.

admin.site.register(Author)
admin.site.register(Blog)
```

**CHECKPOINT 2** — `python manage.py check` is clean, `blogs` exists, and `/admin/blog/blog/add/`
gives you a form with an **Author** dropdown. Create two posts by hand — one with **Published**
ticked, one without. Part 6 reads them back.

**WHY the dropdown has authors in it** — the admin built it from the foreign key. The same fact is
what makes `author` writable in Part 3.

> **DOCS** — [Model field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/) ·
> [`ForeignKey`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#foreignkey) ·
> [`related_name`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ForeignKey.related_name) ·
> [`AutoField` / `DEFAULT_AUTO_FIELD`](https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field) ·
> [Migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/) ·
> [The admin site](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/)

\newpage

# Part 3 — The serializer

**TYPE** — `blog/serializers.py`, in full. `AuthorSerializer` is yesterday's; `BlogSerializer` is new:

```python
from rest_framework import serializers
from .models import Author, Blog


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = [
            'id',
            'name',
            'bio'
        ]
        read_only_fields = ['id']


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = [
            'id',
            'title',
            'content',
            'author',
            'published',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
```

## 3.1 Reading it

**WHY there is no `author = ...` line and `author` still works** — this is the part worth slowing
down for. `ModelSerializer` reads the model and picks a field type per column. For a `ForeignKey` it
picks `PrimaryKeyRelatedField`, and it sets that field's `queryset` to `Author.objects.all()` on its
own. So `author` is **writable**, it accepts a plain integer, and it validates that the integer is a
real author — none of which you wrote. Part 6 sends `"author": 1` and gets `400` for `"author": 9999`.

**WHY the response contains `"author": 1` and not the author's name** — a `PrimaryKeyRelatedField`
renders as the primary key in both directions. A client that wants "by Jane Austen" has to call
`/blogs/api/authors` as well. That is a real cost, and the fix — nesting `AuthorSerializer` for
reading while keeping something writable for input — is a serializer-relations topic linked in
Appendix E. Today's shape is the honest default, and it is worth understanding before you replace it.

**WHY `read_only_fields = ['id', 'created_at', 'updated_at']`** — those three are set by the database
and by `auto_now`/`auto_now_add`, so a client must not be able to send them. Marking them read-only
keeps them **visible in output** and **ignored in input**. Leaving them out of `fields` would also
make them unwritable, by making them invisible — a different and worse API.

**WHY `read_only` means "ignored", not "rejected"** — send `created_at` in a `PATCH` and you get
`200`, not `400`, and the value does not change. Part 6 does exactly that. Silent is the DRF
convention here; it means a client can round-trip a whole object back at you without stripping fields.

**WHY `id` is listed in `read_only_fields` when it already cannot be written** — belt and braces. It
is harmless and it documents intent.

**CHECKPOINT 3** — `python manage.py check` is clean. Nothing is reachable yet: no view, no URL.

> **DOCS** — [Serializers](https://www.django-rest-framework.org/api-guide/serializers/) ·
> [`ModelSerializer`](https://www.django-rest-framework.org/api-guide/serializers/#modelserializer) ·
> [`read_only_fields`](https://www.django-rest-framework.org/api-guide/serializers/#specifying-read-only-fields) ·
> [Serializer relations](https://www.django-rest-framework.org/api-guide/relations/) ·
> [`PrimaryKeyRelatedField`](https://www.django-rest-framework.org/api-guide/relations/#primarykeyrelatedfield)

\newpage

# Part 4 — One class per resource

**TYPE** — `blog/views.py`, in full. `AuthorListView` goes away; both resources become viewsets:

```python
from django.shortcuts import get_object_or_404, render
from rest_framework import generics
from rest_framework import viewsets
from .serializers import AuthorSerializer, BlogSerializer
from .models import Author, Blog
from rest_framework.permissions import IsAuthenticated,AllowAny


def author_list(request):
    authors = Author.objects.order_by("name")
    return render(request, "blog/author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, "blog/author_detail.html", {"author": author})


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticated]

class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    permission_classes = [IsAuthenticated]
```

Three lines of body each. Six operations each. Here is what is behind them.

**WHY `AuthorListView` is gone rather than kept** — it was
`generics.ListCreateAPIView`, which is list and create and nothing else. There was no
`/blogs/api/authors/1/` at all: no retrieve, no update, no delete. `AuthorViewSet` is the same three
attributes and gets all six, so keeping the old class would mean maintaining two ways to reach one
table, one of them worse. Note the `generics` import at the top of the file is now unused — a
leftover the next tidy-up should remove.

## 4.1 What `ModelViewSet` actually is

**TYPE**

```bash
python manage.py shell -c "
from rest_framework import viewsets
print(viewsets.ModelViewSet.__mro__[1:7])"
```

**EXPECT** — one long line, wrapped here for the page:

```
(<class 'rest_framework.mixins.CreateModelMixin'>, <class 'rest_framework.mixins.RetrieveModelMixin'>,
 <class 'rest_framework.mixins.UpdateModelMixin'>, <class 'rest_framework.mixins.DestroyModelMixin'>,
 <class 'rest_framework.mixins.ListModelMixin'>, <class 'rest_framework.viewsets.GenericViewSet'>)
```

That first line is Django 5.2's `shell` telling you it pre-imported your models; ignore it wherever
it appears below.

`ModelViewSet` is five mixins plus `GenericViewSet`. You could have written it by hand:

```python
# Equivalent to ModelViewSet. Do not type this — it is here to be read.
class BlogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
```

**TYPE** — count the methods those mixins contribute:

```bash
python manage.py shell -c "
from blog.views import BlogViewSet
print([m for m in dir(BlogViewSet) if m in
       ('list','retrieve','create','update','partial_update','destroy')])"
```

**EXPECT**

```
10 objects imported automatically (use -v 2 for details).

['create', 'destroy', 'list', 'partial_update', 'retrieve', 'update']
```

**WHY six methods from five mixins** — `UpdateModelMixin` brings two: `update` for `PUT` and
`partial_update` for `PATCH`. That asymmetry is the most-forgotten fact about DRF's mixins, and it is
why the list is longer than the mixin count.

**WHY the methods are named `list` and `retrieve` rather than `get`** — this is the real difference
between a `ViewSet` and an `APIView`. An `APIView` is addressed by HTTP verb: define `get()` and
`GET` reaches it. A viewset is addressed by **action** — `list`, `retrieve`, `create`, `update`,
`partial_update`, `destroy` — and something else decides which verb at which URL maps to which
action. Nothing in `BlogViewSet` mentions `GET`. That mapping is deliberately not the class's job,
and *that* is what lets one class serve two different URLs.

## 4.2 The four viewset bases

Name the shelf you are reaching onto. DRF ships four ways to be a viewset:

| Class | What it is | Use it when |
| --- | --- | --- |
| `ViewSet` | `APIView` + action dispatch. No queryset, no serializer, no actions | The resource is not a model |
| `GenericViewSet` | `GenericAPIView` + action dispatch. Still no actions | You want *some* of the six |
| `ReadOnlyModelViewSet` | `GenericViewSet` + `list` + `retrieve` | The resource is genuinely read-only |
| `ModelViewSet` | `GenericViewSet` + all five mixins | You want all six |

**WHY `ReadOnlyModelViewSet` deserves a mention** — if the API should not let clients change a
resource, this one class is the whole answer. Reaching for `ModelViewSet` and then fighting it with
permissions is the more common and the worse habit.

**WHY `GenericViewSet` alone does nothing** — it is `GenericAPIView` plus action dispatch, and no
actions. Every request against it returns `405`. The mixins are the behaviour; the viewset is the
wiring. That is the form to use the day "all six" is the wrong number.

## 4.3 `permission_classes = [IsAuthenticated]`

**WHY it is here at all** — `config/settings.py` sets the project default to
`DjangoModelPermissionsOrAnonReadOnly`, which would let the anonymous internet read every blog post
and would tie writes to rows in Django's `auth_permission` table. `IsAuthenticated` on each class
overrides both: no token, no access, in either direction. Both viewsets set it, and they have to —
a permission class on one says nothing about the other.

**WHY that is a stricter rule than the HTML pages follow** — `/blogs/` is public and
`/blogs/api/blogs/` is not, for the same data. That is a deliberate inconsistency for today: it keeps
the permission story to one line while you learn routers. `IsAuthenticatedOrReadOnly` is the class
that makes reads public and writes authenticated, and the permissions documentation in Appendix E is
where to go when you want it.

**CHECKPOINT 4** — `python manage.py check` is clean and `BlogViewSet` is in `blog/views.py`. Still
nothing is reachable: a viewset has no `as_view()` you can call with no arguments, which is Part 5's
problem.

> **DOCS** — [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/) ·
> [`ModelViewSet`](https://www.django-rest-framework.org/api-guide/viewsets/#modelviewset) ·
> [`ReadOnlyModelViewSet`](https://www.django-rest-framework.org/api-guide/viewsets/#readonlymodelviewset) ·
> [Mixins](https://www.django-rest-framework.org/api-guide/generic-views/#mixins) ·
> [Permissions](https://www.django-rest-framework.org/api-guide/permissions/)

\newpage

# Part 5 — The router

## 5.1 What a viewset cannot do

**TYPE**

```bash
python manage.py shell -c "
from blog.views import BlogViewSet
BlogViewSet.as_view()"
```

**EXPECT** — the last line of the traceback:

```
TypeError: The `actions` argument must be provided when calling `.as_view()` on a ViewSet. For example `.as_view({'get': 'list'})`
```

There it is. A generic view knows which method answers `GET`, so `as_view()` needs no help. A viewset
does not. `as_view({"get": "list"})` is you supplying the verb-to-action map by hand, and you *could*
write the whole thing out:

```python
# Do not type this. It is what you are about to stop doing.
path("api/blogs/", BlogViewSet.as_view({"get": "list", "post": "create"})),
path("api/blogs/<int:pk>/", BlogViewSet.as_view({
    "get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy",
})),
```

That works. Read it once, because it is exactly what a router does for you — two URLs, six mappings,
all of it mechanical and all of it identical for the next resource.

## 5.2 Register both viewsets in the app

The router goes in `blog/urls.py`, next to the app's other routes. The app owns its own URLs.

**TYPE** — `blog/urls.py`. Register `blogs` first, and **read 5.5 before you type the `authors`
line** — the obvious version of it has a bug:

```python
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from . import views


app_name = "blog"
router = DefaultRouter()
router.register(r'blogs', views.BlogViewSet, basename='blog')
# `basename` becomes the route-name prefix. `author` would collide with the
# `author-list` and `author-detail` page names below, in this same `blog:`
# namespace — and a duplicate name is not an error, the later one wins.
router.register(r'authors', views.AuthorViewSet, basename='api-author')

urlpatterns = [
    path("", views.author_list, name="author-list"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),

    # API endpoints(Class-based views)
    # path('api/authors',views.AuthorListView.as_view()),
    
    path("api/", include(router.urls)),
]
```

**WHY the old author route is commented out and not deleted** — it is the before-and-after.
Uncomment it and both styles serve side by side; that is a useful ten seconds on the projector.
Note the leftovers, though: `AuthorListView` is gone from `views.py`, so that commented line no
longer even names a real class, and the `generics` import above it is unused. Dead code with a
comment explaining itself is fine on a teaching branch and would not survive a review.

**WHY `basename=` at all** — the router builds route names from it: `{basename}-list` and
`{basename}-detail`. It is *optional* for both of these, because each viewset has a class-level
`queryset` and the router can read `queryset.model` to guess `blog` and `author`. Pass it anyway.
The day someone replaces `queryset` with a `get_queryset()` method, the guess stops working:

```
AssertionError: `basename` argument not specified, and could not automatically determine the name from the viewset, as it does not have a `.queryset` attribute.
```

And as 5.5 shows, the guessed name is sometimes the *wrong* name.

**WHY the `r''` prefix on `r'blogs'`** — habit, and harmless. It marks a raw string, which matters
for regexes with backslashes. There are none here, so `"blogs"` would be identical.

## 5.3 See what two lines bought

**TYPE**

```bash
python manage.py shell -c "
from blog.urls import router
for u in router.urls:
    print(f'{str(u.pattern):50} {u.name}')"
```

**EXPECT**

```
10 objects imported automatically (use -v 2 for details).

^blogs/$                                           blog-list
^blogs\.(?P<format>[a-z0-9]+)/?$                   blog-list
^blogs/(?P<pk>[^/.]+)/$                            blog-detail
^blogs/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$    blog-detail
^authors/$                                         api-author-list
^authors\.(?P<format>[a-z0-9]+)/?$                 api-author-list
^authors/(?P<pk>[^/.]+)/$                          api-author-detail
^authors/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$  api-author-detail
                                                   api-root
<drf_format_suffix:format>                         api-root
```

Ten patterns from two `register()` calls. Things to point at:

- **Names come from `basename`**, not from the URL prefix. The URL says `authors/`, the name says
  `api-author-`. That independence is what 5.5 relies on.
- **Each route appears twice.** The `\.(?P<format>...)` twin is the format suffix, so
  `/blogs/api/blogs.json` is the same view with the renderer forced. That, plus the `api-root` view
  at the bottom, **is the only difference between `DefaultRouter` and `SimpleRouter`.**
- **`api-root`** is a view you did not write: the index that lists registered resources.

## 5.4 Where the URLs landed

**TYPE**

```bash
python manage.py shell -c "
from django.urls import reverse
names = ['blog:author-list', 'blog:author-detail',
         'blog:api-author-list', 'blog:api-author-detail',
         'blog:blog-list', 'blog:blog-detail']
for n in names:
    args = [1] if n.endswith('detail') else []
    print(f'{n:26} -> {reverse(n, args=args)}')"
```

**EXPECT**

```
10 objects imported automatically (use -v 2 for details).

blog:author-list           -> /blogs/
blog:author-detail         -> /blogs/authors/1/
blog:api-author-list       -> /blogs/api/authors/
blog:api-author-detail     -> /blogs/api/authors/1/
blog:blog-list             -> /blogs/api/blogs/
blog:blog-detail           -> /blogs/api/blogs/1/
```

Six names, two of them pages and four of them endpoints, all in one namespace and all distinct.

**WHY the URL says `blogs` twice** — `config/urls.py` mounts this whole app at `blogs/`, inside it
you mounted the router at `api/`, and the resource is registered as `blogs`. Stack them and you get
`/blogs/api/blogs/`. It works and it is what your branch does, but say it out loud: the outer
`blogs/` is the *app* (whose pages actually list **authors**), and the inner `blogs` is the
*resource*. If that bothers you, mount the router from `config/urls.py` at `api/` instead of from
`blog/urls.py` and you get `/api/blogs/`. Both are defensible; today's branch does the app-owned one.

## 5.5 The collision, and why `basename='api-author'`

Here is the bug the comment in 5.2 is guarding against. Register the authors the obvious way:

```python
router.register(r'authors', views.AuthorViewSet, basename='author')
```

**TYPE**

```bash
python manage.py shell -c "
from django.urls import reverse
print(reverse('blog:author-list'))
print(reverse('blog:author-detail', args=[1]))"
```

**EXPECT** — not the pages:

```
10 objects imported automatically (use -v 2 for details).

/blogs/api/authors/
/blogs/api/authors/1/
```

`basename='author'` makes the router generate `author-list` and `author-detail` — the **exact names**
the HTML pages already registered four lines below, in the same `blog:` namespace. Django does not
complain about a duplicate URL name. It resolves `reverse()` to the **last** one registered, and the
router's `include()` sits at the end of `urlpatterns`, so the API wins.

**WHY this is nastier than an exception** — nothing fails. `python manage.py check` is clean,
`/blogs/` still returns `200`, and the test suite passes. What breaks is every `{% url %}` in your
templates:

```bash
curl -s http://127.0.0.1:8000/blogs/authors/1/ | grep -o 'href="[^"]*"'
```

**EXPECT** — with `basename='author'`, the "Back to all authors" link:

```
href="/blogs/api/authors/"
```

That link now sends a reader from an HTML page to a JSON endpoint that answers `401`. The page it
was pointing at is still there and still works; only the *name* moved. A duplicate URL name is a
silent redirect of every link that uses it.

**The fix is one word.** `basename='api-author'` moves the router's names out of the way, and the
pages get their names back — which is what 5.4 printed. Nothing about the URLs changes; the API is
still at `/blogs/api/authors/`. Only the reverse name differs.

**WHY not rename the pages instead** — you could, and `blog:author-page-list` would work. But the
templates already reverse `blog:author-list`, the HTML pages had the name first, and the API is the
newcomer. The newcomer moves.

**CHECKPOINT 5** — `python manage.py runserver`, then:

- <http://127.0.0.1:8000/blogs/api/> lists two resources, `blogs` and `authors`.
- <http://127.0.0.1:8000/blogs/api/blogs/> and `/blogs/api/authors/` both return `401`.
- <http://127.0.0.1:8000/blogs/api/authors/1/> returns `401` too — and it *exists*, which it did
  not this morning. That is `AuthorViewSet` earning its place over `AuthorListView`.
- <http://127.0.0.1:8000/blogs/> still renders the HTML author list, and **its links still point at
  pages**. Open `/blogs/authors/1/` and hover "Back to all authors": it must read `/blogs/`, not
  `/blogs/api/authors/`. If it reads the latter, your `basename` is `author` — go back to 5.5.
- <http://127.0.0.1:8000/blogs/api/authors> (no trailing slash) returns `404` — the old
  `AuthorListView` route is commented out, and the router's URLs all end in a slash.

> **DOCS** — [Routers](https://www.django-rest-framework.org/api-guide/routers/) ·
> [`DefaultRouter`](https://www.django-rest-framework.org/api-guide/routers/#defaultrouter) ·
> [`SimpleRouter`](https://www.django-rest-framework.org/api-guide/routers/#simplerouter) ·
> [Format suffixes](https://www.django-rest-framework.org/api-guide/format-suffixes/) ·
> [URL namespaces](https://docs.djangoproject.com/en/5.2/topics/http/urls/#url-namespaces) ·
> [`include()`](https://docs.djangoproject.com/en/5.2/ref/urls/#include)

\newpage

# Part 6 — Walk it with `curl`

**TYPE**

```bash
python manage.py runserver
```

In a second terminal:

**TYPE**

```bash
BASE=http://127.0.0.1:8000
curl -s $BASE/blogs/api/blogs/
```

**EXPECT**

```json
{"detail":"Authentication credentials were not provided."}
```

**WHY `401` and not `403`** — no credentials arrived at all, so DRF asks its first authentication
class for a `WWW-Authenticate` challenge and `JWTAuthentication` supplies one. A response that can
name a challenge is a `401`. Had you sent a *valid* token and still been refused, that would be a
`403`. Short version: `401` is "I do not know who you are", `403` is "I know, and you still may not".

**TYPE** — but the router's index is readable:

```bash
curl -s $BASE/blogs/api/
```

**EXPECT** — both registered resources, and note it is `authors`, not `api-authors`. The router
keys this index by **URL prefix**, not by `basename`:

```json
{"blogs":"http://127.0.0.1:8000/blogs/api/blogs/","authors":"http://127.0.0.1:8000/blogs/api/authors/"}
```

**WHY that one is not a `401`** — `api-root` is the router's own generated view, and it never got
your `permission_classes = [IsAuthenticated]`; it falls back to the project default,
`DjangoModelPermissionsOrAnonReadOnly`, which permits anonymous reads. So the index of your API is
public while the API is not. Harmless here, and a good illustration that a generated view is still a
view with its own permissions.

**TYPE** — log in and keep the token:

```bash
ACCESS=$(curl -s -X POST $BASE/accounts/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"asha","password":"lab-passphrase-2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")
echo "token length ${#ACCESS}"
```

**EXPECT** — a number in the mid-200s:

```
token length 255
```

Use your own username and password. If you do not have one, `POST /accounts/register/` from Day 4.

**IF IT FAILS** — `{"detail":"Given token not valid for any token type"}` later in this part means
the token expired. There is no `SIMPLE_JWT` block in `config/settings.py`, so the access token lives
**five minutes**. Re-run this command whenever that happens.

**TYPE** — create a post:

```bash
curl -s -X POST $BASE/blogs/api/blogs/ \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"title":"Why ViewSets","content":"One class, six routes.","author":1,"published":true}' \
  | python3 -m json.tool
```

**EXPECT**

```json
{
    "id": 1,
    "title": "Why ViewSets",
    "content": "One class, six routes.",
    "author": 1,
    "published": true,
    "created_at": "2026-09-02T07:39:29.478701Z",
    "updated_at": "2026-09-02T07:39:29.478712Z"
}
```

Your ids and timestamps will differ. Use an author id you actually have — `python manage.py shell -c
"from blog.models import Author; print(list(Author.objects.values_list('id','name')))"` prints them.

**WHY you sent `"author": 1` and got `"author": 1` back** — Part 3. `ModelSerializer` turned the
foreign key into a `PrimaryKeyRelatedField`, which is a primary key in both directions.

**WHY `created_at` and `updated_at` came back despite being read-only** — read-only means unwritable,
not invisible.

**TYPE** — list them:

```bash
curl -s $BASE/blogs/api/blogs/ -H "Authorization: Bearer $ACCESS" | python3 -m json.tool
```

**EXPECT** — a bare JSON array:

```json
[
    {
        "id": 1,
        "title": "Why ViewSets",
        "content": "One class, six routes.",
        "author": 1,
        "published": true,
        "created_at": "2026-09-02T07:39:29.478701Z",
        "updated_at": "2026-09-02T07:39:29.478712Z"
    }
]
```

**WHY it is a bare array and not `{"count": ..., "results": [...]}`** — there is no pagination
configured, so this endpoint promises to serialise the entire `blogs` table on every call. Fine with
two rows; a production incident with two hundred thousand. Pagination is the first thing to add after
today, and it is linked in Appendix E. Note that turning it on **changes this response shape**, so
anything you write against a bare array will break.

**TYPE** — the two validation failures, both worth seeing:

```bash
curl -s -X POST $BASE/blogs/api/blogs/ -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"title":"Ghost","content":"x","author":9999}'
echo
curl -s -X POST $BASE/blogs/api/blogs/ -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"title":"No author","content":"x"}'
```

**EXPECT**

```json
{"author":["Invalid pk \"9999\" - object does not exist."]}
{"author":["This field is required."]}
```

**WHY both are `400` and not `500`** — neither reached the database. The `queryset` that
`ModelSerializer` attached to the `author` field is a membership check, and the column being
`NOT NULL` made the field required. You wrote no validation code for either; DRF read your model. A
`500` with an `IntegrityError` is what you would get if the serializer had let them through.

**TYPE** — `PATCH` one field:

```bash
curl -s -X PATCH $BASE/blogs/api/blogs/1/ \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"title":"Why ViewSets, actually"}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['title']); print('created', d['created_at']); print('updated', d['updated_at'])"
```

**EXPECT** — `updated_at` has moved and `created_at` has not:

```
Why ViewSets, actually
created 2026-09-02T07:39:29.478701Z
updated 2026-09-02T07:39:45.987247Z
```

**TYPE** — the same partial body as a `PUT`:

```bash
curl -s -X PUT $BASE/blogs/api/blogs/1/ \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"title":"Only a title"}'
```

**EXPECT**

```json
{"content":["This field is required."],"author":["This field is required."]}
```

**WHY `PATCH` accepted it and `PUT` did not** — this is the whole distinction, and it is why
`UpdateModelMixin` gives you two methods. `PUT` means *replace the resource*, so every required field
must be present; anything you omit you are asking to delete. `PATCH` means *change these fields*, so
`partial=True` is passed to the serializer and missing fields are left alone. Same URL, same viewset,
two different contracts.

**TYPE** — try to write a read-only field:

```bash
curl -s -X PATCH $BASE/blogs/api/blogs/1/ \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"created_at":"1999-01-01T00:00:00Z"}' \
  | python3 -c "import sys,json; print('created_at still', json.load(sys.stdin)['created_at'])"
```

**EXPECT** — `200`, and nothing happened:

```
created_at still 2026-09-02T07:39:29.478701Z
```

**WHY silently and not `400`** — DRF drops read-only fields from the input before validation. It
means a client can `GET` an object, change one field, and `PUT` the whole thing back without
stripping the server-managed fields first. Convenient, and worth knowing so you do not spend an
afternoon wondering why your write "worked" and changed nothing.

**TYPE** — delete it, then try a verb the router never mapped:

```bash
curl -s -X DELETE -o /dev/null -w '%{http_code}\n' $BASE/blogs/api/blogs/1/ \
  -H "Authorization: Bearer $ACCESS"
curl -s -o /dev/null -w '%{http_code}\n' -X PUT $BASE/blogs/api/blogs/ \
  -H "Authorization: Bearer $ACCESS"
```

**EXPECT**

```
204
405
```

**WHY `204` and not `200`** — the row is gone, so there is nothing to return. `204 No Content` says
"done, and deliberately no body".

**WHY `405` on the second** — `PUT` to the *collection* URL. The router mapped `PUT` on the detail
route only, so the verb exists on the viewset but not at that address. `405 Method Not Allowed` is
the router's routing table talking, which is a neat way to see that the mapping is real.

**CHECKPOINT 6** — you have produced `401`, `200`, `201`, `204`, `400` twice with different messages,
and `405`. All six operations of one three-line class are reachable.

> **DOCS** — [Status codes](https://www.django-rest-framework.org/api-guide/status-codes/) ·
> [Validators](https://www.django-rest-framework.org/api-guide/validators/) ·
> [`PUT` vs `PATCH` — RFC 5789](https://www.rfc-editor.org/rfc/rfc5789) ·
> [Simple JWT settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html)

\newpage

# Part 7 — What the generated docs say now

**TYPE**

```bash
python manage.py spectacular --validate --fail-on-warn > /dev/null && echo "schema OK"
```

**EXPECT**

```
schema OK
```

**WHY it passes with no annotations at all** — each viewset has a `queryset` and a
`serializer_class`, which is everything drf-spectacular needs to work out the request and response
bodies for all six operations. The `unable to guess serializer` warning you saw on Day 4 came from a
bare `APIView` with neither.

**TYPE** — look at what it produced:

```bash
python manage.py shell -c "
from drf_spectacular.generators import SchemaGenerator
s = SchemaGenerator().get_schema(request=None, public=True)
for p in sorted(k for k in s['paths'] if k.startswith('/blogs/')):
    for verb, op in s['paths'][p].items():
        print(f'{verb.upper():7} {p:32} opid={op[\"operationId\"]}')"
```

**EXPECT**

```
10 objects imported automatically (use -v 2 for details).

GET     /blogs/api/authors/              opid=blogs_api_authors_list
POST    /blogs/api/authors/              opid=blogs_api_authors_create
GET     /blogs/api/authors/{id}/         opid=blogs_api_authors_retrieve
PUT     /blogs/api/authors/{id}/         opid=blogs_api_authors_update
PATCH   /blogs/api/authors/{id}/         opid=blogs_api_authors_partial_update
DELETE  /blogs/api/authors/{id}/         opid=blogs_api_authors_destroy
GET     /blogs/api/blogs/                opid=blogs_api_blogs_list
POST    /blogs/api/blogs/                opid=blogs_api_blogs_create
GET     /blogs/api/blogs/{id}/           opid=blogs_api_blogs_retrieve
PUT     /blogs/api/blogs/{id}/           opid=blogs_api_blogs_update
PATCH   /blogs/api/blogs/{id}/           opid=blogs_api_blogs_partial_update
DELETE  /blogs/api/blogs/{id}/           opid=blogs_api_blogs_destroy
```

Twelve operations documented for free, from six lines of viewset — and three things that are not
free:

- **Every `summary` is empty.** Add `summary=` to that print and you get `'(none)'` twelve times.
  Swagger UI shows the operations with no prose. Day 4's `@extend_schema` fixes one operation; on a
  viewset the decorator you want is `@extend_schema_view(list=..., retrieve=..., create=...,
  update=..., partial_update=..., destroy=...)`, because a single `@extend_schema` on the class
  applies the *same* summary to all six. Linked in Appendix E.
- **`operationId=blogs_api_blogs_list`.** Generated from the URL path, so the doubled `blogs` from
  5.4 shows up in the names any client generator will produce. Cosmetic, and a reason to care about
  the URL shape.
- **`basename` is nowhere in the schema.** The operation ids come from the path and the actions;
  `api-author` never appears. Route names are a Django-side concern, so 5.5's fix is invisible to
  the document — which is exactly why the collision was invisible until a template rendered.

**TYPE** — then drive it in the browser. Open
<http://127.0.0.1:8000/api/schema/swagger-ui/>, click **Authorize**, type `Bearer `, a space, and
paste your access token.

**CHECKPOINT 7** — Swagger UI lists six operations under `blogs` and six under `authors`, and
`POST` succeeds from inside the page once you have authorised.

> **DOCS** — [drf-spectacular customisation](https://drf-spectacular.readthedocs.io/en/latest/customization.html) ·
> [`extend_schema_view`](https://drf-spectacular.readthedocs.io/en/latest/drf_spectacular.html#drf_spectacular.utils.extend_schema_view) ·
> [Settings](https://drf-spectacular.readthedocs.io/en/latest/settings.html) ·
> [OpenAPI specification](https://spec.openapis.org/oas/latest.html)

\newpage

# Part 8 — Commit and push

**TYPE**

```bash
git status
git add -A
git commit -m "day 8: Blog model, BlogViewSet and a DefaultRouter"
git push -u origin <first_name>/day8
```

**EXPECT** — five modified paths, plus the new migration:

```
modified:   blog/admin.py
modified:   blog/models.py
modified:   blog/serializers.py
modified:   blog/urls.py
modified:   blog/views.py
new file:   blog/migrations/0003_blog.py
```

**WHY the migration is the one to check** — it is a new file, so `git add <file>` on the five modified
paths misses it. A branch with a `Blog` model and no `0003_blog.py` fails for every reviewer with
`no such table: blogs`, and the error appears at request time rather than at `migrate`.

## 8.1 Prove it worked

Do not trust the directory you built it in.

**TYPE**

```bash
cd /tmp
git clone -b <first_name>/day8 <your-repo-url> day8-check
cd day8-check
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
```

**EXPECT** — `Applying blog.0003_blog... OK`, then
`System check identified no issues (0 silenced).`

**IF IT FAILS** — `pip install -r requirements.txt` erroring on the first line means
`requirements.txt` is still UTF-16 encoded from an earlier day. Re-create it with
`pip freeze > requirements.txt` from a shell that writes UTF-8, check the file opens as plain text,
and commit it.

**CHECKPOINT 8** — a fresh clone of your branch installs, migrates and passes `check`, with no files
copied from your working directory.

> **DOCS** — [`git add`](https://git-scm.com/docs/git-add) ·
> [Migrations in version control](https://docs.djangoproject.com/en/5.2/topics/migrations/#version-control) ·
> [`pip freeze`](https://pip.pypa.io/en/stable/cli/pip_freeze/)

\newpage

# Appendix A — Troubleshooting

| You see | It means | Fix |
| --- | --- | --- |
| `TypeError: The 'actions' argument must be provided when calling '.as_view()' on a ViewSet` | You wired a viewset with `path()` and `as_view()` | Register it on a router instead (5.2) |
| `AssertionError: 'basename' argument not specified, and could not automatically determine the name from the viewset` | The viewset has no class-level `queryset` | Pass `basename=` to `register()` (5.2) |
| `{% url 'blog:author-list' %}` renders `/blogs/api/authors/` | Duplicate URL name — the router's `basename='author'` collided with the page name, and the later one won | `basename='api-author'` (5.5) |
| "Back to all authors" leads to `{"detail":"Authentication credentials were not provided."}` | Same collision. The link reversed to the API | Same fix (5.5) |
| `NoReverseMatch: 'post-list' is not a valid view function or pattern name` | `base.html` links a route you have not written yet | Comment the nav link out, or add the route |
| `401 {"detail":"Authentication credentials were not provided."}` on any `/blogs/api/...` URL | No `Authorization` header. Both viewsets are `IsAuthenticated` | `-H "Authorization: Bearer $ACCESS"` (Part 6) |
| `401 {"detail":"Given token not valid for any token type"}` mid-transcript | The access token expired. There is no `SIMPLE_JWT` block, so it lives **five minutes** | Log in again (6, IF IT FAILS) |
| `403` where you expected `401` | You *are* authenticated and the permission class still refused you | Read `permission_classes` on that viewset |
| `405 Method Not Allowed` | The verb exists on the viewset but not at that URL — e.g. `PUT` on the collection | Use the detail URL (Part 6) |
| `404` on `/blogs/api/authors` | No trailing slash. Every router URL ends in one | `/blogs/api/authors/` |
| `400 {"content":["This field is required."],"author":["This field is required."]}` on a one-field update | You sent `PUT`, which replaces the whole resource | Use `PATCH` (Part 6) |
| `400 {"author":["Invalid pk \"9999\" - object does not exist."]}` | The id is not in the serializer's implicit `Author.objects.all()` | Use a real id — `GET /blogs/api/authors/` |
| `400 {"author":["This field is required."]}` | `author_id` is `NOT NULL`, so `ModelSerializer` made the field required | Send `"author": <id>` |
| A `PATCH` returns `200` and changes nothing | You only sent read-only fields; DRF drops them before validation | Send a writable field (Part 6) |
| `500 IntegrityError: NOT NULL constraint failed: blogs.author_id` | The serializer let a missing author through — usually `author` marked read-only | Leave `author` writable (Part 3) |
| Admin changelist shows `Blog object (1)` | No `__str__` on the model | Add it (2.1) |
| Template comment text appears in the page | `{# ... #}` is single-line only; spread over two lines it is not a comment, and tags inside it execute | Use `{% comment %}...{% endcomment %}` |
| A template edit has no effect | The dev server caches templates | Restart `runserver` |
| `spectacular` warns `unable to guess serializer` | A view with neither `serializer_class` nor an annotation | `@extend_schema` on it (Part 7) |
| `pip install -r requirements.txt` fails on line 1 | The file is UTF-16 from an earlier day | Re-create it as UTF-8 (8.1) |
| `Invalid HTTP_HOST header: 'testserver'` | You drove `django.test.Client` outside the test runner | Run through `manage.py test` |
| `That port is already in use` | An earlier `runserver` is still up | `runserver 8001`, or stop the other one |

\newpage

# Appendix B — Official documentation index

**Django 5.2 — models, URLs, admin**

- [Model field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/) · [`ForeignKey`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#foreignkey) · [`related_name`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ForeignKey.related_name)
- [`AutoField`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#autofield) · [`DEFAULT_AUTO_FIELD`](https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field) · [`Meta` options](https://docs.djangoproject.com/en/5.2/ref/models/options/) · [`__str__`](https://docs.djangoproject.com/en/5.2/ref/models/instances/#str)
- [Many-to-one relationships](https://docs.djangoproject.com/en/5.2/topics/db/examples/many_to_one/) · [Related objects reference](https://docs.djangoproject.com/en/5.2/ref/models/relations/)
- [Migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/) · [`sqlmigrate`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#sqlmigrate) · [`makemigrations --check`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#cmdoption-makemigrations-check)
- [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/) · [URL namespaces](https://docs.djangoproject.com/en/5.2/topics/http/urls/#url-namespaces) · [`reverse()`](https://docs.djangoproject.com/en/5.2/ref/urlresolvers/#reverse) · [`include()`](https://docs.djangoproject.com/en/5.2/ref/urls/#include)
- [The admin site](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/) · [`ModelAdmin` options](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#modeladmin-options)

**Django REST Framework — today's core**

- [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/) · [`ModelViewSet`](https://www.django-rest-framework.org/api-guide/viewsets/#modelviewset) · [`ReadOnlyModelViewSet`](https://www.django-rest-framework.org/api-guide/viewsets/#readonlymodelviewset)
- [Routers](https://www.django-rest-framework.org/api-guide/routers/) · [`DefaultRouter`](https://www.django-rest-framework.org/api-guide/routers/#defaultrouter) · [`SimpleRouter`](https://www.django-rest-framework.org/api-guide/routers/#simplerouter) · [Format suffixes](https://www.django-rest-framework.org/api-guide/format-suffixes/)
- [Generic views](https://www.django-rest-framework.org/api-guide/generic-views/) · [Mixins](https://www.django-rest-framework.org/api-guide/generic-views/#mixins) · [`GenericAPIView`](https://www.django-rest-framework.org/api-guide/generic-views/#genericapiview)
- [Serializers](https://www.django-rest-framework.org/api-guide/serializers/) · [`ModelSerializer`](https://www.django-rest-framework.org/api-guide/serializers/#modelserializer) · [`read_only_fields`](https://www.django-rest-framework.org/api-guide/serializers/#specifying-read-only-fields)
- [Serializer relations](https://www.django-rest-framework.org/api-guide/relations/) · [`PrimaryKeyRelatedField`](https://www.django-rest-framework.org/api-guide/relations/#primarykeyrelatedfield) · [Validators](https://www.django-rest-framework.org/api-guide/validators/)
- [Permissions](https://www.django-rest-framework.org/api-guide/permissions/) · [Status codes](https://www.django-rest-framework.org/api-guide/status-codes/) · [The browsable API](https://www.django-rest-framework.org/topics/browsable-api/) · [Settings](https://www.django-rest-framework.org/api-guide/settings/)

**Simple JWT**

- [Documentation home](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/) · [Settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html) · [Blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html)

**drf-spectacular and OpenAPI**

- [Documentation home](https://drf-spectacular.readthedocs.io/en/latest/) · [Customisation](https://drf-spectacular.readthedocs.io/en/latest/customization.html) · [Settings](https://drf-spectacular.readthedocs.io/en/latest/settings.html) · [FAQ](https://drf-spectacular.readthedocs.io/en/latest/faq.html)
- [OpenAPI specification](https://spec.openapis.org/oas/latest.html) · [Swagger UI](https://swagger.io/tools/swagger-ui/) · [ReDoc](https://redocly.com/redoc/)

**HTTP semantics, for the `PUT` / `PATCH` / status-code arguments**

- [RFC 9110 — HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html) · [`401 Unauthorized`](https://www.rfc-editor.org/rfc/rfc9110.html#name-401-unauthorized) · [`405 Method Not Allowed`](https://www.rfc-editor.org/rfc/rfc9110.html#name-405-method-not-allowed)
- [RFC 5789 — the `PATCH` method](https://www.rfc-editor.org/rfc/rfc5789) · [Richardson maturity model](https://martinfowler.com/articles/richardsonMaturityModel.html)

\newpage

# Appendix C — Command cheat sheet

```bash
# model and migration
python manage.py makemigrations blog
python manage.py sqlmigrate blog 0003
python manage.py migrate
python manage.py makemigrations --check --dry-run     # CI gate: non-zero if pending
echo ".tables" | python manage.py dbshell
echo ".schema blogs" | python manage.py dbshell

# introspection
python manage.py shell -c "
from blog.urls import router
for u in router.urls:
    print(f'{str(u.pattern):50} {u.name}')"

python manage.py shell -c "
from django.urls import reverse
print(reverse('blog:author-list'))        # must be /blogs/
print(reverse('blog:api-author-list'))    # must be /blogs/api/authors/
print(reverse('blog:blog-list'))"

python manage.py shell -c "
from rest_framework import viewsets
print(viewsets.ModelViewSet.__mro__[1:7])"

# schema
python manage.py spectacular                              # print
python manage.py spectacular --file schema.yml            # write (do not commit)
python manage.py spectacular --validate --fail-on-warn    # CI form

# exercising the API
BASE=http://127.0.0.1:8000

ACCESS=$(curl -s -X POST $BASE/accounts/login/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"asha","password":"lab-passphrase-2026"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -s $BASE/blogs/api/                                          # public index
curl -s $BASE/blogs/api/blogs/  -H "Authorization: Bearer $ACCESS"
curl -s $BASE/blogs/api/authors/ -H "Authorization: Bearer $ACCESS"
curl -s $BASE/blogs/api/authors/1/ -H "Authorization: Bearer $ACCESS"

curl -s -X POST $BASE/blogs/api/blogs/ -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' \
  -d '{"title":"T","content":"c","author":1,"published":true}'

curl -s -X PATCH $BASE/blogs/api/blogs/1/ -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"title":"New title"}'

curl -s -X DELETE -o /dev/null -w '%{http_code}\n' $BASE/blogs/api/blogs/1/ \
  -H "Authorization: Bearer $ACCESS"

# the link that proves 5.5
curl -s $BASE/blogs/authors/1/ | grep -o 'href="[^"]*"'
```

**The URL map after today**

| URL | Verb(s) | Reverse name | What answers it |
| --- | --- | --- | --- |
| `/admin/` | — | — | Django admin, now with `Blog` |
| `/blogs/` | `GET` | `blog:author-list` | HTML page of **authors** |
| `/blogs/authors/<id>/` | `GET` | `blog:author-detail` | HTML |
| `/blogs/api/` | `GET` | `blog:api-root` | Resource index. Public |
| `/blogs/api/authors/` | `GET` `POST` | `blog:api-author-list` | `AuthorViewSet` |
| `/blogs/api/authors/<pk>/` | `GET` `PUT` `PATCH` `DELETE` | `blog:api-author-detail` | `AuthorViewSet` |
| `/blogs/api/blogs/` | `GET` `POST` | `blog:blog-list` | `BlogViewSet` |
| `/blogs/api/blogs/<pk>/` | `GET` `PUT` `PATCH` `DELETE` | `blog:blog-detail` | `BlogViewSet` |
| `/accounts/register/` · `/login/` · `/logout/` | `POST` | — | Day 4 |
| `/api/schema/` · `/swagger-ui/` · `/redoc/` | `GET` | `schema` · `swagger-ui` · `redoc` | drf-spectacular |

Two viewsets. Ten router patterns. Two `register()` calls.

**Status codes used today**

| Code | Meaning here |
| --- | --- |
| `200` | Read succeeded, or `PUT`/`PATCH` succeeded |
| `201` | Row created |
| `204` | Row deleted, no body |
| `400` | The body was wrong: unknown `author`, missing required field, partial `PUT` |
| `401` | No token, or an expired one |
| `403` | Authenticated, and still refused |
| `404` | No such row — or no trailing slash |
| `405` | The action exists on the viewset but not at that URL |

\newpage

# Appendix D — Trainer notes

**Where this day came from** — Days 5 to 7 shipped code without guides, and the API layer had stalled
at one `AuthorListView(generics.ListCreateAPIView)` behind a hand-written `path()` in
`blog/urls.py`. Day 4's Appendix D named the next step as "putting the `Author` API from the Day 3
guide behind these tokens — `IsAuthenticatedOrReadOnly` on a viewset makes the permission classes
concrete rather than theoretical". This is that day, plus the `Blog` model that makes a viewset worth
having. The Day 3 guide's §4.2–4.3 already contains a `ModelViewSet` + `DefaultRouter` reference that
was reverted off `main` in PR #15; treat it as the same material done at speed if the room is ahead.

**Reference branch** — this guide is built from `kaushal/day8` (PR #20), verified against that
branch's files rather than retyped.

**Deltas from the live session (PR #20)** — the guide above is the corrected build. Five differences
worth naming out loud, because the room has the uncorrected version:

| Live session | Guide | Why it matters |
| --- | --- | --- |
| `router.register(r'authors', views.AuthorViewSet, basename='author')` | `basename='api-author'` | Duplicate URL name. `reverse('blog:author-list')` returned `/blogs/api/authors/`, so the "Back to all authors" link in `author_detail.html` pointed at a `401` JSON endpoint. `check` was clean and `/blogs/` still returned `200` — nothing failed loudly |
| `Blog` with no `__str__` (first commit) | `__str__` returning `self.title` | Fixed in the second commit. Before it, the admin changelist read `Blog object (1)` |
| `AuthorListView(ListCreateAPIView)` | `AuthorViewSet(ModelViewSet)` | Also fixed in the second commit. The old class had no detail route at all |
| `from rest_framework import generics` still imported | — | Unused once `AuthorListView` is gone. Harmless, and the kind of thing that accumulates |
| `blog/models.py` and `blog/views.py` end without a newline | — | Not worth a commit on its own; worth knowing why `git diff` prints `\ No newline at end of file` |

Two more, both pre-existing rather than introduced today: `blog/templates/` still carries stray
unnamespaced copies of `author_list.html` and `base.html` at the app root, which nothing renders;
and `requirements.txt` is UTF-16 encoded, so `pip install -r` fails for anyone cloning the branch.

**The 5.5 collision is the single most valuable thing in this day.** It is a real bug that a real
commit introduced, it produced no error of any kind, and the only visible symptom was a hyperlink
going somewhere unexpected. Run it as a live failure: set `basename='author'`, run `check` (clean),
open `/blogs/` (200), then hover the "Back to all authors" link on `/blogs/authors/1/` and click it.
The `401` JSON is the punchline. Then change one word.

**Live-demo order that lands best**

1. Open the Part 1 table on the projector and count the repeated lines before writing any code. The
   day only makes sense as an answer to a problem the room has felt.
2. Show `ModelViewSet.__mro__` and the `dir()` check in 4.1. Ask why the method list has six entries
   when there are five mixins. Somebody will find `UpdateModelMixin`; if not, tell them.
3. Do 5.1 — `as_view()` with no arguments — *before* mentioning routers. The `TypeError` names the
   missing thing, and a router is then obviously the answer rather than more syntax.
4. Print `router.urls`. Ten lines from two. Let it sit.
5. **Now do 5.5 as a live failure.** See above. This is the twenty minutes that matters.
6. Part 6 in order. The `401`, then login, then `201`.
7. `PUT` with a partial body, immediately after a successful `PATCH` with the same body. Two
   different answers from one URL is how `update` vs `partial_update` stops being trivia.
8. The read-only `PATCH` that returns `200` and changes nothing. Ask what should have happened.
9. Part 7 last, and work backwards: show the twelve operations with no summaries, ask why
   spectacular knew the field types but not the prose.

**Things that reliably confuse the room**

| Confusion | Say this |
| --- | --- |
| "`ViewSet` or `ModelViewSet`?" | `ModelViewSet` if you want all six. `GenericViewSet` + named mixins if you want fewer. |
| "Is `basename` required?" | Only when the router cannot read `.queryset`. Pass it always — and pick it carefully. |
| "Why did my authors page turn into JSON?" | Two URL names are the same. The later one won. That is 5.5. |
| "Why didn't Django warn me about the duplicate name?" | It has no way to know which one you meant. Duplicate names are legal. |
| "Why 401 and not 403?" | 401 = I do not know who you are. 403 = I know, and you still may not. |
| "Why 405 and not 404?" | The URL exists; that verb is not mapped to it. |
| "Why does `PUT` need every field?" | `PUT` replaces the resource. `PATCH` amends it. |
| "Why did my `created_at` update get a 200 and do nothing?" | Read-only fields are dropped before validation, not rejected. |
| "Why does the URL say `blogs` twice?" | App mount + router mount + resource name. Stack them and you get it. |
| "Do I commit `schema.yml`?" | No. Commit the code that generates it. |
| "My template edit did nothing." | Restart `runserver`. Templates are cached. |

**The one to check before they leave** — that `blog/migrations/0003_blog.py` is **staged**. It is a
new file, so `git add` on the five modified paths misses it, and a branch with a `Blog` model and no
migration fails for every reviewer with `no such table: blogs` — at request time, not at `migrate`.
Part 8.1's fresh clone is what catches it; make them actually run it.

**Second thing to check** — `reverse('blog:author-list')`. One shell command, and it is the
difference between a working branch and a branch whose author pages link into the API.

**Time budget** — Part 1 about 20 minutes (do not skip the counting exercise), Part 2 about 30,
Part 3 about 35 (the implicit `PrimaryKeyRelatedField` is the hardest idea), Part 4 about 35,
Part 5 about 45 (5.5 is worth 20 of those), Part 6 about 45, Part 7 about 25, Part 8 about 15.
Roughly four and a half hours with questions. If it must be cut, Part 7 is homework.
**Parts 4, 5.2 and 5.5 are not cuttable** — they are the day.

**Known rough edges, deliberately left in**

- **Both viewsets are `IsAuthenticated`, so the API has no public read at all** while `/blogs/` is
  fully public — the same data, two different rules. Deliberate for today: it keeps the permission
  story to one line per class. `IsAuthenticatedOrReadOnly` is the class that splits reads from
  writes; see Appendix E.
- **No pagination**, so `GET /blogs/api/blogs/` promises to serialise the whole table. Appendix E.
- **`GET /blogs/api/` is public** while everything under it is not, because the router's generated
  `APIRootView` never saw your `permission_classes` and fell back to the project default. Worth one
  sentence: a generated view is still a view.
- **The API returns `"author": 1`**, not the author's name, so any client rendering "by Jane Austen"
  needs a second request. That is the honest default of a `ModelSerializer` over a `ForeignKey`.
  Appendix E has the relations documentation.
- **`id = models.AutoField(primary_key=True)`** silently opts `Blog` out of the project's
  `DEFAULT_AUTO_FIELD = BigAutoField`, so `blogs.id` is 32-bit while `authors.id` is 64-bit. Visible
  in the `sqlmigrate` output in 2.3. Not a bug; worth knowing it is a decision.
- **No `SIMPLE_JWT` block**, so access tokens last five minutes and will expire mid-transcript.

**Carrying into Day 9** — the HTML side of the same model: a `ModelForm` and function-based views for
Blog CRUD, which is where `is_valid()`, `{% csrf_token %}` and the POST-then-redirect pattern get
taught. The templates for it ship on `dharmendra/day9-templates`; the forms, views and routes are the
exercise. After that: moving the router out of `blog/urls.py` into its own module mounted at `/api/`,
which fixes the doubled URL segment and makes 5.5 structurally impossible.

**Exercises, if the room is ahead**

1. Set `basename='author'`, then find every place the collision shows up. Write the one-line test
   that would have caught it.
2. Convert `AuthorViewSet` to `ReadOnlyModelViewSet`. Which four requests stop working, and with
   what status code?
3. Give `BlogViewSet` `permission_classes = [IsAuthenticatedOrReadOnly]` and describe, before
   running it, exactly which of the eight requests in Part 6 change.
4. Delete `basename` from both `register()` calls. Does anything break? Now replace `queryset` with
   a `get_queryset()` method and try again.
5. Add `?search=` to the blogs endpoint using only Appendix E's filtering documentation.
6. Work out why `operationId` says `blogs_api_blogs_list` and propose a URL layout that reads better.

\newpage

# Appendix E — Beyond today, and where to read about it

Today built one model, one serializer, two viewsets and one router. Everything below is a thing a
real API wants that this one does not have yet. Each entry says what it would fix here, then links
the official documentation — go and read it rather than waiting for a later day.

**Pagination** — `GET /blogs/api/blogs/` currently returns a bare array and promises to serialise
every row. Turning it on changes the response to `{"count", "next", "previous", "results"}`, so every
client reading `response[0]` breaks; do it early rather than late.

> [DRF — Pagination](https://www.django-rest-framework.org/api-guide/pagination/) ·
> [`PageNumberPagination`](https://www.django-rest-framework.org/api-guide/pagination/#pagenumberpagination) ·
> [`LimitOffsetPagination`](https://www.django-rest-framework.org/api-guide/pagination/#limitoffsetpagination) ·
> [`CursorPagination`](https://www.django-rest-framework.org/api-guide/pagination/#cursorpagination)

**Searching, ordering and filtering** — `SearchFilter` and `OrderingFilter` ship inside DRF, so
`?search=` and `?ordering=` cost one attribute each and no new dependency. `SearchFilter` follows
`author__name` across the foreign key. `ordering_fields` is an allowlist, not a convenience.
`django-filter` is the third-party package for `?published=true` style field filtering.

> [DRF — Filtering](https://www.django-rest-framework.org/api-guide/filtering/) ·
> [`SearchFilter`](https://www.django-rest-framework.org/api-guide/filtering/#searchfilter) ·
> [`OrderingFilter`](https://www.django-rest-framework.org/api-guide/filtering/#orderingfilter) ·
> [django-filter with DRF](https://django-filter.readthedocs.io/en/stable/guide/rest_framework.html)

**Per-action permissions, and public reads** — both viewsets are `IsAuthenticated`, so nothing is
readable without a token. `IsAuthenticatedOrReadOnly` is the one-line change that makes reads public
and writes authenticated. Object-level rules ("only the author may edit their own post") need a
custom permission class.

> [DRF — Permissions](https://www.django-rest-framework.org/api-guide/permissions/) ·
> [`IsAuthenticatedOrReadOnly`](https://www.django-rest-framework.org/api-guide/permissions/#isauthenticatedorreadonly) ·
> [Custom permissions and `has_object_permission`](https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions)

**Nested and hyperlinked relations** — the API answers `"author": 1`. To return the author object on
read while still accepting an id on write, you need either two fields or a writable nested
serializer with a hand-written `create()`. `HyperlinkedModelSerializer` is the URL-based alternative.

> [DRF — Serializer relations](https://www.django-rest-framework.org/api-guide/relations/) ·
> [Nested relationships](https://www.django-rest-framework.org/api-guide/relations/#nested-relationships) ·
> [Writable nested serializers](https://www.django-rest-framework.org/api-guide/serializers/#writable-nested-representations) ·
> [`HyperlinkedModelSerializer`](https://www.django-rest-framework.org/api-guide/serializers/#hyperlinkedmodelserializer)

**Extra actions on a viewset** — "publish this post" is not one of the six. `@action(detail=True,
methods=["post"])` gives it its own URL and its own route name, which is the thing a router can do
that a stack of `path()` calls cannot express.

> [DRF — Marking extra actions for routing](https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing) ·
> [Routing extra actions](https://www.django-rest-framework.org/api-guide/routers/#routing-for-extra-actions)

**A request-dependent queryset** — `queryset = Blog.objects.all()` is evaluated once at import and
cannot know who is asking. Overriding `get_queryset()` is how "anonymous readers see only published
posts" gets expressed — and note that filtering the queryset yields `404` rather than `403`, which
leaks less.

> [DRF — `get_queryset()`](https://www.django-rest-framework.org/api-guide/generic-views/#get_querysetself) ·
> [Filtering against the current user](https://www.django-rest-framework.org/api-guide/filtering/#filtering-against-the-current-user)

**Query efficiency** — serialising a foreign key for ten rows costs ten extra queries unless the
queryset says otherwise. `select_related` for forward foreign keys, `prefetch_related` for reverse
ones, and `assertNumQueries` to prove it.

> [Django — Database optimisation](https://docs.djangoproject.com/en/5.2/topics/db/optimization/) ·
> [`select_related`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-related) ·
> [`prefetch_related`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#prefetch-related) ·
> [`assertNumQueries`](https://docs.djangoproject.com/en/5.2/topics/testing/tools/#django.test.TransactionTestCase.assertNumQueries)

**Documenting a viewset properly** — all twelve operations have empty summaries. One
`@extend_schema` on a viewset class applies the *same* summary to all six of its actions, which is
why `@extend_schema_view` exists: one keyword per action, keyed on the action name
(`partial_update`, not `patch`).

> [drf-spectacular — Customisation](https://drf-spectacular.readthedocs.io/en/latest/customization.html) ·
> [`extend_schema_view`](https://drf-spectacular.readthedocs.io/en/latest/drf_spectacular.html#drf_spectacular.utils.extend_schema_view) ·
> [`extend_schema`](https://drf-spectacular.readthedocs.io/en/latest/drf_spectacular.html#drf_spectacular.utils.extend_schema)

**Testing the API** — a `curl` transcript proves it worked once, by hand. `APITestCase` proves it
again after every change, and `force_authenticate` skips the token dance for tests that are about
the viewset rather than about auth.

> [DRF — Testing](https://www.django-rest-framework.org/api-guide/testing/) ·
> [`APITestCase` and `APIClient`](https://www.django-rest-framework.org/api-guide/testing/#apiclient) ·
> [`force_authenticate`](https://www.django-rest-framework.org/api-guide/testing/#force_authenticate) ·
> [Django — Testing tools](https://docs.djangoproject.com/en/5.2/topics/testing/tools/)

**Addressing rows by something other than `pk`** — `lookup_field = "slug"` gives
`/blogs/api/blogs/why-viewsets/`. The catch is that a writable slug means the resource can change
its own address.

> [DRF — `lookup_field`](https://www.django-rest-framework.org/api-guide/generic-views/#attributes) ·
> [`SlugField`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#slugfield) ·
> [`slugify`](https://docs.djangoproject.com/en/5.2/ref/utils/#django.utils.text.slugify)

**Rate limiting, versioning, throttling** — the things that arrive the first time an API has real
users.

> [DRF — Throttling](https://www.django-rest-framework.org/api-guide/throttling/) ·
> [Versioning](https://www.django-rest-framework.org/api-guide/versioning/) ·
> [Caching](https://www.django-rest-framework.org/api-guide/caching/)

**Token lifetime and rotation** — five-minute access tokens with no `SIMPLE_JWT` block is why your
`$ACCESS` keeps expiring. Rotation plus the already-installed blacklist app is the pair worth
configuring.

> [Simple JWT — Settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html) ·
> [Token types](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/token_types.html) ·
> [Blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html)
