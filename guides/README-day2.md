---
title: "Day 2 — Apps, Table Names, Migrations and the Django Admin"
subtitle: "Creating the blog app, giving Author an explicit table name, and getting into /admin/"
author: "Django Practical Lab — daily guide series"
date: "Django 5.2 LTS · Python 3.12"
---

# What we did today

| # | Task | Command / change | Result |
| --- | --- | --- | --- |
| 1 | Created a second app | `python manage.py startapp blog` | `blog/` package scaffolded |
| 2 | Registered it | `'blog'` added to `INSTALLED_APPS` | Django now loads the app |
| 3 | Gave `Author` an explicit table name | `db_table = "authors"` in `Author.Meta` | Table renamed from `catalog_author` |
| 4 | Generated the migration | `python manage.py makemigrations catalog` | `catalog/migrations/0002_alter_author_table.py` |
| 5 | Applied it | `python manage.py migrate` | SQLite table is now `authors` |
| 6 | Created an admin login | `python manage.py createsuperuser` | Superuser account |
| 7 | Opened the admin | `runserver` → <http://127.0.0.1:8000/admin/> | Authors, Books, Genres, Author profiles |

## Before you start: the `catalog` app

Parts 4 and 6 are written against the `catalog` app — `Author`, `Book`, `Genre`
and `AuthorProfile`. **`catalog` is not in this repository.** It is trainer-owned
reference material, distributed separately.

| You have `catalog/` on disk | Follow the guide exactly as written |
| --- | --- |
| **You do not** | Parts 1–3, 5 and 7 run unchanged. For Parts 4 and 6, either ask the trainer for the app, or apply the same steps to any model of your own — the concepts do not depend on which model you use. |

Nothing in Parts 4 or 6 is specific to `Author`. `Meta.db_table`,
`AlterModelTable`, `sqlmigrate` and the `ModelAdmin` options behave identically
on any model, including one you write in `blog/` on Day 3.

## Conventions

Same as Day 1 — see `guides/README-day1.md`.

| Marker | Meaning |
| --- | --- |
| **TYPE** | Type this exactly. |
| **EXPECT** | What should appear. If you see something else, stop and fix it. |
| **CHECKPOINT** | A verifiable state. Nobody moves on until everyone reaches it. |
| **WHY** | The reasoning. Read it before the exam. |
| **DOCS** | The official Django documentation for what you just did. |

Every **DOCS** link points at the `5.2` version of the docs, matching the Django in `requirements.txt`. Django's docs are versioned by URL — if you land on a page reading `/en/stable/` or `/en/4.2/`, change it to `/en/5.2/` or you may be reading about a feature that does not exist in your install.

## Start here

**TYPE**

```bash
cd ~/code/django-lab
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
git switch main
git pull origin main
git switch -c <first_name>/day2
```

**EXPECT**

```
Switched to a new branch 'dharmendra/day2'
```

\newpage

# Part 1 — What a Django project actually is

Before creating a second app, be clear on the two words that get used interchangeably and should not be.

| Term | What it is | In this repo |
| --- | --- | --- |
| **Project** | The deployable unit. Holds settings, the root URLconf, and the WSGI/ASGI entry points. There is exactly one. | `config/` |
| **App** | A self-contained slice of functionality — models, views, templates, its own migrations. A project has many. Apps are meant to be reusable across projects. | `catalog/`, `blog/` |

> **DOCS** — [Django at a glance](https://docs.djangoproject.com/en/5.2/intro/overview/) · [Applications reference](https://docs.djangoproject.com/en/5.2/ref/applications/) · [Tutorial part 1: projects vs apps](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)

## The project layout, annotated

```
django-lab/
├── manage.py               <- CLI entry point; sets DJANGO_SETTINGS_MODULE, then delegates
├── requirements.txt        <- pinned dependencies (Day 1)
├── db.sqlite3              <- the database (gitignored — never commit it)
│
├── config/                 <- THE PROJECT
│   ├── __init__.py
│   ├── settings.py         <- INSTALLED_APPS, DATABASES, TEMPLATES, STATIC_URL...
│   ├── urls.py             <- the ROOT URLconf; every request starts here
│   ├── wsgi.py             <- entry point for sync production servers (gunicorn, uWSGI)
│   └── asgi.py             <- entry point for async servers (uvicorn, daphne)
│
├── catalog/                <- APP 1 (books, authors, genres)
│   ├── models.py
│   ├── views.py
│   ├── urls.py             <- included by config/urls.py under /catalog/
│   ├── admin.py            <- admin registrations
│   ├── apps.py             <- the AppConfig class
│   ├── migrations/         <- schema history; these ARE committed
│   ├── templates/catalog/
│   └── static/catalog/
│
└── blog/                   <- APP 2 (created today)
    ├── models.py           <- empty so far
    ├── views.py            <- empty so far
    ├── urls.py             <- empty so far
    ├── admin.py            <- empty so far
    ├── apps.py             <- BlogConfig
    └── migrations/         <- only __init__.py; no migrations yet
```

> **DOCS** — [`manage.py` and django-admin](https://docs.djangoproject.com/en/5.2/ref/django-admin/) · [Settings reference](https://docs.djangoproject.com/en/5.2/ref/settings/) · [How to deploy with WSGI](https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/) · [ASGI](https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/)

**WHY templates and static live in a nested folder** — `catalog/templates/catalog/base.html`, not `catalog/templates/base.html`. Django searches *all* apps' template directories and returns the first match. Without the app-named subfolder, two apps that both define `base.html` would shadow each other, and which one wins would depend on `INSTALLED_APPS` order. The repeated folder name is a namespace, not a typo.

> **DOCS** — [Template loading and namespacing](https://docs.djangoproject.com/en/5.2/intro/tutorial03/#namespacing-url-names) · [Managing static files](https://docs.djangoproject.com/en/5.2/howto/static-files/)

\newpage

# Part 2 — Create the `blog` app

## 2.1 Scaffold it

**TYPE**

```bash
python manage.py startapp blog
```

**EXPECT** — no output. Silence is success. A new `blog/` directory appears.

> **DOCS** — [`startapp`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#startapp)

## 2.2 What each generated file is for

**TYPE**

```bash
ls blog/
```

**EXPECT**

```
__init__.py  admin.py  apps.py  migrations/  models.py  tests.py  views.py
```

| File | Purpose | Docs |
| --- | --- | --- |
| `__init__.py` | Marks the directory as a Python package. Leave it empty. | — |
| `models.py` | Your database tables, as Python classes | [Models](https://docs.djangoproject.com/en/5.2/topics/db/models/) |
| `views.py` | Functions/classes that take a request and return a response | [Views](https://docs.djangoproject.com/en/5.2/topics/http/views/) |
| `admin.py` | Registers models with the admin site | [Admin site](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/) |
| `apps.py` | The `AppConfig` — app metadata and startup hooks | [AppConfig](https://docs.djangoproject.com/en/5.2/ref/applications/#configuring-applications) |
| `tests.py` | Where your tests go | [Testing](https://docs.djangoproject.com/en/5.2/topics/testing/) |
| `migrations/` | Schema change history. Commit these. | [Migrations](https://docs.djangoproject.com/en/5.2/topics/migrations/) |

Note what `startapp` does **not** create: no `urls.py`, and no `templates/` or `static/` directories. You add those yourself when you need them.

**TYPE** — read the AppConfig:

```bash
cat blog/apps.py
```

**EXPECT**

```python
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
```

`default_auto_field` decides the type of the implicit `id` primary key Django adds to every model. `BigAutoField` is a 64-bit integer — the modern default, because 32-bit `AutoField` tops out at roughly 2.1 billion rows.

> **DOCS** — [`DEFAULT_AUTO_FIELD`](https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field) · [Automatic primary keys](https://docs.djangoproject.com/en/5.2/topics/db/models/#automatic-primary-key-fields)

## 2.3 Register the app

Creating the directory is not enough. Django only knows about apps listed in `INSTALLED_APPS`.

Edit `config/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'catalog',
    'blog',
]
```

> **DOCS** — [`INSTALLED_APPS`](https://docs.djangoproject.com/en/5.2/ref/settings/#installed-apps)

**WHY it matters** — `INSTALLED_APPS` is what drives model discovery, migration discovery, template discovery, static file discovery, and admin autodiscovery. An unregistered app is invisible: its models never get tables, `makemigrations` ignores it, and its templates are never found. If something you wrote seems to do nothing at all, check this list first.

**WHY the `django.contrib.*` entries are there** — they are apps too, shipped with Django. `admin` is the admin site you will open in Part 5; `auth` provides the `User` model and permissions; `contenttypes` lets other apps refer to any model generically; `sessions` backs login state; `staticfiles` serves CSS and JS in development.

> **DOCS** — [contrib packages](https://docs.djangoproject.com/en/5.2/ref/contrib/) · [Using the auth system](https://docs.djangoproject.com/en/5.2/topics/auth/default/)

**TYPE** — confirm Django loads cleanly:

```bash
python manage.py check
```

**EXPECT**

```
System check identified no issues (0 silenced).
```

> **DOCS** — [System check framework](https://docs.djangoproject.com/en/5.2/topics/checks/)

## 2.4 An app with no models produces no migrations

**TYPE**

```bash
python manage.py makemigrations blog
```

**EXPECT**

```
No changes detected in app 'blog'
```

**TYPE**

```bash
python manage.py showmigrations blog
```

**EXPECT**

```
blog
 (no migrations)
```

This is correct, not a failure. `blog/models.py` still contains only the placeholder comment, so there is no table to create. Migrations describe *changes to models*; no models, no changes.

> **DOCS** — [Migrations workflow](https://docs.djangoproject.com/en/5.2/topics/migrations/#workflow)

> **CHECKPOINT 1** — `blog` appears in `INSTALLED_APPS`, `manage.py check` is clean, and `showmigrations blog` reports `(no migrations)`.

## 2.5 Where `blog` stops, for now

Be honest about what the app can and cannot do at the end of today:

| | Status |
| --- | --- |
| Registered in `INSTALLED_APPS` | Yes |
| Has models | No — `models.py` is empty |
| Has a `urls.py` | The file exists but is empty |
| Included in `config/urls.py` | **No** |
| Reachable in a browser | **No** — there is no URL that routes to it |
| Visible in `/admin/` | **No** — nothing registered, nothing to register |

Today's goal was the scaffold and the wiring into settings. Models, views and URLs are Day 3.

\newpage

# Part 3 — URL configuration

You did not change URLs today, but you need to understand the file you will edit tomorrow.

## 3.1 The root URLconf

**TYPE**

```bash
cat config/urls.py
```

**EXPECT**

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("catalog/", include("catalog.urls")),
]
```

> **DOCS** — [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/) · [`path()`](https://docs.djangoproject.com/en/5.2/ref/urls/#path) · [`include()`](https://docs.djangoproject.com/en/5.2/ref/urls/#include) · [`ROOT_URLCONF`](https://docs.djangoproject.com/en/5.2/ref/settings/#root-urlconf)

## 3.2 How a request is resolved

1. A request arrives for `/catalog/books/3/`.
2. Django reads `ROOT_URLCONF` from settings — it points at `config.urls`.
3. It walks `urlpatterns` **top to bottom** and stops at the first match.
4. `"admin/"` does not match. `"catalog/"` does.
5. `include("catalog.urls")` **strips the matched prefix** and hands the remainder — `books/3/` — to `catalog/urls.py`.
6. That file matches it against its own `urlpatterns` and calls the view.

**WHY `include()` strips the prefix** — it is what makes apps portable. `catalog/urls.py` never mentions `/catalog/`, so you can remount the entire app at `/library/` by changing one line in the project, without touching the app.

**WHY order matters** — first match wins, so a broad pattern placed above a specific one will shadow it permanently.

**WHY the trailing slash** — Django's `APPEND_SLASH` setting (on by default, via `CommonMiddleware`) redirects `/catalog/books` to `/catalog/books/`. Be consistent: define patterns with a trailing slash.

> **DOCS** — [`APPEND_SLASH`](https://docs.djangoproject.com/en/5.2/ref/settings/#append-slash) · [Naming URL patterns](https://docs.djangoproject.com/en/5.2/topics/http/urls/#naming-url-patterns) · [`reverse()`](https://docs.djangoproject.com/en/5.2/ref/urlresolvers/#reverse)

## 3.3 What tomorrow's wiring will look like

Do not type this today — it is here so the shape is familiar when you meet it:

```python
# config/urls.py
urlpatterns = [
    path("admin/", admin.site.urls),
    path("catalog/", include("catalog.urls")),
    path("blog/", include("blog.urls")),      # Day 3
]
```

```python
# blog/urls.py
from django.urls import path
from . import views

app_name = "blog"                              # the URL namespace

urlpatterns = [
    path("", views.post_list, name="post-list"),
    path("<int:pk>/", views.post_detail, name="post-detail"),
]
```

Adding `include("blog.urls")` **before** `blog/urls.py` defines a `urlpatterns` list raises `ImproperlyConfigured` at startup. Write the app's URLconf first, then include it.

> **DOCS** — [URL namespaces](https://docs.djangoproject.com/en/5.2/topics/http/urls/#url-namespaces) · [Path converters](https://docs.djangoproject.com/en/5.2/topics/http/urls/#path-converters)

\newpage

# Part 4 — Give `Author` an explicit table name

> **Needs the `catalog` app** — see *Before you start*. Without it, apply every
> step below to a model of your own; only the names change.

## 4.1 What Django names tables by default

Django derives a table name as `<app_label>_<lowercased_model_name>`:

| Model | Default table |
| --- | --- |
| `catalog.Author` | `catalog_author` |
| `catalog.Book` | `catalog_book` |
| `catalog.AuthorProfile` | `catalog_authorprofile` |

You can override that per model with the `db_table` option on the model's inner `Meta` class.

> **DOCS** — [Model `Meta` options](https://docs.djangoproject.com/en/5.2/ref/models/options/) · [**`db_table`**](https://docs.djangoproject.com/en/5.2/ref/models/options/#db-table) · [Model `Meta` explained](https://docs.djangoproject.com/en/5.2/topics/db/models/#meta-options)

## 4.2 The change

Edit `catalog/models.py`:

```python
class Author(models.Model):
    name = models.CharField(max_length=120)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = "authors"
        ordering = ["name"]

    def __str__(self):
        return self.name
```

That is the whole change: one line.

| `Meta` option | Effect | Docs |
| --- | --- | --- |
| `db_table` | The physical table name in the database | [ref](https://docs.djangoproject.com/en/5.2/ref/models/options/#db-table) |
| `ordering` | Default sort for every queryset on this model | [ref](https://docs.djangoproject.com/en/5.2/ref/models/options/#ordering) |

**WHY you would ever set `db_table`:**

- **Legacy databases.** The table already exists and is called `authors`. You cannot rename it — other systems read it.
- **Shared databases.** A DBA or another team owns the schema and has a naming standard your Django app must follow.
- **Cross-app clarity.** `catalog_author` leaks the app name into the schema. If the app is ever renamed or the model moved, the table name becomes actively misleading.

**WHY you often should not** — the default is predictable and self-documenting: any developer can look at a table and know which app owns it. Override deliberately, not by habit.

> `__str__` is not a `Meta` option — it is a regular method, and it controls how the object is labelled in the admin, in the shell, and anywhere it is coerced to a string. Every model should define one.
>
> **DOCS** — [`__str__()`](https://docs.djangoproject.com/en/5.2/ref/models/instances/#django.db.models.Model.__str__)

## 4.3 Generate the migration

**TYPE**

```bash
python manage.py makemigrations catalog
```

**EXPECT**

```
Migrations for 'catalog':
  catalog/migrations/0002_alter_author_table.py
    ~ Rename table for author to authors
```

> **DOCS** — [`makemigrations`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#makemigrations)

## 4.4 Read the migration before applying it

Never run a migration you have not read. It is the only chance you get to catch a destructive operation before it happens.

**TYPE**

```bash
cat catalog/migrations/0002_alter_author_table.py
```

**EXPECT**

```python
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='author',
            table='authors',
        ),
    ]
```

| Part | Meaning |
| --- | --- |
| `dependencies` | This migration must run after `catalog.0001_initial`. Django builds a dependency graph across all apps and orders every migration from it. |
| `operations` | The actual changes. Here, exactly one. |
| `AlterModelTable` | Emits `ALTER TABLE "catalog_author" RENAME TO "authors"` |

**TYPE** — see the real SQL, without running it:

```bash
python manage.py sqlmigrate catalog 0002
```

**EXPECT**

```sql
BEGIN;
--
-- Rename table for author to authors
--
ALTER TABLE "catalog_author" RENAME TO "authors";
COMMIT;
```

> **DOCS** — [Migration operations reference](https://docs.djangoproject.com/en/5.2/ref/migration-operations/) · [`AlterModelTable`](https://docs.djangoproject.com/en/5.2/ref/migration-operations/#altermodeltable) · [`sqlmigrate`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#sqlmigrate)

**WHY this is a RENAME and not a DROP + CREATE** — Django compares the model state recorded in `0001_initial` against your current models and finds only the table name differs. A rename preserves every row. Had it dropped and recreated, all four authors would be gone.

**WHY the foreign keys do not break** — `Book.author` and `AuthorProfile.author` point at the `Author` *model*, not at a table name string. Django regenerates the FK constraints against the new table automatically. You will verify this in 4.6.

## 4.5 Apply it

**TYPE**

```bash
python manage.py migrate
```

**EXPECT**

```
Operations to perform:
  Apply all migrations: admin, auth, catalog, contenttypes, sessions
Running migrations:
  Applying catalog.0002_alter_author_table... OK
```

**TYPE** — confirm the recorded state:

```bash
python manage.py showmigrations catalog
```

**EXPECT** — `[X]` means applied:

```
catalog
 [X] 0001_initial
 [X] 0002_alter_author_table
```

> **DOCS** — [`migrate`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#migrate) · [`showmigrations`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#showmigrations)

## 4.6 Verify the rename, and that nothing was lost

**TYPE** — inspect the database directly:

```bash
python manage.py dbshell
```

```sql
.tables
SELECT COUNT(*) FROM authors;
.quit
```

**EXPECT** — `authors` is present and `catalog_author` is gone.

**TYPE** — or from the Django shell, which also proves the relationships still resolve:

```bash
python manage.py shell
```

```python
>>> from catalog.models import Author, Book
>>> Author._meta.db_table
'authors'
>>> Author.objects.count()
4
>>> Book.objects.count()
10
>>> Author.objects.first().books.count()
2
>>> exit()
```

That last line is the important one: it follows the `Book.author` foreign key backwards through `related_name="books"`. If it returns a number rather than raising, the FK survived the rename.

> **DOCS** — [`dbshell`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#dbshell) · [`shell`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#shell) · [Related objects reference](https://docs.djangoproject.com/en/5.2/ref/models/relations/) · [QuerySet API](https://docs.djangoproject.com/en/5.2/ref/models/querysets/)

> **CHECKPOINT 2** — `Author._meta.db_table` returns `'authors'`, the row counts are unchanged, and `.books.count()` works.

## 4.7 Migrations are code — commit them

A migration file is as much a part of your source as the model. The model says what the schema *should* be; the migration says how to *get there* from what shipped last time. Without it, a teammate's database never changes and the two silently diverge.

In a normal project you would commit the model and its migration together:

```bash
git add <app>/models.py <app>/migrations/0002_*.py
```

> **In *this* repository `catalog/` is gitignored**, so you will not commit today's migration — see 7.1. The principle still stands, and it applies to every app you write yourself.

**A trap worth knowing**, because it is silent and it has bitten this repo: gitignore is only consulted for **untracked** files. Add a directory rule to a folder that is already partly tracked and the existing files keep showing as modified while *new* ones disappear from `git status` entirely. You then commit a model change whose migration was never staged, and every clone's `migrate` quietly does nothing.

If a file you expect is missing from `git status`, check before reaching for `-f`:

```bash
git check-ignore -v <path>      # exit 0 = a rule matched; exit 1 = no rule, it is tracked
```

Fix the rule rather than force-adding around it, or the next migration vanishes too.

**Never edit a migration that has been pushed.** Someone else has already applied it. Make a new one.

> **DOCS** — [Migrations in version control](https://docs.djangoproject.com/en/5.2/topics/migrations/#version-control)

\newpage

# Part 5 — Create a superuser

The admin requires a login, and a fresh database has no users.

**TYPE**

```bash
python manage.py createsuperuser
```

**EXPECT** — three prompts:

```
Username (leave blank to use 'you'): admin
Email address: you@example.com
Password:
Password (again):
Superuser created successfully.
```

| Field | Notes |
| --- | --- |
| **Username** | Required and unique. Pressing Enter accepts your OS username. |
| **Email** | Optional — press Enter to skip. Used for password reset. |
| **Password** | Not echoed. The cursor will not move as you type. This is normal. |

If you choose something weak, Django warns and offers a bypass:

```
This password is too short. It must contain at least 8 characters.
This password is too common.
Bypass password validation and create user anyway? [y/N]:
```

Answer `y` only on a local lab database. The rules come from `AUTH_PASSWORD_VALIDATORS` in settings.

> **DOCS** — [`createsuperuser`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#createsuperuser) · [Password validation](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/#password-validation) · [`User` model](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/#user-model)

**WHY "superuser" and not just "user"** — two boolean flags on `User` control admin access:

| Flag | Meaning |
| --- | --- |
| `is_staff` | May log into `/admin/` at all |
| `is_superuser` | Has every permission implicitly, without them being granted |

`createsuperuser` sets both. A user with `is_staff=True` but `is_superuser=False` can log in and will see only the models they hold explicit permissions for — that is how you give someone limited admin access.

> **DOCS** — [Permissions and authorization](https://docs.djangoproject.com/en/5.2/topics/auth/default/#permissions-and-authorization)

**If you forget the password:**

```bash
python manage.py changepassword admin
```

**Non-interactive** (for scripts and CI — never with a real password on the command line):

```bash
DJANGO_SUPERUSER_PASSWORD=changeme123 \
  python manage.py createsuperuser --noinput --username admin --email admin@example.com
```

**TYPE** — list who exists:

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
for u in User.objects.all():
    print(u.username, 'staff=', u.is_staff, 'super=', u.is_superuser)
"
```

> **CHECKPOINT 3** — at least one user prints with `staff= True super= True`.

\newpage

# Part 6 — The Django admin

> **6.1 and 6.3 need the `catalog` app** — see *Before you start*. Without it,
> `/admin/` shows only Groups and Users; log in, then read 6.2–6.3 as the
> reference for registering your own models on Day 3.

## 6.1 Open it

**TYPE**

```bash
python manage.py runserver
```

Go to <http://127.0.0.1:8000/admin/> and log in with the superuser you just made.

> **DOCS** — [The Django admin site](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/) · [`runserver`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#runserver)

**EXPECT** — the index, grouped by app:

```
AUTHENTICATION AND AUTHORIZATION
    Groups
    Users

CATALOG
    Author profiles
    Authors
    Books
    Genres
```

Two things to notice:

- **`Authors` still reads "Authors".** The admin labels models from the class name, not the table name. Renaming the table changed nothing a user can see — which is the point of an ORM.
- **There is no `BLOG` section.** `blog` is installed, but it has no models, so there is nothing to register and nothing to show.

## 6.2 Why those four models appear

Because `catalog/admin.py` registers them:

```python
from django.contrib import admin

from .models import Author, AuthorProfile, Book, Genre


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "year", "price", "added_on")
    list_filter = ("year", "genres")
    search_fields = ("title", "author__name")
    filter_horizontal = ("genres",)
    ordering = ("-year",)
    list_per_page = 25


admin.site.register(Genre)
admin.site.register(AuthorProfile)
```

There are two registration styles here, and both are fine:

- `@admin.register(Book)` — decorator, attaches the `ModelAdmin` class
- `admin.site.register(Genre)` — plain call with no `ModelAdmin`, so Django uses defaults

**A model that is not registered does not appear in the admin at all.** That is the single most common "why can't I see my model" answer.

> **DOCS** — [`ModelAdmin` options](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#modeladmin-options) · [`admin.site.register`](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.AdminSite.register)

## 6.3 What each `ModelAdmin` option does

Open **Books** and match each option to what you see:

| Option | Effect on the page | Docs |
| --- | --- | --- |
| `list_display` | The columns in the change list. Without it you get one column of `__str__`. | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display) |
| `list_filter` | The filter sidebar on the right | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter) |
| `search_fields` | The search box. `author__name` follows the FK — the double underscore means "traverse the relationship". | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.search_fields) |
| `filter_horizontal` | Turns the many-to-many `genres` box into the two-pane chooser | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.filter_horizontal) |
| `ordering` | Default sort. `-year` means descending. | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.ordering) |
| `list_per_page` | Rows before pagination kicks in | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_per_page) |

The `field__lookup` double-underscore syntax in `search_fields` is the same syntax used throughout the ORM — `Book.objects.filter(author__name="...")`.

> **DOCS** — [Field lookups](https://docs.djangoproject.com/en/5.2/topics/db/queries/#field-lookups) · [Lookups that span relationships](https://docs.djangoproject.com/en/5.2/topics/db/queries/#lookups-that-span-relationships)

## 6.4 Confirm the rename end to end

1. Click **Authors**. Four authors are listed.
2. Open one. Change the bio. **Save**.
3. Stop the server and check the write landed in the renamed table:

```bash
python manage.py shell -c "
from catalog.models import Author
a = Author.objects.first()
print(Author._meta.db_table, '|', a.name, '|', a.bio[:40])
"
```

**EXPECT** — `authors | <name> | <your edited text>`

You edited a row through the admin, and it was written to a table called `authors`. Neither the admin nor your model code mentioned that name anywhere except one line of `Meta`.

> **CHECKPOINT 4 — Day 2 complete.** You can log into `/admin/`, see the four catalog models, edit an author, and confirm the write landed in the `authors` table.

\newpage

# Part 7 — Commit and push

**TYPE**

```bash
git status
```

**EXPECT** — `config/settings.py` modified and `blog/` untracked.

**TYPE**

```bash
git add config/settings.py blog/
git status
git commit -m "Day 2: add blog app and register it in INSTALLED_APPS"
git push -u origin <first_name>/day2
```

Confirm on GitHub that the branch contains:

- [ ] `blog/` with `apps.py`, `models.py`, `views.py`, `admin.py`, `migrations/__init__.py`
- [ ] `config/settings.py` listing `'blog'` in `INSTALLED_APPS`
- [ ] **no** `db.sqlite3`, **no** `venv/`, **no** `__pycache__/`

The database is deliberately absent. Your classmate rebuilds their own by running `migrate` — that is what migrations are for.

## 7.1 Why your Part 4 work is not in that list

`catalog/` is listed in this repository's `.gitignore`, so `catalog/models.py` and your new migration are deliberately **not** committed here — the app is trainer-owned and distributed separately.

Trying to add them anyway tells you so:

```
$ git add catalog/models.py
The following paths are ignored by one of your .gitignore files:
catalog
hint: Use -f if you really want to add them.
```

**Do not use `-f`.** The rule is intentional. Part 4 was an exercise in reading and applying a migration, not in shipping one.

This is a property of *this* repo, not of Django. In a normal project `catalog/` would be tracked and its migrations committed like any other source file — which is exactly what 4.7 argues.

\newpage

# Appendix A — Troubleshooting

| You see | It means | Fix |
| --- | --- | --- |
| `No installed app with label 'blog'` | Not in `INSTALLED_APPS`, or a typo | Check `config/settings.py`, then `manage.py check` |
| `ModuleNotFoundError: No module named 'blog'` | Listed in settings but the directory is missing or misnamed | `ls blog/`; re-run `startapp` |
| `No changes detected` after editing a model | Wrong app label, or you edited a file Django does not load | `python manage.py makemigrations` with no app label |
| `Table 'catalog_author' already exists` | The migration state and the database disagree | `showmigrations`; on a lab DB, delete `db.sqlite3` and `migrate` again |
| `no such table: authors` | Migration created but never applied | `python manage.py migrate` |
| `Conflicting migrations detected` | Two migrations with the same number, usually after a merge | `python manage.py makemigrations --merge` |
| `You have N unapplied migration(s)` on `runserver` | Pending migrations | `python manage.py migrate` |
| `That username is already taken` | The superuser exists | `changepassword <username>` |
| Login page rejects a correct password | The account has `is_staff=False` | Set `is_staff=True` in the shell |
| Admin index is empty | Nothing registered in `admin.py` | Register the models |
| Model missing from `/admin/` | Not registered | Add `admin.site.register(Model)` |
| CSS missing on `/admin/` | `staticfiles` not installed, or `DEBUG=False` locally | Check `INSTALLED_APPS`; keep `DEBUG=True` in the lab |
| `That port is already in use` | An old `runserver` is still alive | `runserver 8001`, or kill it |

\newpage

# Appendix B — Official documentation index

Bookmark these. Everything in this guide came from them.

**Start here**

- [Django 5.2 documentation home](https://docs.djangoproject.com/en/5.2/)
- [Django at a glance](https://docs.djangoproject.com/en/5.2/intro/overview/)
- [Tutorial, parts 1–8](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)
- [How the documentation is organised](https://docs.djangoproject.com/en/5.2/intro/)

**Projects, apps and settings**

- [Applications and `AppConfig`](https://docs.djangoproject.com/en/5.2/ref/applications/)
- [Settings reference](https://docs.djangoproject.com/en/5.2/ref/settings/) · [`INSTALLED_APPS`](https://docs.djangoproject.com/en/5.2/ref/settings/#installed-apps)
- [`django-admin` and `manage.py`](https://docs.djangoproject.com/en/5.2/ref/django-admin/)
- [System check framework](https://docs.djangoproject.com/en/5.2/topics/checks/)
- [Reusable apps](https://docs.djangoproject.com/en/5.2/intro/reusable-apps/)

**Models**

- [Models topic guide](https://docs.djangoproject.com/en/5.2/topics/db/models/)
- [Model field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/)
- [**Model `Meta` options**](https://docs.djangoproject.com/en/5.2/ref/models/options/) · [`db_table`](https://docs.djangoproject.com/en/5.2/ref/models/options/#db-table) · [`ordering`](https://docs.djangoproject.com/en/5.2/ref/models/options/#ordering)
- [Relationships: FK, M2M, O2O](https://docs.djangoproject.com/en/5.2/topics/db/examples/)
- [Making queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/)
- [QuerySet API reference](https://docs.djangoproject.com/en/5.2/ref/models/querysets/)
- [Model instance reference](https://docs.djangoproject.com/en/5.2/ref/models/instances/)

**Migrations**

- [Migrations topic guide](https://docs.djangoproject.com/en/5.2/topics/migrations/)
- [Migration operations reference](https://docs.djangoproject.com/en/5.2/ref/migration-operations/)
- [Writing database migrations](https://docs.djangoproject.com/en/5.2/howto/writing-migrations/)

**URLs and views**

- [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/)
- [`path()`, `re_path()`, `include()`](https://docs.djangoproject.com/en/5.2/ref/urls/)
- [URL namespaces](https://docs.djangoproject.com/en/5.2/topics/http/urls/#url-namespaces)
- [Writing views](https://docs.djangoproject.com/en/5.2/topics/http/views/)
- [`reverse()` and resolvers](https://docs.djangoproject.com/en/5.2/ref/urlresolvers/)

**Admin and auth**

- [The admin site](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/)
- [`ModelAdmin` options](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#modeladmin-options)
- [`InlineModelAdmin`](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#inlinemodeladmin-objects)
- [Using the auth system](https://docs.djangoproject.com/en/5.2/topics/auth/default/)
- [`User` model reference](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/)

**Templates and static files**

- [Templates](https://docs.djangoproject.com/en/5.2/topics/templates/)
- [Template language](https://docs.djangoproject.com/en/5.2/ref/templates/language/)
- [Managing static files](https://docs.djangoproject.com/en/5.2/howto/static-files/)

\newpage

# Appendix C — Command cheat sheet

```bash
# apps
python manage.py startapp <name>          # scaffold, then add to INSTALLED_APPS
python manage.py check                    # does the project load?

# migrations
python manage.py makemigrations           # all apps
python manage.py makemigrations catalog   # one app
python manage.py sqlmigrate catalog 0002  # show the SQL, run nothing
python manage.py migrate                  # apply
python manage.py showmigrations           # [X] applied, [ ] pending
python manage.py migrate catalog 0001     # roll back to 0001

# users
python manage.py createsuperuser
python manage.py changepassword <username>

# inspecting
python manage.py shell
python manage.py dbshell
python manage.py runserver
python manage.py runserver 8001
```

\newpage

# Appendix D — Trainer notes

**Live-demo order that lands best**

1. `startapp blog`, then `runserver` *before* touching settings — nothing happens. Then add to `INSTALLED_APPS`. The contrast is what makes `INSTALLED_APPS` memorable.
2. Show `catalog_author` in `dbshell` **before** editing `Meta`. Students need the "before" to believe the rename.
3. Run `sqlmigrate` before `migrate`, every time, all week. Make reading generated SQL a reflex.
4. Deliberately break it: comment out `admin.site.register(Genre)`, reload `/admin/`, watch Genres vanish. Restore.

**Things that reliably confuse the room**

| Confusion | Say this |
| --- | --- |
| "Why is the admin still saying Authors?" | The admin reads the class name. The table name is a database detail the ORM hides. That is the whole point. |
| "Why did `makemigrations blog` do nothing?" | Migrations describe model changes. No models, no changes. Not an error. |
| "Do I commit migrations?" | Yes. Always. They are source code. |
| "Do I commit `db.sqlite3`?" | Never. Your classmate rebuilds it with `migrate`. |
| "It says no such table" | You made the migration but did not apply it. |

**Watch for** — students on Windows hitting `Set-ExecutionPolicy` again in a new terminal, and students who never reactivated the venv (`django-admin: command not found`). Both are Day 1 issues resurfacing; point at `README-day1.md` §5.2 rather than re-teaching.

**Time budget** — Parts 1–2 about 30 minutes, Part 3 about 20 (discussion, no typing), Part 4 about 35 including `sqlmigrate` and verification, Parts 5–6 about 30. Roughly two hours with questions.
