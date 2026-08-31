# Django Practical Lab

Course repository for *Django Framework Backend Development*. It holds the
per-day lab sheets and the Django project students build against.

```
django-lab/
├── README.md                ← you are here
├── manage.py                ← the project lives at the repository root
├── requirements.txt         ← pinned; install from this, not from `pip install django`
├── config/                  ← project settings and the root URLconf
├── blog/                    ← the app; `Author` model (Day 2), views and API (Day 3)
└── guides/
    ├── README-day1.md       ← GitHub auth, cloning, branching, venv
    ├── README-day2.md       ← apps, INSTALLED_APPS, db_table, migrations, admin
    └── README-day3.md       ← views, templates, DRF, JWT auth, OpenAPI docs
```

---

## 1. Set up

```bash
git clone https://github.com/kode-mafia008/django-lab.git
cd django-lab

python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

| URL | Shows |
| --- | --- |
| <http://127.0.0.1:8000/admin/> | the admin — log in with the superuser you just made |

The admin is currently the only route, and **Authors** is the only app listed in
it. `blog` has the `Author` model from Day 2 but no views yet, so there is no
public page to visit — that is where Day 3 starts.

Full step-by-step setup, including the GitHub authentication you need before
the `git clone` above will work, is in `guides/README-day1.md`.

---

## 2. Work through the guides

| Guide | Covers |
| --- | --- |
| [`guides/README-day1.md`](guides/README-day1.md) | Personal Access Tokens, SSH keys, cloning, branching off `main`, virtual environments, `requirements.txt`, pushing to your own branch |
| [`guides/README-day2.md`](guides/README-day2.md) | Projects vs apps, `startapp`, `INSTALLED_APPS`, URL resolution, `Meta.db_table`, reading migrations with `sqlmigrate`, `createsuperuser`, `ModelAdmin` |
| [`guides/README-day3.md`](guides/README-day3.md) | Views, URLconfs and templates, rendering the author list, Django REST Framework serializers and viewsets, JWT register/login/refresh/logout with Simple JWT, OpenAPI docs with drf-spectacular |

Each guide is written to be typed, not skimmed: every command is given verbatim,
every expected output is the real output, and each section ends in a checkpoint
you should reach before moving on. Every Django concept links to the official
documentation at `docs.djangoproject.com/en/5.2/`.

### Branch naming

Work for each day goes on its own branch, off an up-to-date `main`:

```
{first_name}/day{N}
```

Lowercase first name, forward slash, no spaces — `priya/day1`, `arjun/day2`.

```bash
git switch main
git pull origin main
git switch -c <first_name>/day2
```

---

## 3. The `catalog` reference app

Some exercises — Day 2 Parts 4 and 6 in particular — are written against a
`catalog` app with `Author`, `Book`, `Genre` and `AuthorProfile` models.

**`catalog` is not in this repository.** It is trainer-owned reference material
and is distributed separately. If you are following Day 2 and do not have it,
ask the trainer; the concepts (`Meta.db_table`, `AlterModelTable`, `ModelAdmin`
options) transfer unchanged to any model you have.

Everything else in both guides runs against what is in this repo.

---

## 4. What is deliberately not committed

| Path | Why |
| --- | --- |
| `venv/` | Contains binaries built for one OS and CPU. Rebuild it from `requirements.txt`. |
| `db.sqlite3` | Rebuild it with `migrate`. Never commit a database. |
| `__pycache__/`, `*.pyc` | Generated. |
| `.env`, `*.pem` | Secrets. |
| `catalog/`, `seed.py`, `lab.css` | Trainer-owned; see above. |
| `guides/django-practical-lab.md`, `guides/*.html` | The long-form trainer manual and its generated output. |

Migrations are the opposite case — **always commit them.** A migration is source
code: the model says what the schema should be, the migration says how to get
there. Without it, a teammate's database never changes and silently diverges
from the models.

---

## Versions

| | Pinned for the cohort | Verified working here |
| --- | --- | --- |
| Python | 3.12.x | 3.14.6 |
| Django | 5.2 LTS | 5.2.17 |
| Database | SQLite | SQLite |

Pin **Python 3.12** for students — Django 5.2's officially supported range is
3.10–3.13, and a whole cohort on one version means everyone hits the same
behaviour. Confirm the current Django LTS at
<https://www.djangoproject.com/download/> before term starts.
