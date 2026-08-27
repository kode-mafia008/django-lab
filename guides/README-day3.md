---
title: "Day 3 — Templates, DRF, JWT Auth and OpenAPI Docs"
subtitle: "Rendering the Day 2 authors as a web page, then exposing them as a documented JSON API with register/login"
author: "Django Practical Lab — daily guide series"
date: "Django 5.2 LTS · DRF 3.18 · Simple JWT 5.5 · drf-spectacular 0.30"
---

# What we did today

| # | Task | Command / change | Result |
| --- | --- | --- | --- |
| 1 | Gave `Author` a string form and a default order | `__str__` + `Meta.ordering` | `blog/migrations/0002_alter_author_options.py` |
| 2 | Wrote the first views | `author_list`, `author_detail` in `blog/views.py` | Python functions that return HTML |
| 3 | Wired the app's URLs | `blog/urls.py` + `include()` in `config/urls.py` | `/` and `/authors/<id>/` resolve |
| 4 | Wrote the first templates | `blog/templates/blog/*.html` | The Day 2 authors render in a browser |
| 5 | Installed the API stack | `pip install djangorestframework djangorestframework-simplejwt drf-spectacular` | Three new apps in `INSTALLED_APPS` |
| 6 | Serialized the model | `AuthorSerializer` in `blog/serializers.py` | Model instance ⇄ JSON |
| 7 | Exposed full CRUD | `AuthorViewSet` + `DefaultRouter` | Six endpoints from ten lines |
| 8 | Added JWT auth | `accounts` app: register, login, refresh, verify, logout, me | Access + refresh tokens |
| 9 | Generated the OpenAPI schema | `drf-spectacular` | `/api/schema/`, `/api/docs/`, `/api/redoc/` |

Everything below runs against what is in this repository, starting from `main` at the end of Day 2 — a `blog` app with an `Author` model mapped to the `authors` table, and nothing else.

## Conventions

Same as Day 1 and Day 2.

| Marker | Meaning |
| --- | --- |
| **TYPE** | Type this exactly. |
| **EXPECT** | What should appear. If you see something else, stop and fix it. |
| **CHECKPOINT** | A verifiable state. Nobody moves on until everyone reaches it. |
| **WHY** | The reasoning. Read it before the exam. |
| **DOCS** | The official documentation for what you just did. |

Django links point at `/en/5.2/`, matching `requirements.txt`. Today adds three more documentation sites — DRF, Simple JWT and drf-spectacular — all indexed in Appendix B.

## Start here

**TYPE**

```bash
cd ~/code/django-lab
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
git switch main
git pull origin main
git switch -c <first_name>/day3
```

**TYPE**

```bash
python manage.py migrate
python manage.py runserver
```

**EXPECT** — the server starts, and <http://127.0.0.1:8000/admin/> lists **Authors**. If it does not, your Day 2 work is not on `main` yet; fix that before going further.

**CHECKPOINT 0** — you are on branch `<first_name>/day3`, `migrate` is clean, and you can log into `/admin/` and see the `Author` rows you created yesterday. Create two or three if the list is empty — today is about displaying them.

Stop the server with `Ctrl-C` before the next part.

\newpage

# Part 1 — From a table to a page

Day 2 ended with a model, a migration and a table. What it did **not** produce was any way for a person without a database client to look at the data. `/admin/` is not that way — it is a staff tool, behind a login, and it is not your application.

Today closes that gap twice over: once with HTML for humans, once with JSON for programs.

## 1.1 The request/response cycle

Everything Django does is one function: an `HttpRequest` goes in, an `HttpResponse` comes out. Every layer between those two is optional.

```
Browser
   |  GET /
   v
config/urls.py            <- the ROOT URLconf (Day 2, Part 3)
   |  matches "" -> include("blog.urls")
   v
blog/urls.py              <- the app URLconf
   |  matches "" -> views.author_list
   v
blog/views.py             <- YOUR function. Receives HttpRequest.
   |  Author.objects.order_by("name")   -> the ORM issues SQL
   v
blog/templates/blog/author_list.html
   |  rendered with {"authors": <QuerySet>}
   v
HttpResponse (status 200, Content-Type: text/html)
   |
   v
Browser
```

> **DOCS** — [Writing views](https://docs.djangoproject.com/en/5.2/topics/http/views/) · [Request and response objects](https://docs.djangoproject.com/en/5.2/ref/request-response/) · [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/)

## 1.2 MVT, and why it is not MVC

Django calls its pattern **MVT**. The names differ from MVC in one confusing place, so learn the mapping once:

| Django calls it | It is | Lives in | In classic MVC this is |
| --- | --- | --- | --- |
| **Model** | The data and its rules | `blog/models.py` | Model |
| **Template** | The presentation | `blog/templates/blog/*.html` | View |
| **View** | The request handler that picks data and a template | `blog/views.py` | Controller |

A Django "view" is not a page. It is a **function that answers a request**. Say that out loud once; it removes most of the confusion in the next two hours.

> **DOCS** — [FAQ: Django appears to be an MVC framework](https://docs.djangoproject.com/en/5.2/faq/general/#django-appears-to-be-a-mvc-framework-but-you-call-the-controller-the-view-and-the-view-the-template-how-come-you-don-t-use-the-standard-names)

## 1.3 Two small fixes to the model first

Open `blog/models.py`. Yesterday's version works, but two things are missing that everything today would expose.

**TYPE** — replace the file with:

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = "authors"
        ordering = ["name"]

    def __str__(self):
        return self.name
```

**WHY `__str__`** — without it, the admin, the shell and every error message show `Author object (1)`. With it they show the name. It costs two lines and it is the single highest-value method on any Django model. Day 2, Part 6 covered this; if your Day 2 branch never got it, this is where it lands.

**WHY `ordering`** — a `SELECT` with no `ORDER BY` returns rows in whatever order the database finds convenient. That order is not random, but it is *not guaranteed*, and it changes when rows are updated. Once you paginate an API — which you will in Part 4 — an unordered queryset means page 2 can repeat a row from page 1 and skip another entirely. `ordering = ["name"]` makes the default deterministic. DRF will warn you about exactly this if you skip it.

> **DOCS** — [`Model.__str__()`](https://docs.djangoproject.com/en/5.2/ref/models/instances/#django.db.models.Model.__str__) · [`Meta.ordering`](https://docs.djangoproject.com/en/5.2/ref/models/options/#ordering) · [`order_by()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#order-by)

**TYPE**

```bash
python manage.py makemigrations blog
```

**EXPECT**

```
Migrations for 'blog':
  blog/migrations/0002_alter_author_options.py
    ~ Change Meta options on author
```

**TYPE** — read it before applying, as always:

```bash
python manage.py sqlmigrate blog 0002
```

**EXPECT** — no SQL statements. The command succeeds and prints nothing meaningful.

**WHY the SQL is empty** — `ordering` and `__str__` do not exist in the database. Ordering is applied by the ORM when it builds each query; `__str__` is pure Python. Django still records the change as a migration so that every developer's *model state* stays in lockstep — a later migration that depends on today's options needs this row in `django_migrations` to exist. This is the clearest example all week of the difference between **model state** and **database schema**. Migrations track both; only some of them touch SQL.

> **DOCS** — [`AlterModelOptions`](https://docs.djangoproject.com/en/5.2/ref/migration-operations/#altermodeloptions) · [Migrations topic guide](https://docs.djangoproject.com/en/5.2/topics/migrations/)

**TYPE**

```bash
python manage.py migrate
```

**EXPECT** — `Applying blog.0002_alter_author_options... OK`

**CHECKPOINT 1** — `python manage.py showmigrations blog` shows two `[X]` lines.

\newpage

# Part 2 — Render the list of authors

## 2.1 Make sure there is something to render

**TYPE**

```bash
python manage.py shell
```

Then, at the `>>>` prompt:

```python
from blog.models import Author
Author.objects.bulk_create([
    Author(name="Chinua Achebe", bio="Nigerian novelist."),
    Author(name="Ursula K. Le Guin", bio="American author."),
    Author(name="Arundhati Roy", bio=""),
])
Author.objects.count()
```

**EXPECT** — a number of at least 3. Leave the shell with `exit()`.

Note the third author has an empty `bio`. That is deliberate — Part 2.5 uses it.

> **DOCS** — [Making queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/) · [`bulk_create()`](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#bulk-create)

## 2.2 Write the views

`blog/views.py` has been an empty stub since Day 2. Replace it.

**TYPE**

```python
from django.shortcuts import get_object_or_404, render

from .models import Author


def author_list(request):
    authors = Author.objects.order_by("name")
    return render(request, "blog/author_list.html", {"authors": authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    return render(request, "blog/author_detail.html", {"author": author})
```

**WHY `render()`** — it is a shortcut for three steps: load the template, render it with a context dictionary, and wrap the resulting string in an `HttpResponse`. You could write those three lines yourself; nobody does.

**WHY the queryset does not hit the database here** — `Author.objects.order_by("name")` returns a `QuerySet`, not a list. Nothing is executed. The SQL runs at the moment the template's `{% for %}` loop starts iterating. This laziness is why you can pass a queryset around, filter it further, and slice it, all without a single query. It is also why a query that "works in the view" can explode in the template: that is where it actually runs.

**WHY `get_object_or_404` and not `Author.objects.get(pk=pk)`** — `get()` raises `Author.DoesNotExist`, which is an unhandled exception and therefore a **500 Server Error**. A missing author is not a server fault; it is a **404 Not Found**. The shortcut raises `Http404`, which Django turns into the right status code and the right page. Using the wrong one lies to your monitoring and to search engines.

> **DOCS** — [`render()`](https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/#render) · [`get_object_or_404()`](https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/#get-object-or-404) · [QuerySets are lazy](https://docs.djangoproject.com/en/5.2/topics/db/queries/#querysets-are-lazy)

## 2.3 Give the app its own URLconf

Day 2, Part 3.3 showed you what today's wiring would look like. Here it is for real.

**TYPE** — `blog/urls.py`:

```python
from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.author_list, name="author-list"),
    path("authors/<int:pk>/", views.author_detail, name="author-detail"),
]
```

**TYPE** — `config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("blog.urls")),
]
```

**WHY `include()` and not listing the views in `config/urls.py`** — the app owns its URLs. Move `blog/` into another project and its routes travel with it; the new project decides only the prefix. That is what makes a Django app reusable.

**WHY `app_name = "blog"`** — it namespaces the route names. `{% url 'blog:author-detail' 3 %}` can never collide with a `shop:author-detail` added next month. Without `app_name`, the second app to define `author-detail` silently wins, and the bug shows up as a link pointing at the wrong page.

**WHY `<int:pk>` and not `<pk>`** — the `int` converter does two jobs. It refuses to match `/authors/abc/` at the URL layer, so your view never runs with garbage, and it hands `pk` to the view as a Python `int` rather than a string. Path converters are validation you get for free.

**WHY the order in `urlpatterns` matters** — Django tries each pattern top to bottom and stops at the first match. `path("", ...)` matches only the empty path, so it is safe first here, but a catch-all pattern placed above a specific one would shadow it permanently.

> **DOCS** — [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/) · [`include()`](https://docs.djangoproject.com/en/5.2/ref/urls/#include) · [Path converters](https://docs.djangoproject.com/en/5.2/topics/http/urls/#path-converters) · [URL namespaces](https://docs.djangoproject.com/en/5.2/topics/http/urls/#url-namespaces)

## 2.4 Write the templates

`startapp` does not create a templates directory. Make it, with the repeated app name explained on Day 2.

**TYPE**

```bash
mkdir -p blog/templates/blog
```

**TYPE** — `blog/templates/blog/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{% block title %}Django Lab{% endblock %}</title>
</head>
<body>
  <h1>Django Lab — Blog</h1>
  {% block content %}{% endblock %}
</body>
</html>
```

**TYPE** — `blog/templates/blog/author_list.html`:

```html
{% extends "blog/base.html" %}

{% block title %}Authors{% endblock %}

{% block content %}
  <h2>Authors ({{ authors|length }})</h2>

  <ul>
    {% for author in authors %}
      <li>
        <a href="{% url 'blog:author-detail' author.pk %}">{{ author.name }}</a>
      </li>
    {% empty %}
      <li>No authors yet. Add one in <a href="/admin/">the admin</a>.</li>
    {% endfor %}
  </ul>
{% endblock %}
```

**TYPE** — `blog/templates/blog/author_detail.html`:

```html
{% extends "blog/base.html" %}

{% block title %}{{ author.name }}{% endblock %}

{% block content %}
  <h2>{{ author.name }}</h2>
  <p>{{ author.bio|default:"No bio yet." }}</p>
  <p><a href="{% url 'blog:author-list' %}">Back to all authors</a></p>
{% endblock %}
```

### The four template constructs you just used

| Syntax | Name | What it does |
| --- | --- | --- |
| `{{ author.name }}` | Variable | Prints a value, **HTML-escaped** |
| `{% for %}` / `{% empty %}` | Tag | Loops; `{% empty %}` runs when the sequence is empty |
| `{{ author.bio` \| `default:"..." }}` | Filter | Transforms a value before printing |
| `{% extends %}` / `{% block %}` | Inheritance | Child fills the parent's named holes |

**WHY `{% url %}` instead of typing `/authors/3/`** — the template asks the URLconf to build the path from the route *name*. Change `authors/<int:pk>/` to `writers/<int:pk>/` tomorrow and every `{% url %}` follows; every hardcoded href becomes a 404. There is no cost to using it, and the cost of not using it arrives later, in someone else's sprint.

**WHY escaping matters** — set an author's bio to `<script>alert(1)</script>` in the admin and reload the detail page. You will see the tags as text, not a popup. Django escapes every variable by default; that default is the reason Django apps are not routinely XSS-vulnerable. The `|safe` filter turns it off — reach for it only when you produced the HTML yourself.

**WHY template inheritance and not an include** — `{% extends %}` inverts control. The child template does not describe the page; it fills the holes the parent left. One `base.html` change restyles every page in the app.

**WHY the dot in `{{ author.name }}` is not attribute access** — Django tries, in order: dictionary lookup `author["name"]`, attribute lookup `author.name`, then list-index lookup. And if the attribute is callable it *calls* it, with no arguments. That is why `{{ author.get_absolute_url }}` works without parentheses — and why a method with required arguments cannot be used from a template.

> **DOCS** — [Templates topic guide](https://docs.djangoproject.com/en/5.2/topics/templates/) · [Template language](https://docs.djangoproject.com/en/5.2/ref/templates/language/) · [Built-in tags and filters](https://docs.djangoproject.com/en/5.2/ref/templates/builtins/) · [Automatic HTML escaping](https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping) · [Template inheritance](https://docs.djangoproject.com/en/5.2/ref/templates/language/#template-inheritance)

## 2.5 See it

**TYPE**

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

**EXPECT**

```
Django Lab — Blog

Authors (3)
  • Arundhati Roy
  • Chinua Achebe
  • Ursula K. Le Guin
```

Alphabetical, because of `Meta.ordering`. Click a name.

**EXPECT** — the detail page. **Arundhati Roy** shows *No bio yet.* — that is the `default:` filter, firing because `bio` is `""`.

**CHECKPOINT 2** — `/` lists your Day 2 authors, each name links to `/authors/<id>/`, and `/authors/999/` returns a **404** page rather than a yellow error screen. Test that last one; it is the whole point of `get_object_or_404`.

\newpage

# Part 3 — Install the API stack

The HTML pages serve humans. The rest of today serves programs — a mobile app, a React frontend, another service. Same model, same database, different representation.

## 3.1 Install

**TYPE**

```bash
pip install djangorestframework djangorestframework-simplejwt drf-spectacular
```

**EXPECT** — a `Successfully installed` line naming those three plus their dependencies (`PyJWT`, `PyYAML`, `jsonschema`, `inflection`, `uritemplate` and friends).

| Package | What it gives you |
| --- | --- |
| `djangorestframework` | Serializers, viewsets, routers, permissions, the browsable API |
| `djangorestframework-simplejwt` | JSON Web Token authentication: obtain, refresh, verify, blacklist |
| `drf-spectacular` | Generates an OpenAPI 3 schema from your code, and serves Swagger UI / ReDoc |

## 3.2 Pin them

**TYPE**

```bash
pip freeze > requirements.txt
cat requirements.txt
```

**EXPECT** — something close to this. Exact versions will drift; that is fine, and it is precisely why the file is pinned:

```
asgiref==3.12.1
attrs==26.1.0
Django==5.2.17
djangorestframework==3.18.0
djangorestframework_simplejwt==5.5.1
drf-spectacular==0.30.0
inflection==0.5.1
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
PyJWT==2.13.0
PyYAML==6.0.3
referencing==0.37.0
rpds-py==2026.6.3
sqlparse==0.6.0
uritemplate==4.2.0
```

**WHY freeze the transitive dependencies too** — `pip freeze` records the whole resolved tree, not just what you asked for. Six months from now, a new `PyJWT` with a changed default could break token verification on a machine that installed from an unpinned file. The pinned file is the difference between "works on my laptop" and "works".

## 3.3 Register the apps

Open `config/settings.py`. Add the import at the top:

```python
from datetime import timedelta
from pathlib import Path
```

Then extend `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',

    # user-defined apps
    'accounts',
    'blog',
]
```

`accounts` does not exist yet — you create it in Part 5. Django will refuse to start until then, which is a useful reminder that `INSTALLED_APPS` is loaded eagerly. If you would rather not have a broken tree in between, add `'accounts'` at the start of Part 5 instead.

**WHY `token_blacklist` is a separate app** — it ships two models (`OutstandingToken`, `BlacklistedToken`) and therefore its own migrations. JWTs are stateless by design; blacklisting is the deliberate exception that buys you a working logout, and it costs a database table. Simple JWT makes you opt in.

## 3.4 Configure DRF

Append to the bottom of `config/settings.py`:

```python
# Django REST Framework
# https://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
```

| Setting | Why it is set this way |
| --- | --- |
| `DEFAULT_AUTHENTICATION_CLASSES` | JWT first for API clients; session second so the browsable API still works while you are logged into `/admin/` |
| `DEFAULT_PERMISSION_CLASSES` | **Deny by default.** Every endpoint requires a logged-in user unless it explicitly opts out |
| `DEFAULT_SCHEMA_CLASS` | Hands schema generation to drf-spectacular instead of DRF's deprecated built-in |
| `DEFAULT_PAGINATION_CLASS` / `PAGE_SIZE` | A list endpoint with no pagination will one day try to serialize the whole table |

**WHY deny by default** — the alternative is `AllowAny` globally plus a permission class on every view. Forget one and you have leaked data, silently, with a passing test suite. With `IsAuthenticated` as the default, forgetting produces a `401` — loud, immediate, and caught in the first manual test. Make the failure mode noisy.

**WHY authentication and permission are two different things** — authentication answers *who are you* and sets `request.user`. Permission answers *may you do this*. An anonymous request is authenticated perfectly well as `AnonymousUser`; it just fails the permission check. Two questions, two settings, two failure codes (`401` vs `403`).

> **DOCS** — [DRF settings](https://www.django-rest-framework.org/api-guide/settings/) · [Authentication](https://www.django-rest-framework.org/api-guide/authentication/) · [Permissions](https://www.django-rest-framework.org/api-guide/permissions/) · [Pagination](https://www.django-rest-framework.org/api-guide/pagination/)

## 3.5 Configure Simple JWT

Append:

```python
# Simple JWT
# https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'SIGNING_KEY': SECRET_KEY,
}
```

**WHY two tokens with different lifetimes** — the **access** token is sent on every single request, so it is the one most likely to leak (a log file, a proxy, a browser extension). Keeping it short-lived caps the damage at 30 minutes. The **refresh** token is sent only to `/api/auth/refresh/`, rarely, so it can live longer without the same exposure.

**WHY rotation plus blacklist** — with `ROTATE_REFRESH_TOKENS`, each refresh hands back a *new* refresh token; with `BLACKLIST_AFTER_ROTATION`, the old one is recorded as spent. If an attacker steals a refresh token and uses it, the legitimate user's next refresh fails — you get a detectable signal instead of a silent, permanent compromise. You will see this fire in Part 5.6.

**WHY `SIGNING_KEY = SECRET_KEY` is a lab-only choice** — it works, and it is Simple JWT's default. In production, rotating `SECRET_KEY` would then invalidate every session *and* every token at once, and any component that needs to verify tokens would need your Django secret. Real deployments give JWTs their own key, or use asymmetric `RS256` so verifiers only ever hold a public key.

> **DOCS** — [Simple JWT settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html) · [Blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html) · [`SECRET_KEY`](https://docs.djangoproject.com/en/5.2/ref/settings/#secret-key)

## 3.6 Migrate the blacklist tables

**TYPE**

```bash
python manage.py migrate
```

**EXPECT** — a run of `Applying token_blacklist.00NN_...` lines.

**CHECKPOINT 3** — `python manage.py check` reports no issues (once `accounts` exists), and `showmigrations token_blacklist` is all `[X]`.

\newpage

# Part 4 — The Author API

## 4.1 The serializer

A serializer is to an API what a `ModelForm` is to an HTML page: it validates incoming data and converts model instances to a wire format. Forms speak HTML and POST bodies; serializers speak JSON.

**TYPE** — `blog/serializers.py` (a new file):

```python
from rest_framework import serializers

from .models import Author


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ["id", "name", "bio"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Name cannot be blank.")
        return name
```

**WHY list `fields` explicitly instead of `fields = "__all__"`** — `__all__` means "whatever the model has *today*". Add a `password_reset_token` or an `internal_notes` field to the model next month and it is published to the internet the moment you save the file. An explicit list makes exposure a decision, not an accident. This is the single most common serious mistake in DRF codebases.

**WHY `validate_<field>` returns a value** — DRF calls it during `is_valid()` and stores whatever you return. So it is a validation hook *and* a normalisation hook: the `.strip()` above means `"  Achebe  "` is saved as `"Achebe"`. Raise `ValidationError` to reject; return a value to accept, possibly a cleaned one.

**WHY the model's `blank=True` on `bio` already works here** — `ModelSerializer` reads the model field's attributes and maps them: `blank=True` becomes `required=False`, `max_length=100` becomes a length validator. You inherit Day 2's model definition rather than restating it.

> **DOCS** — [Serializers](https://www.django-rest-framework.org/api-guide/serializers/) · [`ModelSerializer`](https://www.django-rest-framework.org/api-guide/serializers/#modelserializer) · [Validators](https://www.django-rest-framework.org/api-guide/validators/)

## 4.2 The viewset

**TYPE** — `blog/api.py` (a new file):

```python
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Author
from .serializers import AuthorSerializer


@extend_schema_view(
    list=extend_schema(summary="List authors", description="Public. Supports ?search= on name and bio."),
    retrieve=extend_schema(summary="Retrieve one author"),
    create=extend_schema(summary="Create an author", description="Requires a Bearer access token."),
    update=extend_schema(summary="Replace an author"),
    partial_update=extend_schema(summary="Update some fields of an author"),
    destroy=extend_schema(summary="Delete an author"),
)
class AuthorViewSet(viewsets.ModelViewSet):
    """CRUD for `blog.Author`, backed by the `authors` table."""

    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "bio"]
    ordering_fields = ["id", "name"]
```

**WHY a separate `api.py` and not `views.py`** — `blog/views.py` already holds the HTML views. Nothing forces the split, but keeping "returns HTML" and "returns JSON" in different modules means a reader can tell which layer they are in from the import line. Larger projects promote this to a `blog/api/` package.

**WHY `ModelViewSet` and not six separate view classes** — it is exactly those six, grouped:

| ViewSet action | Method | URL | Does |
| --- | --- | --- | --- |
| `list` | `GET` | `/api/authors/` | Paginated list |
| `create` | `POST` | `/api/authors/` | Create one |
| `retrieve` | `GET` | `/api/authors/{id}/` | Fetch one |
| `update` | `PUT` | `/api/authors/{id}/` | Replace one — all fields required |
| `partial_update` | `PATCH` | `/api/authors/{id}/` | Update some fields |
| `destroy` | `DELETE` | `/api/authors/{id}/` | Delete one |

**WHY `IsAuthenticatedOrReadOnly` here** — it overrides the global `IsAuthenticated` for this viewset only. Anyone may read the author list; only an authenticated user may change it. The class works by allowing the *safe* methods (`GET`, `HEAD`, `OPTIONS`) unconditionally and requiring a user for everything else.

**WHY `queryset` is a class attribute and not a call** — `Author.objects.all()` is lazy, so no query runs at import time; DRF clones and re-evaluates it per request. If you need per-user filtering, override `get_queryset()` instead — a class attribute is evaluated once and cannot see `request`.

**WHY `search_fields` and `ordering_fields`** — they turn `?search=le+guin` and `?ordering=-name` into `icontains` filters and `ORDER BY` clauses. `ordering_fields` is an allowlist: a client cannot sort by a column you did not name, which stops `?ordering=password` from becoming an oracle.

> **DOCS** — [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/) · [Generic views](https://www.django-rest-framework.org/api-guide/generic-views/) · [Filtering](https://www.django-rest-framework.org/api-guide/filtering/) · [`IsAuthenticatedOrReadOnly`](https://www.django-rest-framework.org/api-guide/permissions/#isauthenticatedorreadonly)

## 4.3 Route it

**TYPE** — replace `config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from blog.api import AuthorViewSet

router = DefaultRouter()
router.register("authors", AuthorViewSet, basename="author")

urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML pages
    path("", include("blog.urls")),

    # JSON API
    path("api/", include(router.urls)),
]
```

**WHY a router** — it reads the viewset and generates the URL patterns and their names. Two lines replace twelve `path()` calls, and the names it produces (`author-list`, `author-detail`) follow one convention across every resource you ever add.

**WHY `basename="author"`** — the router derives route names from the queryset's model unless you say otherwise. Being explicit is required the moment a viewset defines `get_queryset()` instead of `queryset`, and it never hurts.

**WHY the API sits under `/api/`** — the blog URLconf is mounted at `""`, so it would happily match `authors/` too. Prefixes keep the two namespaces from ever competing, and they make it trivial to put the API behind different middleware, rate limits or a CDN rule later.

> **DOCS** — [Routers](https://www.django-rest-framework.org/api-guide/routers/)

## 4.4 Try it

**TYPE**

```bash
python manage.py runserver
```

In a **second terminal** (leave the server running):

```bash
curl -s http://127.0.0.1:8000/api/authors/
```

**EXPECT**

```json
{"count":3,"next":null,"previous":null,"results":[
  {"id":3,"name":"Arundhati Roy","bio":""},
  {"id":1,"name":"Chinua Achebe","bio":"Nigerian novelist."},
  {"id":2,"name":"Ursula K. Le Guin","bio":"American author."}]}
```

That `count / next / previous / results` envelope is `PageNumberPagination` doing its job.

**TYPE** — now try to create one without logging in:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/api/authors/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Nope"}'
```

**EXPECT**

```
401
```

**CHECKPOINT 4** — reading is public, writing returns `401`. Also open <http://127.0.0.1:8000/api/authors/> in a browser: DRF's **browsable API** renders the same endpoint as an HTML page you can click through. It is the same view; only the `Accept` header differs.

> **DOCS** — [The browsable API](https://www.django-rest-framework.org/topics/browsable-api/) · [Content negotiation](https://www.django-rest-framework.org/api-guide/content-negotiation/)

\newpage

# Part 5 — JWT: register, login, refresh, logout

`401` is correct, but right now there is no way to *stop* being anonymous over the API. That is what this part builds.

## 5.1 What a JWT actually is

A JSON Web Token is three base64url chunks joined by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 . eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwi... . lv7ghOxSHLwhN3Iy...
             header                              payload                          signature

header    {"alg":"HS256","typ":"JWT"}
payload   {"token_type":"access","exp":1787810435,"user_id":"1","username":"amina"}
signature HMAC-SHA256 over the first two parts, keyed with SIGNING_KEY
```

Paste one into <https://jwt.io> and read it. Three facts follow immediately, and they are the three that get people into trouble:

1. **The payload is encoded, not encrypted.** Anyone holding the token can read every claim. Never put anything secret in it — no password hash, no card number, no private email if the token may reach a browser's local storage.
2. **The signature is the only thing that matters.** Change one byte of the payload and the signature no longer verifies. That is why the server does not need to store the token to trust it.
3. **Stateless means un-revokable.** Nothing consults the database on each request, so there is no row to delete when a user logs out. The token stays valid until `exp`. That is the whole reason the blacklist app exists.

> **DOCS** — [Simple JWT overview](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/) · [Token types](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/token_types.html) · [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519)

## 5.2 Create the accounts app

**TYPE**

```bash
python manage.py startapp accounts
```

If you have not already added `'accounts'` to `INSTALLED_APPS` (3.3), do it now.

**WHY a separate app rather than putting this in `blog`** — authentication is not blogging. `accounts` will grow password reset, email verification and profile endpoints; none of that belongs next to `Author`. This is the same project/app boundary lesson as Day 2, applied a second time so it sticks.

## 5.3 The serializers

**TYPE** — `accounts/serializers.py`:

```python
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"email": {"required": True}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_staff"]
        read_only_fields = fields


class LoginSerializer(TokenObtainPairSerializer):
    """`TokenObtainPairSerializer` plus the user it just authenticated."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LoginResponseSerializer(serializers.Serializer):
    """Documents what `LoginView` returns. Never used to parse input."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
```

**WHY `get_user_model()` and never `from django.contrib.auth.models import User`** — a project can swap in a custom user model via `AUTH_USER_MODEL`, and many do by month three. Code that imports `User` directly breaks on that day; code that calls `get_user_model()` does not. Treat the direct import as a bug on sight.

**WHY `write_only=True` on `password`** — without it, DRF would include `password` in the *output* representation and the register response would echo the password back. `write_only` means "accept it, never return it".

**WHY `create_user()` and not `User.objects.create()`** — `create()` stores the string you give it verbatim, so the database ends up with a plaintext password and every login fails. `create_user()` runs it through `set_password()`, which hashes with PBKDF2. This is a real bug that ships regularly.

**WHY `validators=[validate_password]`** — it applies the `AUTH_PASSWORD_VALIDATORS` already sitting in `settings.py` since Day 1: minimum length, not too common, not all numeric, not similar to the username. The API and `createsuperuser` now enforce identical rules.

**WHY `email__iexact`** — `Alice@example.com` and `alice@example.com` are the same mailbox to every mail server on earth. A plain `=` comparison would let both register and produce two accounts nobody can tell apart.

**WHY subclass `TokenObtainPairSerializer` at all** — the stock one returns `{"access": ..., "refresh": ...}` and nothing else, so the client has to make a second call just to learn who it is. `validate()` adds the user; `get_token()` adds a `username` claim inside the token itself. Do not put anything sensitive in that claim — see 5.1, point 1.

**WHY `LoginResponseSerializer` exists when nothing parses it** — it is documentation, and Part 6.4 explains what breaks without it.

> **DOCS** — [`get_user_model()`](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#django.contrib.auth.get_user_model) · [Password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/) · [`AUTH_PASSWORD_VALIDATORS`](https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators) · [Customising token claims](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/customizing_token_claims.html)

## 5.4 The views

**TYPE** — `accounts/views.py`:

```python
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema(
    summary="Register a new user",
    description="Creates a user and returns it. Log in afterwards to get tokens.",
    responses={201: UserSerializer},
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Log in and get a token pair",
    description="Exchanges username + password for an `access` token and a `refresh` token.",
    responses={200: LoginResponseSerializer},
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


@extend_schema(
    summary="Who am I",
    description="Returns the user identified by the Bearer access token.",
    responses={200: UserSerializer},
)
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    summary="Log out",
    description="Blacklists the supplied refresh token so it can no longer be exchanged.",
    request=TokenBlacklistSerializer,
    responses={205: OpenApiResponse(description="Refresh token blacklisted")},
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"refresh": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response({"detail": "Token is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)
```

**WHY `RegisterView` must set `permission_classes = [AllowAny]`** — the global default is `IsAuthenticated`. Without this line, registering would require already being logged in. Deny-by-default means every public endpoint declares itself, which is exactly the audit trail you want.

**WHY `create()` is overridden** — the request is validated by `RegisterSerializer`, but the *response* is rendered by `UserSerializer`. Different serializers for input and output is a normal, healthy pattern; the input one knows about passwords and the output one does not.

**WHY `MeView` overrides `get_object()`** — a `RetrieveAPIView` normally looks up by a URL keyword. Here the identity comes from the token, so `request.user` *is* the object. Note there is no queryset and no `pk` in the URL — a user can only ever read themselves.

**WHY logout takes a refresh token and returns 205** — logging out means "make my refresh token unusable"; blacklisting the refresh token is the only durable part of the operation. The access token keeps working until it expires (up to 30 minutes), which surprises everyone the first time. If you need instant revocation, you need a stateful check on every request — and then you have given up most of what JWT is for. `205 Reset Content` tells the client to clear its stored state.

**WHY `except TokenError`** — an expired, malformed or already-blacklisted token raises it. Unhandled, that is a `500`. A bad token supplied by the client is a `400`.

> **DOCS** — [Generic views](https://www.django-rest-framework.org/api-guide/generic-views/) · [`APIView`](https://www.django-rest-framework.org/api-guide/views/) · [Blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html)

## 5.5 The URLs

**TYPE** — `accounts/urls.py`:

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import LoginView, LogoutView, MeView, RegisterView

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("verify/", TokenVerifyView.as_view(), name="verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
```

`TokenRefreshView` and `TokenVerifyView` come straight from Simple JWT — there is nothing project-specific about them, so there is nothing to subclass.

**TYPE** — add one line to `config/urls.py`, under the API section:

```python
    path("api/", include(router.urls)),
    path("api/auth/", include("accounts.urls")),
```

## 5.6 Walk the whole flow

Restart `runserver`. In the second terminal:

**TYPE** — register, deliberately with a bad password first:

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"amina","email":"amina@example.com","password":"pass"}'
```

**EXPECT**

```json
{"password":["This password is too short. It must contain at least 8 characters.",
             "This password is too common."]}
```

That is `AUTH_PASSWORD_VALIDATORS` from Day 1, reaching the API for free.

**TYPE** — now properly:

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"amina","email":"amina@example.com","password":"Str0ng-Lab-Pass"}'
```

**EXPECT**

```json
{"id":1,"username":"amina","email":"amina@example.com","is_staff":false}
```

No password in the response — that is `write_only=True`.

**TYPE** — log in:

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"amina","password":"Str0ng-Lab-Pass"}'
```

**EXPECT**

```json
{"refresh":"eyJhbGciOiJIUzI1NiIs...","access":"eyJhbGciOiJIUzI1NiIs...",
 "user":{"id":1,"username":"amina","email":"amina@example.com","is_staff":false}}
```

Copy the values into shell variables — you will use them several times:

```bash
ACCESS="<paste the access token>"
REFRESH="<paste the refresh token>"
```

**TYPE** — identify yourself:

```bash
curl -s http://127.0.0.1:8000/api/auth/me/ -H "Authorization: Bearer $ACCESS"
```

**EXPECT**

```json
{"id":1,"username":"amina","email":"amina@example.com","is_staff":false}
```

**TYPE** — the write that returned `401` in Part 4.4:

```bash
curl -s -X POST http://127.0.0.1:8000/api/authors/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"name":"Amina Author","bio":"Created over the API."}'
```

**EXPECT**

```json
{"id":4,"name":"Amina Author","bio":"Created over the API."}
```

**TYPE** — check the search filter picked it up:

```bash
curl -s "http://127.0.0.1:8000/api/authors/?search=amina"
```

**EXPECT** — `"count":1` and that one author.

Reload <http://127.0.0.1:8000/> in the browser. The author created over the API is in the HTML list. **One model, one table, two representations** — that is the sentence to take away from today.

**TYPE** — refresh, then try to reuse the old refresh token:

```bash
curl -s -X POST http://127.0.0.1:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" -d "{\"refresh\":\"$REFRESH\"}"

curl -s -X POST http://127.0.0.1:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" -d "{\"refresh\":\"$REFRESH\"}"
```

**EXPECT** — the first returns a fresh `access` **and** a fresh `refresh`. The second returns:

```json
{"detail":"Token is blacklisted","code":"token_not_valid"}
```

That is `ROTATE_REFRESH_TOKENS` plus `BLACKLIST_AFTER_ROTATION` from 3.5. A refresh token is single-use.

**CHECKPOINT 5** — you can register, log in, read `/api/auth/me/`, create an author with a Bearer token, see it on the HTML page, and you have watched a reused refresh token get rejected.

\newpage

# Part 6 — OpenAPI docs with drf-spectacular

You now have eight endpoints. Nobody outside this room knows they exist. An OpenAPI schema is a machine-readable description of every route, parameter, request body and response — and it is generated from the code, so it cannot drift the way a hand-written wiki page does.

## 6.1 Configure it

Append to `config/settings.py`:

```python
# drf-spectacular
# https://drf-spectacular.readthedocs.io/en/latest/settings.html

SPECTACULAR_SETTINGS = {
    'TITLE': 'Django Lab API',
    'DESCRIPTION': 'Authors, plus JWT registration and login. Built on Day 3 of the lab.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True},
}
```

| Setting | Why |
| --- | --- |
| `SERVE_INCLUDE_SCHEMA` | Keeps `/api/schema/` itself out of the schema it serves |
| `COMPONENT_SPLIT_REQUEST` | Separate request and response components, so `write_only` fields like `password` appear only on the request side |
| `SCHEMA_PATH_PREFIX` | Strips `/api/` when deriving tags, so operations group as `authors` and `auth` rather than `api` |
| `SWAGGER_UI_SETTINGS` | `persistAuthorization` keeps your token across page reloads — worth its weight during a live demo |

`DEFAULT_SCHEMA_CLASS` was already set back in 3.4; that is the line that actually hands generation to spectacular.

## 6.2 Serve the schema and the two UIs

**TYPE** — final `config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from blog.api import AuthorViewSet

router = DefaultRouter()
router.register("authors", AuthorViewSet, basename="author")

urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML pages
    path("", include("blog.urls")),

    # JSON API
    path("api/", include(router.urls)),
    path("api/auth/", include("accounts.urls")),

    # OpenAPI schema and docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
```

| URL | Serves |
| --- | --- |
| `/api/schema/` | The raw OpenAPI 3 document, as YAML |
| `/api/docs/` | **Swagger UI** — interactive; you can call endpoints from the page |
| `/api/redoc/` | **ReDoc** — three-pane reference; better for reading, no request button |

**WHY both UIs read `url_name="schema"`** — they fetch the same document from the same route by name. One source of truth; the two pages are only renderers.

## 6.3 Validate it from the command line

**TYPE**

```bash
python manage.py spectacular --file schema.yml --validate --fail-on-warn
```

**EXPECT** — no output, exit status 0. Any warning is a real gap in your documentation and this flag turns it into a failure, which is what makes the command useful in CI.

**TYPE**

```bash
grep -E '^  /' schema.yml
```

**EXPECT**

```
  /api/auth/login/:
  /api/auth/logout/:
  /api/auth/me/:
  /api/auth/refresh/:
  /api/auth/register/:
  /api/auth/verify/:
  /api/authors/:
  /api/authors/{id}/:
```

Eight paths, all generated from the code you wrote. Delete `schema.yml` afterwards — it is a build artefact, not source, and it does not get committed.

## 6.4 The gap `extend_schema` exists to close

Try this experiment. Comment out the `responses={200: LoginResponseSerializer}` line in `accounts/views.py`, regenerate, and look at the login operation:

```yaml
      responses:
        '200':
          description: No response body
```

Wrong — login returns three fields. Spectacular inspects your serializer class to work out the shape, and `LoginSerializer` declares `username` and `password` as *inputs*; the `access`, `refresh` and `user` keys are assembled inside `validate()`, which is ordinary Python that no static inspection can read.

Put the line back and regenerate:

```yaml
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
```

**WHY this is the lesson of the part** — schema generation is inference, and inference has limits. It reads types, serializers and querysets very well. It cannot read your intent. `@extend_schema` is how you supply the part it cannot deduce: response shapes built by hand, status codes you return directly, and endpoints whose request body has no serializer. The summaries you wrote in `blog/api.py` and `accounts/views.py` are the same mechanism used for prose instead of types.

> **DOCS** — [drf-spectacular](https://drf-spectacular.readthedocs.io/en/latest/) · [`@extend_schema`](https://drf-spectacular.readthedocs.io/en/latest/drf_spectacular.html#drf_spectacular.utils.extend_schema) · [Workflow and customisation](https://drf-spectacular.readthedocs.io/en/latest/customization.html) · [OpenAPI specification](https://spec.openapis.org/oas/latest.html)

\newpage

# Part 7 — Drive the whole API from Swagger UI

Close the terminal for a minute and do it all again in the browser. This is the version you will demo to somebody.

1. Open <http://127.0.0.1:8000/api/docs/>. Two tag groups: **auth** and **authors**.
2. Expand `POST /api/auth/register/` → **Try it out** → edit the JSON body → **Execute**. Register a second user.
3. Expand `POST /api/auth/login/` → **Try it out** → log in as that user → copy the `access` value out of the response.
4. Click the **Authorize** button at the top right. Type `Bearer <paste the access token>` and confirm. Every padlock on the page closes.
5. `GET /api/authors/` → **Execute**. Works — it always did.
6. `POST /api/authors/` → **Execute** with a new name. **201**, because you are now authorised.
7. `DELETE /api/authors/{id}/` on the author you just made. **204 No Content**.
8. Click **Authorize** → **Logout**, then retry the `POST`. **401**.

**WHY `Bearer ` must be typed in front of the token** — `AUTH_HEADER_TYPES = ('Bearer',)` in 3.5 tells Simple JWT which prefix to accept in the `Authorization` header. Swagger UI sends the field's contents verbatim. Omit the word and the header reads `Authorization: eyJ...`, which the authentication class does not recognise — and the request is treated as anonymous, so you get a `401` that looks nothing like a formatting mistake. It is the most common five minutes lost in this whole day.

**CHECKPOINT 6** — every endpoint in the list has been executed at least once from Swagger UI, and you have seen the padlocks open and close.

\newpage

# Part 8 — Commit and push

**TYPE**

```bash
rm -f schema.yml
git status
```

**EXPECT** — modified `config/settings.py`, `config/urls.py`, `blog/models.py`, `blog/urls.py`, `blog/views.py`, `requirements.txt`; untracked `accounts/`, `blog/serializers.py`, `blog/api.py`, `blog/templates/`, `blog/migrations/0002_alter_author_options.py`. **No** `db.sqlite3`, **no** `schema.yml`, **no** `venv/`.

**TYPE**

```bash
git add accounts blog config requirements.txt
git status
```

Check the staged list against this before committing:

- [ ] `blog/migrations/0002_alter_author_options.py`
- [ ] `blog/templates/blog/base.html`, `author_list.html`, `author_detail.html`
- [ ] `blog/serializers.py`, `blog/api.py`, `blog/views.py`, `blog/urls.py`
- [ ] `accounts/serializers.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/apps.py`, `accounts/__init__.py`, `accounts/migrations/__init__.py`
- [ ] `config/settings.py`, `config/urls.py`
- [ ] `requirements.txt` with the three new pins
- [ ] **no** `db.sqlite3`, **no** `venv/`, **no** `__pycache__/`, **no** `schema.yml`

The templates are the easiest thing to miss — they live in a directory `startapp` never created, so a `git add blog/*.py` style command skips them entirely and your branch renders a `TemplateDoesNotExist` for everyone who clones it.

**TYPE**

```bash
git commit -m "Day 3: render authors, add DRF author API with JWT auth and OpenAPI docs"
git push -u origin <first_name>/day3
```

## 8.1 Prove it worked

Same discipline as Day 2 — rebuild from the branch alone:

```bash
cd /tmp
git clone -b <first_name>/day3 <repo-url> verify-day3
cd verify-day3
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py spectacular --validate --fail-on-warn > /dev/null && echo "schema OK"
python manage.py runserver 8001
```

**EXPECT** — `schema OK`, then <http://127.0.0.1:8001/> renders an empty author list ("No authors yet"), and <http://127.0.0.1:8001/api/docs/> shows all eight endpoints on a database that is sixty seconds old.

The empty list is the correct result: `db.sqlite3` is not in the repo, so there are no authors. The *endpoints* are all there. Migrations rebuild the schema, code rebuilds the API; only the data is yours.

Clean up with `cd /tmp && rm -rf verify-day3`.

\newpage

# Appendix A — Troubleshooting

| You see | It means | Fix |
| --- | --- | --- |
| `TemplateDoesNotExist: blog/author_list.html` | Wrong path, or app not in `INSTALLED_APPS` | Must be `blog/templates/blog/author_list.html` — the name repeats |
| `NoReverseMatch: 'author-detail' is not a registered namespace` | Missing `app_name`, or you wrote `{% url 'author-detail' %}` without the `blog:` prefix | Add `app_name = "blog"`; use `blog:author-detail` |
| `NoReverseMatch: Reverse for 'author-detail' with arguments '()' not found` | `{% url %}` called without the `pk` argument | `{% url 'blog:author-detail' author.pk %}` |
| Page 500s on `/authors/999/` instead of 404 | Used `Author.objects.get()` | Use `get_object_or_404` |
| `ModuleNotFoundError: No module named 'rest_framework'` | Installed outside the venv, or venv not active | Activate the venv, reinstall |
| `ModuleNotFoundError: No module named 'accounts'` | In `INSTALLED_APPS` but `startapp accounts` not run | Run it (5.2) |
| `Class AuthorViewSet missing "Serializer" attribute` | Typo in `serializer_class` | Check the spelling; it is singular |
| DRF warns `UnorderedObjectListWarning` | Paginating a queryset with no ordering | `Meta.ordering` on the model (1.3) |
| `401 {"detail":"Authentication credentials were not provided."}` | No `Authorization` header, or the header is malformed | Header must be `Authorization: Bearer <token>` |
| `401 {"detail":"Given token not valid for any token type"}` | Access token expired (30 min), or you pasted the refresh token by mistake | Call `/api/auth/refresh/`, or log in again |
| `403` where you expected `401` | You *are* authenticated; the permission class refused you | Read `permission_classes` on that view |
| `{"detail":"Token is blacklisted"}` on refresh | The refresh token was already used once | Rotation is on — use the newest refresh token |
| Login always returns `401 No active account found` | The user was created with `objects.create()`, so the password is not hashed | Recreate with `create_user()` (5.3) |
| Swagger UI **Authorize** does nothing | Token pasted without the `Bearer ` prefix | Type `Bearer ` then the token (Part 7) |
| `manage.py spectacular` warns about an enum or a serializer | Spectacular could not infer a shape | Add `@extend_schema` for that operation (6.4) |
| `/api/docs/` is blank with a console 404 | `SpectacularAPIView` route missing or named differently | The `url_name` must match the `name=` on the schema route |
| `manage.py dbshell -c ".tables"` errors | `dbshell` does not accept `-c` | Pipe it instead: `echo ".tables" \| python manage.py dbshell` |
| `That port is already in use` | The first `runserver` is still up | `runserver 8001`, or stop the other one |

\newpage

# Appendix B — Official documentation index

**Django 5.2 — views, URLs and templates**

- [Writing views](https://docs.djangoproject.com/en/5.2/topics/http/views/) · [Request/response objects](https://docs.djangoproject.com/en/5.2/ref/request-response/)
- [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/) · [`path()` and `include()`](https://docs.djangoproject.com/en/5.2/ref/urls/) · [URL namespaces](https://docs.djangoproject.com/en/5.2/topics/http/urls/#url-namespaces)
- [Shortcut functions](https://docs.djangoproject.com/en/5.2/topics/http/shortcuts/) — `render()`, `get_object_or_404()`
- [Templates topic guide](https://docs.djangoproject.com/en/5.2/topics/templates/) · [Language reference](https://docs.djangoproject.com/en/5.2/ref/templates/language/) · [Built-in tags and filters](https://docs.djangoproject.com/en/5.2/ref/templates/builtins/)
- [Automatic HTML escaping](https://docs.djangoproject.com/en/5.2/ref/templates/language/#automatic-html-escaping)
- [Making queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/) · [QuerySet API](https://docs.djangoproject.com/en/5.2/ref/models/querysets/)
- [`Meta.ordering`](https://docs.djangoproject.com/en/5.2/ref/models/options/#ordering) · [`AlterModelOptions`](https://docs.djangoproject.com/en/5.2/ref/migration-operations/#altermodeloptions)
- [Using the auth system](https://docs.djangoproject.com/en/5.2/topics/auth/default/) · [Password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/) · [Customising the user model](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/)

**Django REST Framework**

- [Home](https://www.django-rest-framework.org/) · [Quickstart](https://www.django-rest-framework.org/tutorial/quickstart/)
- [Serializers](https://www.django-rest-framework.org/api-guide/serializers/) · [Serializer fields](https://www.django-rest-framework.org/api-guide/fields/) · [Validators](https://www.django-rest-framework.org/api-guide/validators/)
- [Class-based views](https://www.django-rest-framework.org/api-guide/views/) · [Generic views](https://www.django-rest-framework.org/api-guide/generic-views/) · [ViewSets](https://www.django-rest-framework.org/api-guide/viewsets/) · [Routers](https://www.django-rest-framework.org/api-guide/routers/)
- [Authentication](https://www.django-rest-framework.org/api-guide/authentication/) · [Permissions](https://www.django-rest-framework.org/api-guide/permissions/) · [Throttling](https://www.django-rest-framework.org/api-guide/throttling/)
- [Filtering](https://www.django-rest-framework.org/api-guide/filtering/) · [Pagination](https://www.django-rest-framework.org/api-guide/pagination/) · [Versioning](https://www.django-rest-framework.org/api-guide/versioning/)
- [Settings](https://www.django-rest-framework.org/api-guide/settings/) · [The browsable API](https://www.django-rest-framework.org/topics/browsable-api/) · [Testing](https://www.django-rest-framework.org/api-guide/testing/)

**Simple JWT**

- [Documentation home](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)
- [Getting started](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html) · [Settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html)
- [Token types](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/token_types.html) · [Customising token claims](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/customizing_token_claims.html) · [Blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html)

**drf-spectacular and OpenAPI**

- [Documentation home](https://drf-spectacular.readthedocs.io/en/latest/) · [Settings list](https://drf-spectacular.readthedocs.io/en/latest/settings.html)
- [Customisation and `@extend_schema`](https://drf-spectacular.readthedocs.io/en/latest/customization.html) · [FAQ](https://drf-spectacular.readthedocs.io/en/latest/faq.html)
- [OpenAPI specification](https://spec.openapis.org/oas/latest.html) · [Swagger UI](https://swagger.io/tools/swagger-ui/) · [ReDoc](https://redocly.com/redoc/)

**JWT background**

- [jwt.io — paste a token and read it](https://jwt.io) · [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519) · [OWASP JWT cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

\newpage

# Appendix C — Command cheat sheet

```bash
# templates and views
python manage.py runserver
python manage.py shell                    # poke at the ORM

# the API stack
pip install djangorestframework djangorestframework-simplejwt drf-spectacular
pip freeze > requirements.txt

# schema
python manage.py spectacular                            # print to stdout
python manage.py spectacular --file schema.yml          # write it
python manage.py spectacular --validate --fail-on-warn  # CI form

# exercising the API
curl -s http://127.0.0.1:8000/api/authors/
curl -s -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"u","email":"u@example.com","password":"Str0ng-Lab-Pass"}'
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"u","password":"Str0ng-Lab-Pass"}'
curl -s http://127.0.0.1:8000/api/auth/me/ -H "Authorization: Bearer $ACCESS"
curl -s -X POST http://127.0.0.1:8000/api/authors/ \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"name":"New Author","bio":""}'

# inspecting
echo ".tables" | python manage.py dbshell
python manage.py showmigrations
```

**The URL map after today**

| URL | What answers it |
| --- | --- |
| `/` | `blog.views.author_list` — HTML |
| `/authors/<id>/` | `blog.views.author_detail` — HTML |
| `/admin/` | Django admin |
| `/api/authors/` | `AuthorViewSet` list + create |
| `/api/authors/<id>/` | `AuthorViewSet` retrieve + update + partial_update + destroy |
| `/api/auth/register/` | `RegisterView` |
| `/api/auth/login/` | `LoginView` — returns the token pair |
| `/api/auth/refresh/` | `TokenRefreshView` |
| `/api/auth/verify/` | `TokenVerifyView` |
| `/api/auth/logout/` | `LogoutView` — blacklists a refresh token |
| `/api/auth/me/` | `MeView` |
| `/api/schema/` | The OpenAPI document |
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |

\newpage

# Appendix D — Trainer notes

**The reference branch** — the finished state of this guide is on `dharmendra/day3` (PR #14, kept as a draft on purpose). It is generated from the code blocks below, so the two cannot drift. Use it to demo from, to diff a student's branch against, and to unblock anyone who falls badly behind. It is deliberately **not** merged: `main` has to stay at the end of Day 2 or *Start here* hands students the answers instead of an empty `blog/views.py`.

**Live-demo order that lands best**

1. Start at `/admin/` and ask: *how does a visitor who is not staff see this list?* Nobody has an answer, and that is the day's motivation in one question.
2. Write `author_list` and hit `/` **before** creating the template. `TemplateDoesNotExist` names the exact path it looked for, in the exact `blog/templates/blog/` form. Let the error teach the convention rather than telling them.
3. Before writing `{% url %}`, hardcode `/authors/1/`, then rename the route to `writers/` and reload. Every link 404s. Restore, switch to `{% url %}`, rename again — the links follow. Ninety seconds, and nobody hardcodes a URL again.
4. Set a bio to `<script>alert('xss')</script>` in the admin and reload the detail page. Nothing pops. Then add `|safe` and reload. *Then* remove it. That is the whole XSS lesson, felt.
5. In Part 4, run `curl` on `/api/authors/` and open the same URL in the browser side by side. Same view, same code, different `Accept` header, different rendering. Content negotiation clicks instantly.
6. Do the `401` → login → `201` sequence in one unbroken flow. The contrast is the point; splitting it across a break kills it.
7. Part 6.4 works best done live and backwards: show the broken `No response body`, ask the room why spectacular cannot know, *then* add the `responses=` line.

**Things that reliably confuse the room**

| Confusion | Say this |
| --- | --- |
| "So a view is a page?" | No. A view is a function that answers a request. It might return HTML, JSON, a PDF, or a redirect. |
| "Why is the templates folder name repeated?" | Django merges every app's template directory into one namespace. The inner folder is what stops two apps' `base.html` from colliding. Day 2, Part 1. |
| "Serializer or form?" | Forms for HTML pages, serializers for APIs. Same job, different wire format. |
| "Why does `GET` work but `POST` give 401?" | `IsAuthenticatedOrReadOnly`. Reads are open, writes need a user. |
| "401 or 403?" | 401 = I do not know who you are. 403 = I know, and you still may not. |
| "Where is the token stored on the server?" | Nowhere. That is the point. The signature is what makes it trustworthy. |
| "Then how does logout work?" | It only half-works. The refresh token is blacklisted; the access token dies of old age. Show them the 30-minute setting. |
| "Do I commit `schema.yml`?" | No — it is generated. Commit the code that generates it. |
| "Do I commit `requirements.txt` after `pip freeze`?" | Yes, every time you install something. |

**The one to check before they leave** — that `blog/templates/` is committed. `git add blog/*.py` misses it silently, and the branch then fails for everyone who clones it, with an error that points at a file that *is* on the author's disk. Part 8.1 catches it; make sure they actually run the clone-and-rebuild.

**Second thing to check** — `requirements.txt` was re-frozen. A branch with `accounts/` but no `djangorestframework` pin cannot be installed by anyone.

**Time budget** — Part 1 about 20 minutes, Part 2 about 50 (this is the part where the room is genuinely writing code for the first time), Part 3 about 25, Part 4 about 40, Part 5 about 55 including the JWT anatomy discussion, Parts 6–7 about 40. Roughly four hours with questions; if the day is shorter, Part 7 can be homework — but do not cut Part 5.6, the end-to-end curl walk is where it becomes real.

**Carrying into Day 4** — the obvious next steps are a `Post` model with a `ForeignKey` to `Author` (which makes `select_related` and nested serializers necessary rather than academic), `django-filter` for real query parameters, and `APITestCase` so the endpoints they wrote today get tests. The `Author` API is deliberately small enough to extend rather than replace.
