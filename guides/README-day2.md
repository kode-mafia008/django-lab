---
title: "Day 2 — Apps, Models, Table Names, Migrations and the Django Admin"
subtitle: "Creating the blog app, adding an Author model with an explicit table name, and getting into /admin/"
author: "Django Practical Lab — daily guide series"
date: "Django 5.2 LTS · Python 3.12"
---

# What we did today

| # | Task | Command / change | Result |
| --- | --- | --- | --- |
| 1 | Created a second app | `python manage.py startapp blog` | `blog/` package scaffolded |
| 2 | Registered it | `'blog'` added to `INSTALLED_APPS` | Django now loads the app |
| 3 | Wrote the first model | `Author` in `blog/models.py` | Two fields: `name`, `bio` |
| 4 | Gave it an explicit table name | `db_table = "authors"` in `Author.Meta` | Table is `authors`, not `blog_author` |
| 5 | Generated the migration | `python manage.py makemigrations blog` | `blog/migrations/0001_initial.py` |
| 6 | Applied it | `python manage.py migrate` | The `authors` table exists in SQLite |
| 7 | Created an admin login | `python manage.py createsuperuser` | Superuser account |
| 8 | Registered the model and opened the admin | `blog/admin.py`, then `runserver` → <http://127.0.0.1:8000/admin/> | Authors editable in the admin |

Everything below runs against what is in this repository. No other app is needed.

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
| **App** | A self-contained slice of functionality — models, views, templates, its own migrations. A project has many. Apps are meant to be reusable across projects. | `blog/` |

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
└── blog/                   <- THE APP (created today)
    ├── __init__.py
    ├── models.py           <- Author, added in Part 4
    ├── views.py            <- empty so far (Day 3)
    ├── urls.py             <- empty so far (Day 3)
    ├── admin.py            <- admin registrations, Part 6
    ├── apps.py             <- BlogConfig
    ├── tests.py
    └── migrations/         <- schema history; these ARE committed
```

Two directories `startapp` does **not** create, which you add yourself when needed:

```
blog/
├── templates/blog/         <- note the repeated name
└── static/blog/
```

> **DOCS** — [`manage.py` and django-admin](https://docs.djangoproject.com/en/5.2/ref/django-admin/) · [Settings reference](https://docs.djangoproject.com/en/5.2/ref/settings/) · [How to deploy with WSGI](https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/) · [ASGI](https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/)

**WHY templates and static live in a nested folder** — `blog/templates/blog/base.html`, not `blog/templates/base.html`. Django searches *all* apps' template directories and returns the first match. Without the app-named subfolder, two apps that both define `base.html` would shadow each other, and which one wins would depend on `INSTALLED_APPS` order. The repeated folder name is a namespace, not a typo.

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
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
```

One route, and it is the admin. That is the whole URLconf today — which is why nothing you write in `blog/views.py` would be reachable yet even if you wrote it.

> **DOCS** — [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/) · [`path()`](https://docs.djangoproject.com/en/5.2/ref/urls/#path) · [`include()`](https://docs.djangoproject.com/en/5.2/ref/urls/#include) · [`ROOT_URLCONF`](https://docs.djangoproject.com/en/5.2/ref/settings/#root-urlconf)

## 3.2 How a request is resolved

Take a request for `/blog/posts/3/`, once Day 3 has wired the app up:

1. The request arrives for `/blog/posts/3/`.
2. Django reads `ROOT_URLCONF` from settings — it points at `config.urls`.
3. It walks `urlpatterns` **top to bottom** and stops at the first match.
4. `"admin/"` does not match. `"blog/"` does.
5. `include("blog.urls")` **strips the matched prefix** and hands the remainder — `posts/3/` — to `blog/urls.py`.
6. That file matches it against its own `urlpatterns` and calls the view.

**WHY `include()` strips the prefix** — it is what makes apps portable. `blog/urls.py` never mentions `/blog/`, so you can remount the entire app at `/journal/` by changing one line in the project, without touching the app.

**WHY order matters** — first match wins, so a broad pattern placed above a specific one will shadow it permanently.

**WHY the trailing slash** — Django's `APPEND_SLASH` setting (on by default, via `CommonMiddleware`) redirects `/blog/posts` to `/blog/posts/`. Be consistent: define patterns with a trailing slash.

> **DOCS** — [`APPEND_SLASH`](https://docs.djangoproject.com/en/5.2/ref/settings/#append-slash) · [Naming URL patterns](https://docs.djangoproject.com/en/5.2/topics/http/urls/#naming-url-patterns) · [`reverse()`](https://docs.djangoproject.com/en/5.2/ref/urlresolvers/#reverse)

## 3.3 What tomorrow's wiring will look like

Do not type this today — it is here so the shape is familiar when you meet it:

```python
# config/urls.py
from django.urls import include, path       # include() is needed from Day 3

urlpatterns = [
    path("admin/", admin.site.urls),
    path("blog/", include("blog.urls")),    # Day 3
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

# Part 4 — Write the `Author` model with an explicit table name

This is where `blog` stops being an empty scaffold. You will add one model, decide what its database table is called, and watch Django generate the SQL that creates it.

## 4.1 What Django names tables by default

Django derives a table name as `<app_label>_<lowercased_model_name>`:

| Model | Default table |
| --- | --- |
| `blog.Author` | `blog_author` |
| `blog.Post` | `blog_post` |
| `blog.PostCategory` | `blog_postcategory` |

You can override that per model with the `db_table` option on the model's inner `Meta` class.

> **DOCS** — [Model `Meta` options](https://docs.djangoproject.com/en/5.2/ref/models/options/) · [**`db_table`**](https://docs.djangoproject.com/en/5.2/ref/models/options/#db-table) · [Model `Meta` explained](https://docs.djangoproject.com/en/5.2/topics/db/models/#meta-options)

## 4.2 Write the model

Replace the placeholder comment in `blog/models.py` with:

```python
from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = "authors"

    def __str__(self):
        return self.name
```

Three separate decisions are packed into that, and each is worth naming.

### The fields

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `CharField` | `max_length` is **required** — it becomes `VARCHAR(100)` in the schema |
| `bio` | `TextField` | No length limit, so no `max_length` |

You did not declare a primary key. Django adds one automatically: an `id` column, `BigAutoField`, because `blog/apps.py` sets `default_auto_field`.

> **DOCS** — [Model field reference](https://docs.djangoproject.com/en/5.2/ref/models/fields/) · [`CharField`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#charfield) · [`TextField`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#textfield) · [Automatic primary keys](https://docs.djangoproject.com/en/5.2/topics/db/models/#automatic-primary-key-fields)

### `blank=True` is not `null=True`

The single most common early confusion, so get it straight now:

| Option | Layer | Means |
| --- | --- | --- |
| `blank=True` | **Validation** (forms, admin) | The field may be left empty in a form |
| `null=True` | **Database** | The column may store `NULL` |

`bio = models.TextField(blank=True)` means you can save an author with no bio, and it is stored as an empty string `''` — not `NULL`. For text fields prefer this: it avoids having two different representations of "no value".

> **DOCS** — [`null`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#null) · [`blank`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#blank) · [`null` vs `blank`](https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.Field.null)

### `db_table = "authors"`

Without this line the table would be `blog_author`. With it, the table is `authors`.

**WHY you would set it:**

- **Legacy databases.** The table already exists and is called `authors`. You cannot rename it — other systems read it.
- **Shared databases.** A DBA or another team owns the schema and has a naming standard your Django app must follow.
- **Cross-app clarity.** `blog_author` leaks the app name into the schema. If the app is ever renamed or the model moved, the table name becomes actively misleading.

**WHY you often should not** — the default is predictable and self-documenting: any developer can look at a table and know which app owns it. Override deliberately, not by habit.

### `__str__`

Not a `Meta` option — a regular method. It controls how the object is labelled in the admin, in the shell, and anywhere it is coerced to a string. Without it the admin shows `Author object (1)`, which is useless. Every model should define one.

> **DOCS** — [`__str__()`](https://docs.djangoproject.com/en/5.2/ref/models/instances/#django.db.models.Model.__str__)

## 4.3 Generate the migration

**TYPE**

```bash
python manage.py makemigrations blog
```

**EXPECT**

```
Migrations for 'blog':
  blog/migrations/0001_initial.py
    + Create model Author
```

Compare this with 2.4, where the same command reported `No changes detected`. Now there is a model, so there is a change to record.

> **DOCS** — [`makemigrations`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#makemigrations)

## 4.4 Read the migration before applying it

Never run a migration you have not read. It is the only chance you get to catch a destructive operation before it happens.

**TYPE**

```bash
cat blog/migrations/0001_initial.py
```

**EXPECT**

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('bio', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'authors',
            },
        ),
    ]
```

| Part | Meaning |
| --- | --- |
| `initial = True` | The first migration for this app — nothing precedes it |
| `dependencies` | Empty, for the same reason. Later migrations will list `('blog', '0001_initial')`. |
| `CreateModel` | Builds the whole table in one operation |
| The `id` field | You never wrote it. Django added it. |
| `options={'db_table': 'authors'}` | Your `Meta` — carried into the migration |

**Note what is absent:** `blank=True` appears on `bio`, but there is no `NULL` handling, because `blank` is a validation rule, not a schema one. Confirm that in the SQL next.

**TYPE** — see the real SQL, without running it:

```bash
python manage.py sqlmigrate blog 0001
```

**EXPECT**

```sql
BEGIN;
--
-- Create model Author
--
CREATE TABLE "authors" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" varchar(100) NOT NULL,
    "bio" text NOT NULL
);
COMMIT;
```

Read that carefully — it is the most clarifying thirty seconds of the day:

- The table is `"authors"`, not `"blog_author"`. That is your `db_table`.
- `"bio" text NOT NULL` — **`blank=True` did not make the column nullable.** Exactly as described in 4.2. An empty bio is stored as `''`.
- `"id"` exists although you never declared it.
- `varchar(100)` comes straight from `max_length=100`. That is what `max_length` is *for*.

> **DOCS** — [Migration operations reference](https://docs.djangoproject.com/en/5.2/ref/migration-operations/) · [`CreateModel`](https://docs.djangoproject.com/en/5.2/ref/migration-operations/#createmodel) · [`sqlmigrate`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#sqlmigrate)

## 4.5 Apply it

**TYPE**

```bash
python manage.py migrate
```

**EXPECT**

```
Operations to perform:
  Apply all migrations: admin, auth, blog, contenttypes, sessions
Running migrations:
  Applying blog.0001_initial... OK
```

**TYPE** — confirm the recorded state:

```bash
python manage.py showmigrations blog
```

**EXPECT** — `[X]` means applied:

```
blog
 [X] 0001_initial
```

> **DOCS** — [`migrate`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#migrate) · [`showmigrations`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#showmigrations)

## 4.6 Verify the table is really called `authors`

**TYPE**

```bash
python manage.py dbshell
```

```sql
.tables
.schema authors
.quit
```

**EXPECT** — `authors` in the table list, and no `blog_author` anywhere.

**TYPE** — or from the Django shell, which also proves the model works end to end:

```bash
python manage.py shell
```

```python
>>> from blog.models import Author
>>> Author._meta.db_table
'authors'
>>> Author.objects.create(name="Ursula K. Le Guin", bio="")
<Author: Ursula K. Le Guin>
>>> Author.objects.count()
1
>>> exit()
```

`Author._meta.db_table` is how you ask Django what table a model maps to, without guessing.

> **DOCS** — [`dbshell`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#dbshell) · [`shell`](https://docs.djangoproject.com/en/5.2/ref/django-admin/#shell) · [Making queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/) · [QuerySet API](https://docs.djangoproject.com/en/5.2/ref/models/querysets/)

> **CHECKPOINT 2** — `Author._meta.db_table` returns `'authors'`, and you can create and count an `Author` from the shell.

## 4.7 Setting `db_table` on a model that already has rows

You set `db_table` when creating the model, so Django emitted a single `CREATE TABLE`. Adding it to a model that is **already in the database** is a different operation, and it is worth knowing what happens.

Django compares the model state recorded in previous migrations against your current models, sees that only the table name differs, and generates:

```python
migrations.AlterModelTable(name='author', table='authors')
```

which emits:

```sql
ALTER TABLE "blog_author" RENAME TO "authors";
```

A **rename**, not a drop-and-recreate — so every existing row survives. Foreign keys pointing at the model survive too, because they reference the *model*, not a table-name string; Django regenerates the constraints against the new name.

You will not run this today. Recognise it when you meet it.

> **DOCS** — [`AlterModelTable`](https://docs.djangoproject.com/en/5.2/ref/migration-operations/#altermodeltable)

## 4.8 Migrations are code — commit them

A migration file is as much a part of your source as the model. The model says what the schema *should* be; the migration says how to *get there* from what shipped last time. Without it, a teammate's database never changes and the two silently diverge.

**TYPE**

```bash
git status
git add blog/models.py blog/migrations/0001_initial.py
```

**A trap worth knowing**, because it is silent: gitignore is only consulted for **untracked** files. Add a directory rule to a folder that is already partly tracked and the existing files keep showing as modified while *new* ones disappear from `git status` entirely. You then commit a model change whose migration was never staged, and every clone's `migrate` quietly does nothing.

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

## 6.1 Open it, before registering anything

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
```

**There is no `BLOG` section, and no `Authors`.** You have a model. You migrated it. The table exists and you put a row in it from the shell in 4.6. It still does not appear.

That is the lesson: **`INSTALLED_APPS` gets Django to load your model; `admin.py` gets it into the admin.** They are separate steps.

## 6.2 Register the model

Edit `blog/admin.py`:

```python
from django.contrib import admin

from .models import Author


admin.site.register(Author)
```

Reload <http://127.0.0.1:8000/admin/>. No restart needed — `runserver` reloads on file change.

**EXPECT**

```
AUTHENTICATION AND AUTHORIZATION
    Groups
    Users

BLOG
    Authors
```

Click **Authors**. The row you created in 4.6 is listed, labelled `Ursula K. Le Guin` — that is your `__str__` doing its job. Delete the `__str__` method and reload to see `Author object (1)` instead, then put it back.

**A model that is not registered does not appear in the admin at all.** That is the single most common "why can't I see my model" answer.

> **DOCS** — [`admin.site.register`](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.AdminSite.register)

## 6.3 Configure the change list with a `ModelAdmin`

Plain registration gives you defaults: one column, no search, no filters. To control the page, attach a `ModelAdmin`.

Replace the contents of `blog/admin.py`:

```python
from django.contrib import admin

from .models import Author


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("name", "bio")
    search_fields = ("name",)
    ordering = ("name",)
    list_per_page = 25
```

There are two registration styles, and both are fine:

- `@admin.register(Author)` — decorator, attaches the `ModelAdmin` class
- `admin.site.register(Author)` — plain call, Django uses defaults

Reload and match each option to what changed on the page:

| Option | Effect on the page | Docs |
| --- | --- | --- |
| `list_display` | The columns in the change list. Without it you get one column of `__str__`. | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display) |
| `search_fields` | Adds the search box above the list | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.search_fields) |
| `ordering` | Default sort. A leading `-` means descending — `("-name",)`. | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.ordering) |
| `list_per_page` | Rows before pagination kicks in | [ref](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_per_page) |

Three more you will need as soon as the model has relationships, on Day 3:

| Option | For |
| --- | --- |
| `list_filter` | The filter sidebar on the right | 
| `filter_horizontal` | Turns a many-to-many box into the two-pane chooser |
| `raw_id_fields` | Replaces a huge foreign-key dropdown with a lookup widget |

Once `Author` has related models, `search_fields` can reach across them: `search_fields = ("name", "post__title")`. The double underscore means "traverse the relationship", and it is the same syntax used throughout the ORM — `Author.objects.filter(post__title__icontains="django")`.

> **DOCS** — [`ModelAdmin` options](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#modeladmin-options) · [Field lookups](https://docs.djangoproject.com/en/5.2/topics/db/queries/#field-lookups) · [Lookups that span relationships](https://docs.djangoproject.com/en/5.2/topics/db/queries/#lookups-that-span-relationships)

## 6.4 Confirm the table name end to end

1. In the admin, click **Authors** → **Add author**. Give it a name and a bio. **Save**.
2. Stop the server and check where that write actually landed:

```bash
python manage.py shell -c "
from blog.models import Author
a = Author.objects.last()
print(Author._meta.db_table, '|', a.name, '|', a.bio[:40])
"
```

**EXPECT** — `authors | <name> | <your bio text>`

**TYPE** — and confirm it against the database directly, bypassing Django entirely:

```bash
python manage.py dbshell
```

```sql
SELECT id, name FROM authors;
.quit
```

You created a row through a web form, and it was written to a table called `authors`. Neither the admin nor your form nor your query mentioned that name anywhere except one line of `Meta`. The model name stayed `Author`, the admin label stayed "Authors", and the table underneath is whatever you said it should be — that separation is the point of an ORM.

> **CHECKPOINT 4 — Day 2 complete.** You can log into `/admin/`, see **BLOG → Authors**, add an author through the form, and confirm the row is in the `authors` table.


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
```

**EXPECT** — nine files staged, and **the migration must be among them**:

```
Changes to be committed:
	modified:   config/settings.py
	new file:   blog/__init__.py
	new file:   blog/admin.py
	new file:   blog/apps.py
	new file:   blog/migrations/0001_initial.py
	new file:   blog/migrations/__init__.py
	new file:   blog/models.py
	new file:   blog/tests.py
	new file:   blog/views.py
```

If `blog/migrations/0001_initial.py` is missing from that list, stop and re-read 4.8 — do not commit without it.

**TYPE**

```bash
git commit -m "Day 2: add blog app with Author model mapped to the authors table"
git push -u origin <first_name>/day2
```

Confirm on GitHub that the branch contains:

- [ ] `blog/models.py` with `Author` and `db_table = "authors"`
- [ ] `blog/migrations/0001_initial.py`
- [ ] `blog/admin.py` registering `Author`
- [ ] `config/settings.py` listing `'blog'` in `INSTALLED_APPS`
- [ ] **no** `db.sqlite3`, **no** `venv/`, **no** `__pycache__/`

The database is deliberately absent. Your classmate rebuilds their own by running `migrate` — that is what migrations are for. That only works if the migration is committed, which is why it has its own checkbox above.

## 7.1 Prove it worked

The real test of a commit is whether someone else can use it. Clone your own branch somewhere else and rebuild from scratch:

```bash
cd /tmp
git clone -b <first_name>/day2 <repo-url> verify-day2
cd verify-day2
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py dbshell -c ".tables"
```

**EXPECT** — `authors` appears in the table list, on a database that did not exist sixty seconds ago. That is your migration doing its job.

Clean up with `cd /tmp && rm -rf verify-day2`.

\newpage

# Appendix A — Troubleshooting

| You see | It means | Fix |
| --- | --- | --- |
| `No installed app with label 'blog'` | Not in `INSTALLED_APPS`, or a typo | Check `config/settings.py`, then `manage.py check` |
| `ModuleNotFoundError: No module named 'blog'` | Listed in settings but the directory is missing or misnamed | `ls blog/`; re-run `startapp` |
| `No changes detected` after editing a model | Wrong app label, or you edited a file Django does not load | `python manage.py makemigrations` with no app label |
| `table "authors" already exists` | The migration state and the database disagree | `showmigrations`; on a lab DB, delete `db.sqlite3` and `migrate` again |
| Model saved to `blog_author`, not `authors` | `db_table` added after the table was created, migration not made | `makemigrations blog` — you should get `AlterModelTable` (4.7) |
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
python manage.py makemigrations blog      # one app
python manage.py sqlmigrate blog 0001     # show the SQL, run nothing
python manage.py migrate                  # apply
python manage.py showmigrations           # [X] applied, [ ] pending
python manage.py migrate blog zero        # roll all of blog's migrations back

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
2. Run `makemigrations blog` at 2.4 with an empty `models.py` and let the room see `No changes detected`. Then write the model in 4.2 and run the same command. Same command, different answer — that is what a migration *is*.
3. Run `sqlmigrate` before `migrate`, every time, all week. Make reading generated SQL a reflex. On Day 2 the payoff is `"bio" text NOT NULL` — the line that settles `null` vs `blank` for good.
4. Open `/admin/` at 6.1 **before** writing `admin.py`. The model exists, the table exists, the row exists, and the admin still shows nothing. Then register it. Two separate steps, felt rather than told.
5. Deliberately break it: delete `__str__`, reload, watch `Author object (1)`. Restore.

**Things that reliably confuse the room**

| Confusion | Say this |
| --- | --- |
| "The admin says Authors but the table is `authors` — which is it?" | Both. The admin reads the class name; the table name is a database detail the ORM hides. That separation is the point. |
| "Why did `makemigrations blog` say no changes?" | Migrations describe model changes. Before Part 4 there were no models, so no changes. Not an error. |
| "I set `blank=True` so why is the column `NOT NULL`?" | `blank` is form validation, `null` is the database. Point at the `sqlmigrate` output. |
| "My model is migrated but not in the admin" | `INSTALLED_APPS` loads it; `admin.py` registers it. Two steps. |
| "Do I commit migrations?" | Yes. Always. They are source code. |
| "Do I commit `db.sqlite3`?" | Never. Your classmate rebuilds it with `migrate`. |
| "It says no such table" | You made the migration but did not apply it. |

**Watch for** — students on Windows hitting `Set-ExecutionPolicy` again in a new terminal, and students who never reactivated the venv (`django-admin: command not found`). Both are Day 1 issues resurfacing; point at `README-day1.md` §5.2 rather than re-teaching.

**The one to check before they leave** — that `blog/migrations/0001_initial.py` is actually committed. A student who commits `models.py` alone has a branch nobody else can build, and the failure only shows up when someone clones it. Part 7.1 makes them prove it; make sure they run it.

**Time budget** — Parts 1–2 about 30 minutes, Part 3 about 20 (discussion, no typing), Part 4 about 40 including `sqlmigrate` and verification, Parts 5–6 about 35. Roughly two and a quarter hours with questions.
