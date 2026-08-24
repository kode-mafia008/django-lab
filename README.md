# Django Practical Lab — Foundation & Django Core

Teaching materials and a working reference project for Modules 1–7 of
*Django Framework Backend Development* (30 of the course's 62 contact hours).

```
django-lab/
├── README.md                    ← you are here
├── manage.py                    ← the reference project lives at the root
├── requirements.txt
├── seed.py
├── config/                      ← project settings, root URLconf
├── catalog/                     ← the app: models, views, templates, admin
└── guides/
    ├── django-practical-lab.html   ← the lab manual. Open this in a browser.
    ├── django-practical-lab.md     ← markdown source of the manual
    └── build-html.sh               ← regenerates the HTML from the markdown
```

---

## 1. Read the lab manual

Open `guides/django-practical-lab.html` in any browser — double-click it, or:

```bash
open guides/django-practical-lab.html          # macOS
xdg-open guides/django-practical-lab.html      # Linux
start guides/django-practical-lab.html         # Windows
```

It needs no server and no internet. Everything is inlined.

It contains seven sessions, one per module, each with timed demos, the exact
commands to type, the output to expect, deliberate errors to stage, and a
checkpoint nobody moves past until they reach it.

To regenerate the HTML after editing the markdown:

```bash
bash guides/build-html.sh
```

---

## 2. Run the reference project

The project at the repository root is the **finished state** — what a student's
project looks like at the end of Session 7. Use it to demo the target, or to
diff against a student who is stuck.

It is already set up: virtual environment created, Django installed, database
migrated, and ten books seeded.

```bash
source venv/bin/activate        # macOS / Linux
# venv\Scripts\Activate.ps1     # Windows PowerShell

python manage.py runserver
```

| URL | Shows |
| --- | --- |
| <http://127.0.0.1:8000/catalog/books/> | book list — templates, `select_related`, partials |
| <http://127.0.0.1:8000/catalog/books/1/> | book detail — `get_object_or_404`, relationships |
| <http://127.0.0.1:8000/catalog/search/?q=dune> | search — `Q` objects, filtering across a `ForeignKey` |
| <http://127.0.0.1:8000/catalog/about/> | a static page sharing the same base template |
| <http://127.0.0.1:8000/admin/> | the admin — `ModelAdmin` configuration |

**Admin login:** `admin` / `admin12345`

> This is a throwaway local password for a teaching sandbox, and `db.sqlite3`
> is gitignored so it never leaves your machine. Never use a password like this
> anywhere real — Module 13 covers why.

### Reset the sample data

```bash
python manage.py shell < seed.py
```

Safe to re-run; it clears the catalog tables first.

### Start over completely

```bash
rm db.sqlite3
python manage.py migrate
python manage.py shell < seed.py
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com \
  DJANGO_SUPERUSER_PASSWORD=admin12345 python manage.py createsuperuser --noinput
```

---

## 3. What the reference project demonstrates

| Session | Concept | Where to look |
| --- | --- | --- |
| 4 | URLs, `include()`, path converters, views | `config/urls.py`, `catalog/urls.py`, `catalog/views.py` |
| 5 | Template inheritance, `{% static %}`, partials | `catalog/templates/catalog/`, `catalog/static/catalog/` |
| 6 | Models, `null` vs `blank`, `__str__`, `Meta`, admin | `catalog/models.py`, `catalog/admin.py` |
| 6 | Migrations | `catalog/migrations/0001_initial.py` |
| 7 | One-to-many — `ForeignKey` | `Book.author` |
| 7 | Many-to-many — join table | `Book.genres` |
| 7 | One-to-one | `AuthorProfile.author` |
| 7 | Query optimisation | `select_related` / `prefetch_related` in `catalog/views.py` |
| 7 | `Q` objects and search | `catalog/views.py::book_search` |

### See the generated SQL

The single most clarifying command in Session 6:

```bash
python manage.py sqlmigrate catalog 0001
```

### See the N+1 problem

```bash
python manage.py shell
```

```python
>>> from catalog.models import Book
>>> for b in Book.objects.all():            # 1 + 10 queries
...     print(b.title, b.author.name)
>>> for b in Book.objects.select_related("author"):   # 1 query
...     print(b.title, b.author.name)
```

To watch the queries scroll past, uncomment the `LOGGING` block at the bottom
of `config/settings.py`.

---

## Versions

| | Pinned in the manual | Verified working here |
| --- | --- | --- |
| Python | 3.12.x | 3.14.6 |
| Django | 5.2 LTS | 5.2.17 |
| Database | SQLite | SQLite |

The manual pins **Python 3.12** because it is the widest-supported version for
a whole cohort — Django 5.2's officially supported range is 3.10–3.13. This
machine happens to run 3.14 and the project works on it, but pin 3.12 for
students so everyone hits the same behaviour. Confirm the current Django LTS on
<https://www.djangoproject.com/download/> before term starts.
