---
title: "Day 10 — API Security"
subtitle: "Authentication is not authorisation: ownership, rate limits, tokens, and the deployment checklist"
author: "Django Practical Lab — daily guide series"
date: "Django 5.2 LTS · DRF 3.18 · Simple JWT 5.5 · drf-spectacular 0.30"
---

# What we did today

| # | Task | Command / change | Result |
| --- | --- | --- | --- |
| 1 | Attacked our own API | `curl` | Six real holes, found in ten minutes |
| 2 | Closed the default | `DEFAULT_PERMISSION_CLASSES` | Every new endpoint is private until it says otherwise |
| 3 | Bounded every list | `PageNumberPagination`, `PAGE_SIZE` | `{count, next, previous, results}` |
| 4 | Gave rows an owner | `Blog.owner` + `0004_blog_owner` | The server records who wrote a row |
| 5 | Wrote an object permission | `blog/permissions.py` | A stranger's `PATCH` is a `403` |
| 6 | Scoped the queryset | `BlogViewSet.get_queryset()` | Somebody else's draft is a `404`, not a `403` |
| 7 | Stopped trusting the body | `perform_create` + `read_only_fields` | `"owner": 3` in the JSON changes nothing |
| 8 | Rate-limited the door | `ScopedRateThrottle`, `"auth": "5/min"` | The sixth password guess is a `429` |
| 9 | Rate-limited an HTML page | `blog/throttling.py` + `PAGE_THROTTLE_RATES` | The 31st read of a post is a `429` |
| 10 | Read a JWT without the key | `base64` | Signed is not encrypted — no secrets in claims |
| 11 | Rotated and blacklisted tokens | `SIMPLE_JWT` | A replayed refresh token is `"Token is blacklisted"` |
| 12 | Locked the HTML pages | `@login_required` + ownership | 26 Day-9 tests went red, which was the point |
| 13 | Took the secret out of git | `DJANGO_SECRET_KEY`, `.env.example` | `check --deploy` exits clean |

Everything below runs against this repository as it stands at the end of Day 9: a `blog` app with
HTML CRUD over `Blog`, a JSON API under `/api/`, and an `accounts` app issuing JWTs.

Today's scope is **the application's own access control**. Transport security (certificates,
firewalls), infrastructure hardening and dependency scanning are named in **Appendix E** and are not
built today.

## Conventions

Same as Days 1–8.

| Marker | Meaning |
| --- | --- |
| **TYPE** | Type this exactly. |
| **EXPECT** | What should appear. If you see something else, stop and fix it. |
| **CHECKPOINT** | A verifiable state. Nobody moves on until everyone reaches it. |
| **WHY** | The reasoning. Read it before the exam. |
| **DOCS** | The official documentation for what you just did. |

Django links point at `/en/5.2/`, matching `requirements.txt`. Today adds no new package —
permissions, throttling and pagination all ship inside DRF, and the environment handling is
`os.environ`.

## Start here

**TYPE**

```bash
cd ~/code/django-lab
source venv/bin/activate      # Windows: venv\Scripts\Activate.ps1
git switch main
git pull origin main
git switch -c <first_name>/day10
```

If your Day 9 work lives on your own branch and is not on `main` yet, branch from that instead —
today edits the files you wrote yesterday.

**TYPE**

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py test
```

**EXPECT** — the suite is green before you change anything.

```
Ran 39 tests in 0.588s

OK
```

Your number will differ if you added tests on Day 9. Green is what matters, not 39.

**TYPE** — two accounts and some data to attack. If you already have users, use those.

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from blog.models import Author, Blog
User.objects.create_user('asha', password='lab-passphrase-2026')
User.objects.create_user('bello', password='lab-passphrase-2026')
a = Author.objects.create(name='Jane Austen', bio='Novelist.')
Blog.objects.create(title='Ashas published post', content='Body.', author=a, published=True)
Blog.objects.create(title='Ashas unfinished draft', content='Not ready for anyone.', author=a)
print('seeded')
"
```

**CHECKPOINT 0** — you are on `<first_name>/day10`, the tests pass, and `python manage.py runserver`
serves <http://127.0.0.1:8000/blogs/posts/>. Leave the server running in one terminal; every `curl`
today goes in a second one.

\newpage

# Part 1 — Attack it first

Nothing in this part changes a line of code. You are going to use the app the way somebody who did
not write it would use it, and write down what it lets you do.

Two users exist: **asha**, who wrote both posts, and **bello**, who is a stranger with a valid
account. That is the entire threat model for the next twenty minutes, and it is the most common one
in real life: the attacker is not anonymous, the attacker is a customer.

## 1.1 Log in as the stranger

**TYPE**

```bash
BELLO=$(curl -s -X POST http://127.0.0.1:8000/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"bello","password":"lab-passphrase-2026"}' \
  | python -c "import json,sys; print(json.load(sys.stdin)['access'])")
echo ${BELLO:0:40}...
```

**EXPECT** — a token prefix. Windows PowerShell users: see Appendix A for the `curl.exe` form.

## 1.2 Read everything, including the drafts

**TYPE**

```bash
curl -s http://127.0.0.1:8000/api/blogs/ -H "Authorization: Bearer $BELLO" | python -m json.tool
```

**EXPECT**

```json
[
  {
    "id": 2,
    "title": "Ashas unfinished draft",
    "published": false,
    ...
  },
  {
    "id": 1,
    "title": "Ashas published post",
    "published": true,
    ...
  }
]
```

Two findings in one response.

* `published: false` is in there. A draft is a thing somebody decided *not* to publish, and the API
  hands it to any account on the system.
* The response is a bare JSON array. No `count`, no `next`. Ten thousand rows would all arrive in
  one response, and the way to find out how much that costs is for somebody to do it to you.

## 1.3 Edit a post you did not write

**TYPE**

```bash
curl -s -X PATCH http://127.0.0.1:8000/api/blogs/1/ \
  -H "Authorization: Bearer $BELLO" -H "Content-Type: application/json" \
  -d '{"title":"Defaced by bello"}' -w "\nstatus=%{http_code}\n"
```

**EXPECT**

```json
{"id":1,"title":"Defaced by bello","content":"Body.","author":1,"published":true, ...}
status=200
```

**TYPE**

```bash
curl -s -X DELETE http://127.0.0.1:8000/api/blogs/2/ \
  -H "Authorization: Bearer $BELLO" -o /dev/null -w "status=%{http_code}\n"
```

**EXPECT**

```
status=204
```

Bello just rewrote one of asha's posts and deleted another. Nothing failed. Nothing was logged. The
API did exactly what it was written to do.

**WHY this is the important one** — the industry name for it is **Broken Object Level
Authorization**, and it has been number one on the OWASP API Security Top 10 since the list existed.
It is not exotic. It is what you get by default, because `IsAuthenticated` answers *"is this a real
user?"* and every URL in a REST API contains a row id that the caller is free to change.

## 1.4 The HTML pages need no account at all

**TYPE** — no token, no session, no login.

```bash
curl -s http://127.0.0.1:8000/blogs/posts/new/ -o /dev/null -w "GET  /blogs/posts/new/ -> %{http_code}\n"
```

**EXPECT**

```
GET  /blogs/posts/new/ -> 200
```

The form renders for anybody. Post it — the CSRF token has to come from the page, which is exactly
what a script does:

**TYPE**

```bash
curl -s -c /tmp/c.txt http://127.0.0.1:8000/blogs/posts/new/ -o /tmp/form.html
TOKEN=$(python -c "
import re; print(re.search(r'name=\"csrfmiddlewaretoken\" value=\"([^\"]+)\"', open('/tmp/form.html').read()).group(1))")
curl -s -b /tmp/c.txt -X POST http://127.0.0.1:8000/blogs/posts/new/ \
  -d "csrfmiddlewaretoken=$TOKEN&title=Written by a stranger&author=1&content=Nobody asked me to log in" \
  -o /dev/null -w "POST /blogs/posts/new/ -> %{http_code}\n"
```

**EXPECT**

```
POST /blogs/posts/new/ -> 302
```

A 302 is the redirect-after-save from Day 9. The row is in the database, written by nobody.

**WHY** — CSRF protection worked perfectly here, and it did not help at all. CSRF stops *another
site* from making a browser submit this form. It has nothing to say about who may submit it. The
two are unrelated controls and people constantly assume the first one implies the second.

## 1.5 Guess passwords all day

**TYPE**

```bash
for i in 1 2 3 4 5 6 7 8; do
  printf "%s " "$(curl -s -o /dev/null -w '%{http_code}' -X POST http://127.0.0.1:8000/accounts/login/ \
    -H 'Content-Type: application/json' -d '{"username":"asha","password":"guess"}')"
done; echo
```

**EXPECT**

```
401 401 401 401 401 401 401 401
```

Eight in about a second, and the eighth is as welcome as the first. At that rate a four-digit PIN
falls in under twenty minutes, and the list of the ten thousand most common passwords falls
overnight.

## 1.6 The 404 page is a site map

**TYPE**

```bash
curl -s http://127.0.0.1:8000/nope | grep -o "Using the URLconf defined in [a-z.]*"
```

**EXPECT**

```
Using the URLconf defined in config.urls
```

Open <http://127.0.0.1:8000/nope> in a browser and read the whole page:

```
Using the URLconf defined in config.urls, Django tried these URL patterns, in this order:
  admin/   blogs/   accounts/   api/   api/schema/ [name='schema']   ...
The current path, nope, didn't match any of these.
You're seeing this error because you have DEBUG = True in your Django settings file.
```

That is every route in the project, published to anyone who mistypes a URL. On an exception page
`DEBUG = True` goes further and prints local variables and settings.

## 1.7 Ask Django what it thinks

**TYPE**

```bash
python manage.py check --deploy
```

**EXPECT**

```
WARNINGS:
?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting. ...
?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True. ...
?: (security.W009) Your SECRET_KEY has less than 50 characters, less than 5 unique characters, or
   it's prefixed with 'django-insecure-' ...
?: (security.W012) SESSION_COOKIE_SECURE is not set to True. ...
?: (security.W016) You have 'django.middleware.csrf.CsrfViewMiddleware' in your MIDDLEWARE, but you
   have not set CSRF_COOKIE_SECURE to True. ...
?: (security.W018) You should not have DEBUG set to True in deployment.

System check identified 6 issues (0 silenced).
```

**TYPE** — and the key itself is not just weak, it is public.

```bash
git log -p --all -- config/settings.py | grep -c "SECRET_KEY = 'django-insecure"
```

**EXPECT** — a number greater than zero. Every commit that ever touched the file still contains the
key. Changing the line does not remove it from history; only rotating the key does.

## 1.8 The scoreboard

| # | What you did | The industry name for it | Fixed in |
| --- | --- | --- | --- |
| 1 | Read somebody else's draft | Broken object level authorization | Part 4 |
| 2 | Edited and deleted another user's row | Broken object level authorization | Part 3 |
| 3 | Wrote rows with no account at all | Broken function level authorization | Part 8 |
| 4 | Guessed passwords without limit | Unrestricted resource consumption | Part 5 |
| 5 | Pulled every row in one request | Unrestricted resource consumption | Part 2 |
| 6 | Read the URLconf off a 404 page | Security misconfiguration | Part 9 |

**CHECKPOINT 1** — everybody has seen a `200` on a `PATCH` they had no right to make. If somebody
got a `403`, they are on the Day 8 settings where `DjangoModelPermissionsOrAnonReadOnly` was in
force — read Appendix A, then carry on; today rewrites that setting anyway.

> **DOCS** — [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) ·
> [Django security overview](https://docs.djangoproject.com/en/5.2/topics/security/) ·
> [Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

\newpage

# Part 2 — Two different questions

Every request that reaches a view has already been asked one question and is about to be asked
another. Keeping them apart is most of what this day is.

| Question | Answered by | Failure looks like |
| --- | --- | --- |
| **Who are you?** — authentication | `DEFAULT_AUTHENTICATION_CLASSES`; sets `request.user` | `401 Unauthorized` |
| **What may you do?** — authorisation | `permission_classes` | `403 Forbidden` |

A `401` means *"I do not know who you are"*. A `403` means *"I know exactly who you are, and no."*
When a caller sends no credential at all, DRF returns `401` only if an authentication class has a
`WWW-Authenticate` header to offer; otherwise it collapses to `403`. That is why the same missing
token can produce either code depending on which authentication classes are installed.

## 2.1 What was in the settings

Open `config/settings.py` and find `REST_FRAMEWORK`. Today's starting state:

```python
# Do not keep this. It is what we are replacing.
"DEFAULT_PERMISSION_CLASSES": [
    "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
]
```

This line arrived by copy-paste from the drf-spectacular README and is wrong in two directions at
once:

* **`...OrAnonReadOnly`** — anonymous callers may read anything that does not override the default.
  That is a *publishing* decision, made globally, by a default.
* **`DjangoModelPermissions`** — writes are allowed only if the user has the matching row in
  `auth_permission`. Nobody in this project has those rows, so a perfectly valid JWT gets a `403`.
  It also requires the view to expose `.queryset`, which breaks the moment a viewset computes its
  rows in `get_queryset()` — which is exactly what we do in Part 4.

The reason it did no harm so far is that both viewsets override it with `IsAuthenticated`. A default
that is always overridden is not a default; it is a trap waiting for the next person to add a view
and forget.

## 2.2 Replace it

**TYPE** — replace the whole `REST_FRAMEWORK` block in `config/settings.py`:

```python
REST_FRAMEWORK = {
    # WHO ARE YOU — how a request is turned into `request.user`.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # WHAT MAY YOU DO — the default answer for every view that does not
    # override it. Closed by default: a new endpoint is private until its
    # author decides otherwise.
    #
    # This replaces `DjangoModelPermissionsOrAnonReadOnly`, which was pasted in
    # from the drf-spectacular README and is wrong twice over: it lets anonymous
    # callers read everything, and it ties writes to `auth_permission` rows, so
    # a perfectly valid JWT still gets a 403.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # HOW OFTEN — the cheapest defence against credential stuffing and scraping.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "240/min",
        # Views that set `throttle_scope = "auth"` — login and register.
        "auth": "5/min",
    },
    # HOW MUCH — an unpaginated list endpoint is a denial-of-service tool that
    # you built and shipped yourself.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Throttle counters live in the cache. The default local-memory cache is
# per-process, so two gunicorn workers keep two separate counts — real
# deployments point this at Redis or Memcached.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "django-lab-throttling",
    }
}
```

**TYPE**

```bash
curl -s http://127.0.0.1:8000/api/blogs/ -H "Authorization: Bearer $BELLO" | python -m json.tool | head -6
```

**EXPECT** — the list is bounded now.

```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
```

**WHY pagination is on the security list** — `count` and `next` are the polite half. The real point
is that no single request can now ask the database for an unbounded amount of work. Every
list endpoint you ship without it is a load generator with a public URL.

**CHECKPOINT 2** — `GET /api/blogs/` returns the four-key envelope, and
`curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/` with no credential now prints
`401` rather than `200`: the router's own root view inherits the new default.

> **DOCS** — [DRF permissions](https://www.django-rest-framework.org/api-guide/permissions/) ·
> [DRF authentication](https://www.django-rest-framework.org/api-guide/authentication/) ·
> [DRF pagination](https://www.django-rest-framework.org/api-guide/pagination/)

\newpage

# Part 3 — Who owns a row

`IsAuthenticated` cannot stop 1.3, and no global setting can, because the answer depends on the row.
For that, the row has to know something it does not know yet.

## 3.1 The field

`Blog` already has an `author`. It is not the answer. `author` is a `blog.Author` — a byline the
client picks from a dropdown — and three people can share one. What is missing is the account that
is allowed to change the row.

**TYPE** — in `blog/models.py`, add the import and the field:

```python
from django.conf import settings
from django.db import models
```

```python
    # `author` is attribution: whose byline goes on the post. The client picks it.
    # `owner` is the security fact: which account is allowed to change this row.
    # The client never picks that — the server records it from the credential.
    #
    # Nullable because rows written before today have no owner. That is on
    # purpose: an unowned row matches nobody, so every ownership check fails
    # closed rather than open.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blogs",
        null=True,
        blank=True,
        editable=False,
    )
```

Put it directly under `author`.

**WHY `settings.AUTH_USER_MODEL` and not `User`** — a project that later swaps in a custom user
model changes one setting. A `ForeignKey(User)` written into a migration does not follow.

**WHY `editable=False`** — it takes the field out of every `ModelForm` and out of the admin form.
A value the server owns should not be reachable from a form field at all; making it read-only in
the form is a weaker version of the same idea, and one that a later `fields = "__all__"` undoes.

**TYPE**

```bash
python manage.py makemigrations blog
python manage.py migrate
```

**EXPECT**

```
Migrations for 'blog':
  blog/migrations/0004_blog_owner.py
    + Add field owner to blog
```

## 3.2 The permission class

**TYPE** — a new file, `blog/permissions.py`:

```python
"""Object-level permissions for the blog API.

A permission class answers two different questions, and DRF asks them at two
different moments:

* `has_permission(request, view)` — asked once, before the view runs, with no
  object in hand. "May this caller use this endpoint at all?"
* `has_object_permission(request, view, obj)` — asked per row, and *only* from
  `get_object()`. "May this caller touch this particular row?"

The second one is the one APIs forget, and forgetting it is the single most
common API vulnerability there is: authenticated user A edits user B's data by
changing a number in the URL.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Anyone who got past authentication may read; only the owner may write.

    `owner` is nullable, and `None == request.user` is False for every user —
    so a row written before ownership existed is read-only for everybody. That
    is deliberate. A permission check must fail closed.
    """

    message = "You can only change posts you created."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner_id is not None and obj.owner_id == request.user.id
```

Three details worth stopping on.

* **`SAFE_METHODS`** is `("GET", "HEAD", "OPTIONS")` — the verbs that do not change anything.
* **`obj.owner_id`, not `obj.owner`** — the `_id` version is already in memory. Reading `obj.owner`
  fires a query per row unless the queryset was `select_related`.
* **`is not None` first.** Without it, an unowned row plus an anonymous-ish caller is a comparison
  of two empty things, and empty things compare equal more often than you would like.

**WHY there is no `has_permission` here** — this class only ever *adds* a row-level rule. Whether
you may be at the endpoint at all is `IsAuthenticated`'s job, and DRF ANDs the list together.
`BasePermission.has_permission` returns `True` by default, so leaving it out is the same as
"no opinion".

## 3.3 Wire it up

**TYPE** — `blog/api.py`, `BlogViewSet`:

```python
class BlogViewSet(viewsets.ModelViewSet):
    """CRUD for `blog.Blog`, backed by the `blogs` table."""

    serializer_class = BlogSerializer
    # Documentation, not a filter. drf-spectacular reads this attribute to work
    # out that `{id}` is an integer, and DRF ignores it entirely once
    # `get_queryset()` exists. Do not mistake it for the security boundary —
    # the method below is the security boundary.
    queryset = Blog.objects.all()
    # Both are checked. `IsAuthenticated` answers "may you be here"; the second
    # answers "may you touch this row". DRF ANDs the list together, and it runs
    # the object-level half only for views that call `get_object()`.
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
```

with the import at the top:

```python
from .permissions import IsOwnerOrReadOnly
```

## 3.4 Record the owner, do not accept it

A permission that compares `obj.owner` to `request.user` is worthless if the client gets to say who
the owner is. Two changes, and you want both.

**TYPE** — `blog/serializers.py`:

```python
    # Output only. The client sees who owns a post; it never gets to say so.
    # If this were writable, "create a post as somebody else" would be one
    # extra key in the JSON body.
    # `default=None` matters: without it, a row whose owner is NULL drops the
    # key from the JSON entirely instead of reporting `"owner": null`, and a
    # response shape that changes per row is a bug waiting to be written.
    owner = serializers.ReadOnlyField(source="owner.username", default=None)
```

and add `'owner'` to `fields` and to `read_only_fields`.

**TYPE** — `blog/api.py`:

```python
    def perform_create(self, serializer):
        """Stamp the owner from the credential, never from the request body.

        `serializer.save(owner=...)` lands in `validated_data`, so it wins over
        anything the client sent — and `owner` is read-only in the serializer,
        so the client could not have sent it anyway. Two locks, one door.
        """
        serializer.save(owner=self.request.user)
```

**WHY both** — `read_only_fields` stops the field being read from the body; `perform_create` decides
what the value actually is. Either alone is a correct fix today. Together they survive the day
somebody adds `owner` back to a writable serializer without reading this file.

## 3.5 Run the attack again

Restart the server, log both users in again, and have asha write a post — trying, while she is at
it, to set fields she does not own:

**TYPE**

```bash
ASHA=$(curl -s -X POST http://127.0.0.1:8000/accounts/login/ -H "Content-Type: application/json" \
  -d '{"username":"asha","password":"lab-passphrase-2026"}' | python -c "import json,sys; print(json.load(sys.stdin)['access'])")

curl -s -X POST http://127.0.0.1:8000/api/blogs/ \
  -H "Authorization: Bearer $ASHA" -H "Content-Type: application/json" \
  -d '{"title":"Written by asha","content":"Body.","author":1,"published":true,
       "owner":3,"created_at":"2000-01-01T00:00:00Z"}' | python -m json.tool
```

**EXPECT** — the two smuggled fields are gone.

```json
{
    "id": 2,
    "title": "Written by asha",
    "content": "Body.",
    "author": 1,
    "owner": "asha",
    "published": true,
    "created_at": "2026-09-06T05:50:37.943750Z",
    "updated_at": "2026-09-06T05:50:37.943760Z"
}
```

`"owner": 3` was bello's id and it was ignored. `created_at` came from `auto_now_add`, not from the
body. This class of bug is called **mass assignment**, and the defence is an allowlist —
`Meta.fields` — not a denylist of things you remembered to strip.

**TYPE** — now bello, again:

```bash
curl -s -X PATCH http://127.0.0.1:8000/api/blogs/2/ \
  -H "Authorization: Bearer $BELLO" -H "Content-Type: application/json" \
  -d '{"title":"Defaced"}' -w "\nstatus=%{http_code}\n"
```

**EXPECT**

```json
{"detail":"You can only change posts you created."}
status=403
```

**TYPE**

```bash
curl -s -X PATCH http://127.0.0.1:8000/api/blogs/1/ \
  -H "Authorization: Bearer $BELLO" -H "Content-Type: application/json" \
  -d '{"title":"Claimed"}' -w "\nstatus=%{http_code}\n"
```

**EXPECT** — post 1 predates the `owner` column, so it belongs to nobody:

```json
{"detail":"You can only change posts you created."}
status=403
```

**CHECKPOINT 3** — bello gets `403` on both a post owned by asha and a post owned by nobody, and
asha still gets `200` on her own. Anyone still seeing `200` for bello has `permission_classes` on the
wrong class, or is hitting a cached old server process.

> **DOCS** — [DRF object-level permissions](https://www.django-rest-framework.org/api-guide/permissions/#object-level-permissions) ·
> [`AUTH_USER_MODEL`](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model) ·
> [Serializer `read_only_fields`](https://www.django-rest-framework.org/api-guide/serializers/#specifying-read-only-fields)

\newpage

# Part 4 — What you are allowed to know exists

Bello can no longer *change* asha's draft. He can still read it, and he can still see it in the
list. A `403` is also an answer: it confirms that row 2 exists.

Permissions decide what you may do to a row. **The queryset decides which rows exist.**

## 4.1 Scope the queryset

**TYPE** — `blog/api.py`, replacing the plain `queryset` line's job:

```python
    def get_queryset(self):
        """The rows this caller is allowed to know about.

        Everything reachable by pk is reachable through this queryset, so
        filtering here covers `retrieve`, `update` and `destroy` too — not just
        the list. A draft belonging to somebody else is a 404, not a 403.
        """
        # `select_related` collapses the per-row author lookup that serialising
        # the foreign key would otherwise trigger.
        visible = Blog.objects.select_related("author", "owner")
        return visible.filter(Q(published=True) | Q(owner=self.request.user))
```

with `from django.db.models import Q` at the top.

**WHY this covers every action** — `get_object()` calls `filter_queryset(get_queryset())` and then
looks up the pk *inside* that result. A row the queryset excluded is not found, and DRF raises
`Http404` before any permission class is consulted. One method, five actions.

**TYPE**

```bash
curl -s http://127.0.0.1:8000/api/blogs/3/ -H "Authorization: Bearer $BELLO" -w "\nstatus=%{http_code}\n"
```

**EXPECT** — asha's draft, as far as bello is concerned, does not exist.

```json
{"detail":"No Blog matches the given query."}
status=404
```

**TYPE**

```bash
curl -s http://127.0.0.1:8000/api/blogs/ -H "Authorization: Bearer $BELLO" \
  | python -c "
import json,sys
d = json.load(sys.stdin)
print(json.dumps([{k: r[k] for k in ('id','title','owner','published')} for r in d['results']], indent=2))"
```

**EXPECT** — published rows only, and the unowned one reports `null` rather than dropping the key.

```json
[
  {
    "id": 2,
    "title": "Written by asha",
    "owner": "asha",
    "published": true
  },
  {
    "id": 1,
    "title": "A post from before ownership existed",
    "owner": null,
    "published": true
  }
]
```

Log in as asha and repeat: her draft is in her own list. Same code, different `request.user`.

## 4.2 403 or 404 — pick on purpose

Both are defensible, and the difference is what the response admits:

| Answer | Says | Use when |
| --- | --- | --- |
| `403 Forbidden` | "row exists, you may not" | The caller already knows the row exists — they followed a link to it |
| `404 Not Found` | nothing at all | Existence is itself information: private drafts, other tenants' data |

This project now uses both, deliberately: the API returns `404` for a draft that is not yours
(Part 4) and `403` for a published post that is not yours (Part 3, where the row is public anyway).
The HTML pages in Part 8 answer `403` for editing, because the person on the other end is a human
who followed a link and "you cannot edit this" is more use to them than "no such page".

What is not defensible is picking neither and finding out later which one you shipped.

**CHECKPOINT 4** — for bello: asha's draft is `404`, asha's published post is `200` to read and
`403` to change. For asha: her own draft is `200`.

> **DOCS** — [DRF filtering by the current user](https://www.django-rest-framework.org/api-guide/filtering/#filtering-against-the-current-user) ·
> [`Q` objects](https://docs.djangoproject.com/en/5.2/topics/db/queries/#complex-lookups-with-q-objects)

\newpage

# Part 5 — Rate limits

Part 1.5 guessed eight passwords in a second. Nothing in Parts 2–4 changed that: every one of those
requests was a legitimate, correctly-formed, entirely unauthorised-but-that-is-not-the-point login
attempt.

## 5.1 Three throttles, one cache

You already added the settings in Part 2. What they mean:

| Class | Counts per | Rate here |
| --- | --- | --- |
| `AnonRateThrottle` | client IP, for callers with no `request.user` | `60/min` |
| `UserRateThrottle` | user id, for authenticated callers | `240/min` |
| `ScopedRateThrottle` | `view.throttle_scope`, per view | `"auth": 5/min` |

`ScopedRateThrottle` does nothing at all to a view that does not set `throttle_scope`, which is why
it is safe to list globally. Rates are written `number/period` where period is
`second`, `minute`, `hour` or `day` — DRF reads the first character, so `5/m` and `5/min` are the
same thing.

**WHY the counters live in the cache** — throttling is per-process state, and the local-memory cache
is a dict inside one Python process. Two gunicorn workers means two counts, and an attacker gets
double the rate. The moment this project runs on more than one process, `CACHES` has to point at
Redis or Memcached. That is one settings change, and it is the whole reason `CACHES` is written
out explicitly rather than left to the default.

## 5.2 Scope the door

**TYPE** — in `accounts/views.py`, add the import and two pairs of lines:

```python
from rest_framework.throttling import ScopedRateThrottle
```

```python
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.none()
    serializer_class = RegisterSerializer
    # The one endpoint that has to be open. `AllowAny` here is a decision, not
    # an oversight — which is why it is written out rather than inherited.
    permission_classes = [AllowAny]
    # ...and an open endpoint that writes rows needs a rate limit. The "auth"
    # rate is set in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
```

```python
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    # Without this, a password is a 30-millisecond guess that can be repeated
    # forever. With it, an attacker gets five tries a minute per IP.
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"
```

## 5.3 Trip it

**TYPE**

```bash
for i in 1 2 3 4 5 6; do
  printf "attempt %s -> " $i
  curl -s -o /tmp/out.json -w "%{http_code}" -X POST http://127.0.0.1:8000/accounts/login/ \
    -H "Content-Type: application/json" -d '{"username":"asha","password":"guess"}'
  printf "  %s\n" "$(cat /tmp/out.json)"
done
```

**EXPECT**

```
attempt 1 -> 401  {"detail":"No active account found with the given credentials"}
attempt 2 -> 401  {"detail":"No active account found with the given credentials"}
attempt 3 -> 401  {"detail":"No active account found with the given credentials"}
attempt 4 -> 401  {"detail":"No active account found with the given credentials"}
attempt 5 -> 401  {"detail":"No active account found with the given credentials"}
attempt 6 -> 429  {"detail":"Request was throttled. Expected available in 60 seconds."}
```

**TYPE** — now try the *correct* password.

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/accounts/login/ \
  -H "Content-Type: application/json" -d '{"username":"asha","password":"lab-passphrase-2026"}'
```

**EXPECT**

```
429
```

**WHY that matters both ways** — the throttle runs before the view, so it never reaches the password
check. Good: an attacker who has just tried five wrong passwords cannot try a sixth right one. Also
bad: an attacker can lock *you* out of your own login by burning the rate from your IP. Rate limits
trade availability for integrity, always. Five a minute is a lab number; pick yours by measuring
what real users do, and read Appendix E on `django-axes` for per-account lockout instead of per-IP.

Wait a minute (literally) before continuing, or restart the server to clear the local-memory cache.

## 5.4 The pages get nothing for free

`DEFAULT_THROTTLE_CLASSES` is enforced by `APIView.initial()`. `blog/views.py` holds function views
that never touch DRF, so none of Part 5 applies to them — the same gap Part 8 has to close for
permissions. The busiest read in the app, `/blogs/posts/<pk>/`, is currently unlimited.

**WHY that page in particular** — it is public for published posts, it takes a row id in the URL,
and walking `1..n` through it is how somebody copies your whole site. A list page at least paginates.

**TYPE** — a new file, `blog/throttling.py`. The two functions that carry the ideas:

```python
def parse_rate(rate):
    """`"30/min"` -> `(30, 60)`. Only the first letter of the period is read."""
    count, _, period = rate.partition("/")
    return int(count), PERIODS[period[0]]


def client_key(request, scope):
    """One counter per caller per scope.

    Authenticated callers are counted by primary key, so a shared office IP
    does not make one user's reading throttle everybody else's.

    Anonymous callers are counted by `REMOTE_ADDR` and nothing else.
    `X-Forwarded-For` is supplied by the client and forgeable, so trusting it
    hands an attacker an unlimited supply of fresh counters — read it only
    behind a proxy you control that overwrites the header.
    """
    if request.user.is_authenticated:
        return f"page-throttle:{scope}:user:{request.user.pk}"
    return f"page-throttle:{scope}:ip:{request.META.get('REMOTE_ADDR', 'unknown')}"
```

and the decorator itself, which is a counter and an expiry:

```python
            # `add` writes only when the key is absent, so the window opens on
            # the first request and closes by expiry — no cleanup, no cron.
            if cache.add(key, 0, timeout=window):
                cache.set(f"{key}:reset", time.time() + window, timeout=window)
            try:
                used = cache.incr(key)
            except ValueError:
                # The key expired between `add` and `incr`. That is the first
                # request of a new window, not an error.
                cache.set(key, 1, timeout=window)
                cache.set(f"{key}:reset", time.time() + window, timeout=window)
                used = 1
```

**WHY `cache.add` and not `cache.set`** — `add` is atomic and only writes when the key is absent.
Read-modify-write with `get` then `set` loses counts under concurrency, which is the one thing a
rate limiter must not do.

**TYPE** — the rate goes with the other security settings, in `config/settings.py`:

```python
# Rate limits for the plain-Django HTML pages. DRF's DEFAULT_THROTTLE_RATES
# cover DRF views only — a function view in blog/views.py is invisible to them,
# so the pages carry their own table, read by blog/throttling.py.
PAGE_THROTTLE_RATES = {
    "blog-detail": "30/min",
}
```

**TYPE** — and the view gets one line, in `blog/views.py`:

```python
@rate_limit(scope="blog-detail", rate="30/min")
def blog_detail(request, pk):
    """One post, rendered — and the busiest read in the app.

    Rate-limited because it is the obvious scraping target: it is public for
    published posts, it takes a row id in the URL, and walking 1..n through it
    is how somebody copies the whole site. The limit is per account when signed
    in and per address when not; see `blog/throttling.py`.
    """
```

with `from .throttling import rate_limit` at the top. A refused request renders
`blog/templates/blog/throttled.html` — an HTML page, because the caller is a browser and a JSON
error body would be shown to a human as raw text.

**TYPE**

```bash
for i in $(seq 31); do
  printf "%s " "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/blogs/posts/1/)"
done; echo
```

**EXPECT** — thirty `200`s and a `429`.

```
200 200 200 ... 200 200 429
```

**TYPE**

```bash
curl -s -i http://127.0.0.1:8000/blogs/posts/1/ | head -8
curl -s -o /dev/null -w "GET /blogs/posts/ -> %{http_code}\n" http://127.0.0.1:8000/blogs/posts/
```

**EXPECT** — the header a well-behaved client reads, and a list page that shares no counter:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: text/html; charset=utf-8
```

```
GET /blogs/posts/ -> 200
```

Sign in and reload: you get `200` again, because an authenticated caller is counted by primary key
rather than by address. Two counters, two scopes, one cache.

**WHY this is a fixed window, and what that costs** — the counter expires as a unit, so a client can
send thirty requests at the end of one minute and thirty more at the start of the next: the
worst-case burst is double the rate. DRF's `SimpleRateThrottle` keeps a list of timestamps instead
and slides the window, at the cost of storing one entry per request. For a page read, the simpler
version is the right trade. For the login endpoint it is not — which is why the login endpoint uses
DRF's throttle and this one does not.

**CHECKPOINT 5b** — the 31st read of a post is a `429` with `Retry-After`, the post *list* still
answers `200`, and signing in resets the count. Anyone who cannot trip it has the browser cache in
the way; use `curl`, not a reload.

> **DOCS** — [`cache.add` and `cache.incr`](https://docs.djangoproject.com/en/5.2/topics/cache/#basic-usage) ·
> [`Retry-After` (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Retry-After) ·
> [DRF `SimpleRateThrottle`](https://www.django-rest-framework.org/api-guide/throttling/#custom-throttles)

**CHECKPOINT 5** — everyone has seen a `429` and can say what `Retry-After` in the response headers
is for.

> **DOCS** — [DRF throttling](https://www.django-rest-framework.org/api-guide/throttling/) ·
> [Django cache framework](https://docs.djangoproject.com/en/5.2/topics/cache/)

\newpage

# Part 6 — What a token actually is

Since Day 3 the API has been handing out JWTs. Today you read one.

## 6.1 Open it without the key

**TYPE**

```bash
python -c "
import base64, json, sys
payload = sys.argv[1].split('.')[1]
print(json.dumps(json.loads(base64.urlsafe_b64decode(payload + '==')), indent=2))
" "$ASHA"
```

**EXPECT**

```json
{
  "token_type": "access",
  "exp": 1788674727,
  "iat": 1788673827,
  "jti": "584b694f6b9d41b6b33fbb8692d39560",
  "user_id": "2",
  "username": "asha"
}
```

No key, no password, no library. A JWT is three base64 chunks: header, payload, signature.

**WHY this is the most misunderstood thing in API auth** — a JWT is **signed, not encrypted**. The
signature stops anyone *changing* the payload; it does nothing to stop them *reading* it. Anything
you put in a claim is public to whoever holds the token, which for a browser app is the user, their
browser extensions, and anything that can read local storage.

So: `username`, `user_id`, a role name — fine. An email address, a phone number, an internal
customer id, a feature flag you do not want copied — not fine.

That is why the custom claim in `accounts/serializers.py` carries this comment:

```python
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # A JWT payload is signed, not encrypted: anyone holding the token can
        # base64-decode this and read it. Claims are for identification, never
        # for secrets — no email, no role you would not print on a badge.
        token['username'] = user.username
        return token
```

## 6.2 Change one character

**TYPE**

```bash
FORGED="${ASHA%??}XX"
curl -s http://127.0.0.1:8000/accounts/user/info -H "Authorization: Bearer $FORGED" \
  -w "\nstatus=%{http_code}\n"
```

**EXPECT**

```json
{"detail":"Given token not valid for any token type","code":"token_not_valid",
 "messages":[{"token_class":"AccessToken","token_type":"access","message":"Token is invalid"}]}
status=401
```

The signature is `HMAC-SHA256(header.payload, SECRET_KEY)`. Editing any byte of the payload breaks
it, and forging a new signature needs the key. **This is what `SECRET_KEY` protects.** A leaked key
is not "please rotate at your convenience"; it is "anyone can mint a token for any user id".

## 6.3 Lifetimes, rotation, blacklist

**TYPE** — add to `config/settings.py`:

```python
SIMPLE_JWT = {
    # Short-lived, because an access token cannot be revoked: until it expires,
    # whoever holds it is you.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    # Every refresh issues a new refresh token and blacklists the old one, so a
    # stolen refresh token is usable at most once before it starts failing.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Tokens are signed with SECRET_KEY. Rotate the key and every token dies.
    "SIGNING_KEY": SECRET_KEY,
}
```

with `from datetime import timedelta` at the top of the file.

**TYPE** — log in again to pick up a fresh pair, then refresh:

```bash
REFRESH=$(curl -s -X POST http://127.0.0.1:8000/accounts/login/ -H "Content-Type: application/json" \
  -d '{"username":"asha","password":"lab-passphrase-2026"}' | python -c "import json,sys; print(json.load(sys.stdin)['refresh'])")

curl -s -X POST http://127.0.0.1:8000/accounts/refresh -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}" -o /tmp/rot.json -w "status=%{http_code}\n"
python -c "import json; d=json.load(open('/tmp/rot.json')); print(sorted(d))"
NEW_REFRESH=$(python -c "import json; print(json.load(open('/tmp/rot.json'))['refresh'])")
```

**EXPECT**

```
status=200
['access', 'refresh']
```

A *new* refresh token came back. Use the old one again:

**TYPE**

```bash
curl -s -X POST http://127.0.0.1:8000/accounts/refresh -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}" -w "\nstatus=%{http_code}\n"
```

**EXPECT**

```json
{"detail":"Token is blacklisted","code":"token_not_valid"}
status=401
```

**WHY rotation is worth the extra row in the database** — a refresh token lives for a day. If one
leaks, rotation means the thief and the real user cannot both keep using it: the second one to
present it gets `Token is blacklisted`, and somebody notices. Without rotation, a leaked refresh
token is a silent day-long session.

## 6.4 The honest limit of "log out"

`LogoutView` blacklists the refresh token. Test what that does and does not achieve:

**TYPE**

```bash
curl -s -X POST http://127.0.0.1:8000/accounts/logout/ -H "Authorization: Bearer $ASHA" \
  -H "Content-Type: application/json" -d "{\"refresh\":\"$NEW_REFRESH\"}" \
  -o /dev/null -w "logout            -> %{http_code}\n"
curl -s -o /dev/null -w "user/info after   -> %{http_code}\n" \
  http://127.0.0.1:8000/accounts/user/info -H "Authorization: Bearer $ASHA"
```

**EXPECT**

```
logout            -> 205
user/info after   -> 200
```

The access token still works. It will keep working until `exp`, and there is no list to add it to —
that is what "stateless" means. Logging out of a JWT API means:

1. the client deletes both tokens, and
2. the refresh token is blacklisted so no new access token can be minted, and
3. the existing access token dies of old age.

Step 3 is why `ACCESS_TOKEN_LIFETIME` is fifteen minutes and not fifteen hours. If your product
needs instant revocation, you need server-side sessions or a token-introspection call on every
request — and at that point you have rebuilt sessions with extra steps. That is a real, reasonable
choice; make it knowingly.

**CHECKPOINT 6** — everyone can state, without looking: what a JWT hides (nothing), what the
signature prevents (tampering), and what logout does not do (revoke the access token).

> **DOCS** — [Simple JWT settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html) ·
> [Token blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html) ·
> [RFC 7519 §11 — JWT security considerations](https://www.rfc-editor.org/rfc/rfc7519#section-11)

\newpage

# Part 7 — The registration endpoint

`RegisterView` is the only endpoint in the project that an anonymous stranger may write to. It
therefore gets read twice.

**TYPE**

```bash
curl -s -X POST http://127.0.0.1:8000/accounts/register/ -H "Content-Type: application/json" \
  -d '{"username":"mallory","email":"m@example.com","password":"lab-passphrase-2026",
       "is_staff":true,"is_superuser":true}' | python -m json.tool
```

**EXPECT**

```json
{
    "id": 4,
    "username": "mallory",
    "email": "m@example.com"
}
```

**TYPE**

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='mallory')
print('is_staff =', u.is_staff, '| is_superuser =', u.is_superuser)
print('password field =', u.password[:38] + '...')
"
```

**EXPECT**

```
is_staff = False | is_superuser = False
password field = pbkdf2_sha256$1000000$mMFXR8QSET9Ccbxp...
```

Two attacks failed here and neither of them printed an error.

* **Privilege escalation by extra field.** `User` has fifteen columns; `Meta.fields` names four.
  A key that is not in the allowlist is not rejected, it is *ignored* — which is why the response
  is a cheerful `201`. Had the serializer said `fields = "__all__"`, mallory would now be staff.
* **Plaintext passwords.** `ModelSerializer.create()` calls `User.objects.create()`, which writes
  whatever string it is given straight into the column. The three-line `create()` override calls
  `create_user()` instead, which hashes. `pbkdf2_sha256$1000000$...` is the proof.

**TYPE** — and the third defence:

```bash
curl -s -X POST http://127.0.0.1:8000/accounts/register/ -H "Content-Type: application/json" \
  -d '{"username":"weak","password":"123456"}' | python -m json.tool
```

**EXPECT**

```json
{
    "password": [
        "This password is too short. It must contain at least 8 characters.",
        "This password is too common.",
        "This password is entirely numeric."
    ]
}
```

That is `AUTH_PASSWORD_VALIDATORS` — the block `startproject` writes into every settings file and
that people delete because it is noisy in tests. It is running because the serializer opts in:

```python
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
```

`write_only=True` is the fourth defence: it is why no response in this project has ever contained a
password field.

**CHECKPOINT 7** — the room can name the four separate things in `RegisterSerializer` that each
stop a different attack, without reading them off the screen.

> **DOCS** — [Password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/) ·
> [`validate_password`](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/#module-django.contrib.auth.password_validation) ·
> [Serializer field-level options](https://www.django-rest-framework.org/api-guide/fields/#core-arguments)

\newpage

# Part 8 — The pages are a separate application

Everything so far protects `/api/`. Repeat 1.4 and watch it still work:

**TYPE**

```bash
curl -s http://127.0.0.1:8000/blogs/posts/new/ -o /dev/null -w "GET /blogs/posts/new/ -> %{http_code}\n"
```

**EXPECT**

```
GET /blogs/posts/new/ -> 200
```

**WHY** — `permission_classes` is a DRF attribute, read by DRF's `APIView.initial()`. `blog/views.py`
holds plain Django function views. They never touch DRF, so nothing in Parts 2–5 applies to them.
Two clients, two doors, two locks — and the second one is still open.

## 8.1 Require a login

**TYPE** — `blog/views.py`, imports:

```python
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
```

**TYPE** — the same visibility rule the API got, written for the HTML side:

```python
def visible_blogs(user):
    """The posts `user` is allowed to see: everything published, plus their own drafts.

    The API enforces the same rule in `BlogViewSet.get_queryset()`. Two clients,
    one rule — but it has to be written twice, because a permission class
    protects a DRF view and nothing else. `@login_required` and
    `permission_classes` do not know about each other.
    """
    posts = Blog.objects.select_related("author", "owner")
    if not user.is_authenticated:
        # `Q(owner=AnonymousUser())` is a TypeError, not an empty result — an
        # anonymous branch is required, not optional.
        return posts.filter(published=True)
    return posts.filter(Q(published=True) | Q(owner=user))


def owned_blog_or_403(request, pk):
    """Fetch a post for editing, or refuse with 403.

    A deliberate difference from the API. `BlogViewSet` scopes its queryset, so
    a post you may not touch comes back as a 404 and leaks nothing. Here the
    answer is an explicit 403, because the caller is a person who followed a
    link and "you cannot edit this" is more useful to them than "no such page".

    Both are defensible. What is not defensible is picking neither — which is
    what this view did until today.
    """
    blog = get_object_or_404(Blog, pk=pk)
    if blog.owner_id is None or blog.owner_id != request.user.id:
        raise PermissionDenied("You can only change posts you created.")
    return blog
```

**TYPE** — then five small edits to the views themselves:

```python
def blog_list(request):
    blogs = visible_blogs(request.user)
    return render(request, "blog/blog_list.html", {"blogs": blogs})
```

```python
    # Somebody else's draft is a 404 here, exactly as it is over the API.
    blog = get_object_or_404(visible_blogs(request.user), pk=pk)
    return render(request, "blog/blog_detail.html", {"blog": blog})


@login_required
def blog_create(request):
```

(`blog_detail` keeps the `@rate_limit` decorator and docstring it got in 5.4 — only its first line
changes.)

Inside `blog_create`, the save changes:

```python
        form = BlogForm(request.POST)
        if form.is_valid():
            # `commit=False` builds the object without writing it, so the
            # server can add the fields the form is not allowed to carry.
            blog = form.save(commit=False)
            blog.owner = request.user
            blog.save()
```

And both write views gain a decorator and lose their bare `get_object_or_404`:

```python
@login_required
def blog_update(request, pk):
    blog = owned_blog_or_403(request, pk)
```

```python
@login_required
def blog_delete(request, pk):
    blog = owned_blog_or_403(request, pk)
```

**WHY `form.save(commit=False)`** — `BlogForm.Meta.fields` is an allowlist for exactly the reason
`Meta.fields` was one on the serializer, so `owner` cannot come from the POST body. `commit=False`
is how the server adds it afterwards. It is the HTML twin of `perform_create`.

## 8.2 Point `LOGIN_URL` somewhere that exists

`@login_required` redirects to `settings.LOGIN_URL`, which defaults to `/accounts/login/`. In this
project that URL is the **JSON login endpoint** — a browser sent there gets a DRF error page, not a
form.

**TYPE** — `config/settings.py`:

```python
# Where @login_required sends an anonymous visitor. The default is
# /accounts/login/, which in this project is the JSON login endpoint — a page
# no browser can render a form for.
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/blogs/posts/"
```

Borrowing the admin's login page is a lab shortcut. A real site wires up
`django.contrib.auth.urls` and writes its own `registration/login.html` — see Appendix E.

## 8.3 Stop offering buttons that will refuse

**TYPE** — `blog/templates/blog/base.html`, in the nav:

```html
      {% if user.is_authenticated %}
        <li><a href="{% url 'blog:post-create' %}">New post</a></li>
        <li class="nav-user">Signed in as {{ user.username }} &middot; <a href="{% url 'admin:index' %}">admin</a></li>
      {% else %}
        <li class="nav-user"><a href="{% url 'admin:login' %}?next={{ request.path }}">Log in</a></li>
      {% endif %}
```

**TYPE** — `blog/templates/blog/blog_list.html`, the actions cell:

```html
              <td class="actions">
                {% comment %}
                  Hiding a link is not a permission check — the view still has
                  to refuse. This is here so the page does not offer people
                  buttons that will 403 on them.

                  Written as `blog.owner == user` on purpose. The tempting
                  `blog.owner_id == user.id` is a hole: for an anonymous
                  visitor looking at an unowned post it compares None to None
                  and says yes.
                {% endcomment %}
                {% if user.is_authenticated and blog.owner == user %}
                  <a href="{% url 'blog:post-update' blog.pk %}">Edit</a>
                  <a href="{% url 'blog:post-delete' blog.pk %}" class="danger">Delete</a>
                {% else %}
                  <span class="muted">&mdash;</span>
                {% endif %}
              </td>
```

and the same `{% if %}` around the two buttons in `blog_detail.html`. Two classes join the
stylesheet, `.nav-user` and `.muted` — `blog/test_styles.py` fails if a template emits a class the
CSS never defines, so add them before running the tests.

**WHY the template check is not the security control** — it is a courtesy. The view refuses
regardless. Say this out loud to the room, because "I hid the button" is a genuinely common answer
to "how did you secure it".

## 8.4 Watch twenty-six tests turn red

**TYPE**

```bash
python manage.py test
```

**EXPECT** — a wall of failures.

```
FAILED (failures=21, errors=5)
```

Read three of them before fixing anything. They all say some version of `302 != 200`: the Day 9
tests do `self.client.get(reverse("blog:post-create"))` with no login, and until an hour ago that
worked.

**That number is the finding.** Twenty-six assertions in yesterday's suite only passed because the
pages were open. A test suite cannot tell you about a control you never wrote.

**TYPE** — the fix is a login and an owner. In `blog/test_forms.py`:

```python
    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen")
        cls.herbert = Author.objects.create(name="Frank Herbert")
        cls.user = User.objects.create_user("asha", password="lab-passphrase-2026")

    def setUp(self):
        self.client.force_login(self.user)
```

and every `Blog.objects.create(...)` in that file gains `owner=self.user`. Do the same in
`blog/test_styles.py`. In `blog/test_api.py` one test posts to an HTML page, and needs *both*
logins:

```python
        self.client.force_authenticate(user=self.user)
        self.client.force_login(self.user)
```

**WHY both** — `force_authenticate` fakes a DRF credential and the HTML views know nothing about it.
`force_login` writes a session cookie, which is what `@login_required` reads. Same test client, two
unrelated mechanisms.

**TYPE** — while you are in `blog/test_api.py`, add a base class:

```python
class ThrottleFreeAPITestCase(APITestCase):
    """Throttle counters live in the cache, and the cache outlives a test.

    `TestCase` rolls the database back between tests; it does not roll back
    Redis, Memcached or local memory. Without this, tests start failing with
    429s in whatever order happens to be unlucky.
    """

    def setUp(self):
        super().setUp()
        cache.clear()
```

and inherit the three API test classes from it instead of `APITestCase`.

**CHECKPOINT 8** — `python manage.py test` is green again, and an anonymous
`GET /blogs/posts/new/` returns `302` to `/admin/login/?next=/blogs/posts/new/`.

> **DOCS** — [`login_required`](https://docs.djangoproject.com/en/5.2/topics/auth/default/#the-login-required-decorator) ·
> [`PermissionDenied`](https://docs.djangoproject.com/en/5.2/ref/exceptions/#permissiondenied) ·
> [`ModelForm.save(commit=False)`](https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/#the-save-method) ·
> [CSRF protection](https://docs.djangoproject.com/en/5.2/ref/csrf/)

\newpage

# Part 9 — Settings, secrets and the deploy checklist

Six warnings from 1.7, plus a secret key that is in git forever.

## 9.1 Read the environment

**TYPE** — replace the top of `config/settings.py`:

```python
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
```

```python
def env_flag(name, default="0"):
    """Read a boolean from the environment. Anything unlisted is False."""
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


# Settings that differ between a laptop and a server are read from the
# environment. Nothing secret is written in this file, because this file is in
# git and git remembers forever.
DEBUG = env_flag("DJANGO_DEBUG", "1")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        # Fail loudly. A missing key that silently falls back to a known value
        # is worse than a crash: every signature the site makes is forgeable.
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be set when DEBUG is off. "
            "Generate one with: python -c "
            "'from django.core.management.utils import get_random_secret_key as k; print(k())'"
        )
    SECRET_KEY = "django-insecure-dev-only-never-deploy-this-key"

# `ALLOWED_HOSTS` is the Host-header allowlist. Empty + DEBUG=True quietly means
# localhost only; empty + DEBUG=False rejects every request.
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
```

**WHY it raises instead of generating a key** — a random key generated at startup logs everyone out
on every restart and breaks every signed value the site has ever produced. A default key shared by
every deployment is worse: it is a published key. Crashing is the only honest option.

**WHY `env_flag` and not `bool(os.environ.get(...))`** — `bool("0")` is `True`. Every string except
the empty one is truthy, so the naive version turns `DJANGO_DEBUG=0` into debug mode in production.
This exact bug ships regularly.

## 9.2 Headers and cookies

**TYPE** — append to `config/settings.py`:

```python
# Never render this site inside someone else's <iframe> (clickjacking).
X_FRAME_OPTIONS = "DENY"
# Do not let a browser second-guess a Content-Type it was given.
SECURE_CONTENT_TYPE_NOSNIFF = True
# Do not leak the full URL of this site in the Referer header of outbound links.
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    # Everything below is a no-op on http://127.0.0.1, and mandatory in front
    # of a real domain.
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # one year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Behind a TLS-terminating proxy, this is how Django learns the original
    # request was HTTPS. Only set it if the proxy strips a client-sent header.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

**WHY the `if not DEBUG:` wrapper** — `SECURE_SSL_REDIRECT = True` on a laptop turns every
`http://127.0.0.1:8000/` request into a `301` to `https://127.0.0.1:8000/`, which nothing is
listening on. The block is not "the production settings"; it is "the settings that require a real
certificate to be present".

**WHY `SECURE_PROXY_SSL_HEADER` is dangerous if you cheat** — Django believes that header. If your
proxy does not overwrite `X-Forwarded-Proto` on the way in, any client can send
`X-Forwarded-Proto: https` and Django will treat a plaintext request as secure. Set it only when you
know the proxy strips it.

## 9.3 The `.env` file

**TYPE** — a new file, `.env.example`, tracked in git:

```bash
# Copy to `.env` and fill in. `.env` itself is gitignored and must stay that way.
#
#   set -a; source .env; set +a       # bash / zsh: export everything in here
#
# Nothing in this file is a real secret — it is the *list* of secrets, which is
# the part that belongs in git.

DJANGO_DEBUG=1
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

**TYPE** — confirm the real one can never be committed:

```bash
grep -n "^\.env$" .gitignore
```

**EXPECT** — a line number. It has been there since Day 1; today it finally matters.

## 9.4 Run the checklist properly

**TYPE**

```bash
DJANGO_DEBUG=0 \
DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key as k; print(k())')" \
DJANGO_ALLOWED_HOSTS=example.com \
python manage.py check --deploy
```

**EXPECT**

```
System check identified no issues (0 silenced).
```

Six warnings to none, and the difference between the two runs is entirely in the environment.

**TYPE** — see what the same server looks like with `DEBUG=0`. In a second terminal:

```bash
DJANGO_DEBUG=0 \
DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key as k; print(k())')" \
DJANGO_ALLOWED_HOSTS=127.0.0.1 \
python manage.py runserver 8001 --insecure
```

```bash
curl -s -o /dev/null -w "Host: evil.example.com -> %{http_code}\n" -H "Host: evil.example.com" \
  http://127.0.0.1:8001/blogs/posts/
curl -s -I http://127.0.0.1:8001/blogs/posts/ -H "X-Forwarded-Proto: https" | head -10
```

**EXPECT**

```
Host: evil.example.com -> 400
```

```
HTTP/1.1 200 OK
...
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin
Cross-Origin-Opener-Policy: same-origin
```

Without the `X-Forwarded-Proto` header that request is a `301` to `https://` — that is
`SECURE_SSL_REDIRECT` doing its job. And <http://127.0.0.1:8001/nope> is now a plain
"Not Found" with no URLconf on it.

**WHY `--insecure`** — with `DEBUG=0` the dev server stops serving `/static/` for you. The flag
turns it back on for this demo. On a real server, `collectstatic` and a web server do that job.

**CHECKPOINT 9** — `check --deploy` is clean with the production environment, and everyone can
explain why the same command still reports six warnings without it.

> **DOCS** — [Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) ·
> [`SECRET_KEY`](https://docs.djangoproject.com/en/5.2/ref/settings/#secret-key) ·
> [`ALLOWED_HOSTS`](https://docs.djangoproject.com/en/5.2/ref/settings/#allowed-hosts) ·
> [Security middleware](https://docs.djangoproject.com/en/5.2/ref/middleware/#module-django.middleware.security) ·
> [Clickjacking protection](https://docs.djangoproject.com/en/5.2/ref/clickjacking/)

\newpage

# Part 10 — Write the refusals down

Every rule from Parts 2–9 is a thing the app must refuse to do. A refusal nobody tests is a comment.

**TYPE** — two new files. `blog/test_security.py`:

```python
class OwnershipAPITests(APITestCase):
    """Authentication says who you are. It never says what you may touch."""

    def test_a_stranger_cannot_edit_your_post(self):
        """The bug this file exists for: authenticated is not authorised."""
        self.client.force_authenticate(user=self.bello)
        url = reverse("api:blog-detail", args=[self.asha_post.pk])

        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.patch(url, {"title": "Defaced"}).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)

        self.asha_post.refresh_from_db()
        self.assertEqual(self.asha_post.title, "Asha public post")

    def test_the_owner_comes_from_the_credential_not_the_body(self):
        """Mass assignment: an extra key in the JSON must not become a fact."""
        self.client.force_authenticate(user=self.bello)
        response = self.client.post(reverse("api:blog-list"), {
            "title": "Posted by bello",
            "content": "x",
            "author": self.austen.pk,
            "owner": self.asha.pk,      # <- ignored
            "created_at": "2000-01-01T00:00:00Z",  # <- also ignored
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created = Blog.objects.get(title="Posted by bello")
        self.assertEqual(created.owner, self.bello)
        self.assertEqual(response.data["owner"], "bello")
        self.assertNotEqual(created.created_at.year, 2000)
```

The full file is on the reference branch (Appendix D) and covers thirty-three refusals across seven
classes:

| Class | Asserts |
| --- | --- |
| `OwnershipAPITests` | 401 for anonymous, 403 for a stranger, 404 for a stranger's draft, owner stamped from the token, list paginated, unowned rows read-only |
| `ThrottleTests` | the sixth login is a 429, a correct password does not bypass it, register is throttled too |
| `PageRateLimitTests` | the HTML detail page refuses past its rate, sends `Retry-After`, counts per caller not globally, and reads its limit from settings |
| `RateParsingTests` | every period spelling DRF accepts (`/s`, `/min`, `/hour`, `/day`) parses the same way here |
| `HTMLPageSecurityTests` | anonymous is redirected off every write page *and cannot POST*, a logged-in stranger gets 403, drafts are invisible, the page offers no button it would refuse |
| `SettingsTests` | the API is closed by default, tokens rotate and blacklist, access tokens are short-lived, the secret is not in the settings file |
| `DeploymentChecklistTests` | `check --deploy --fail-level WARNING` exits 0 with a production environment, and the app refuses to start without a key |

**TYPE** — and `accounts/tests.py`, which was still the `startapp` stub:

```python
    def test_an_extra_key_cannot_make_you_staff(self):
        """Privilege escalation by extra field. `Meta.fields` is the defence."""
        response = self.client.post(reverse(self.url_name), {
            "username": "asha", "password": "lab-passphrase-2026",
            "is_staff": True, "is_superuser": True,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="asha")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_a_jwt_payload_is_readable_by_anyone_holding_it(self):
        """Signed is not encrypted. Never put a secret in a claim."""
        access = self.login()["access"]
        header, payload, signature = access.split(".")
        decoded = json.loads(base64.urlsafe_b64decode(payload + "=="))

        self.assertEqual(decoded["username"], "asha")
        # Simple JWT 5.5 writes the user id as a string, not a number.
        self.assertEqual(decoded["user_id"], str(self.user.pk))
        self.assertEqual(decoded["token_type"], "access")
        # No credential is in there — and none ever should be.
        self.assertNotIn("password", decoded)
```

**TYPE**

```bash
python manage.py test
```

**EXPECT**

```
Ran 85 tests in 5.717s

OK
```

Three traps this file hit while it was being written, all of which will bite you too:

1. **`assertNotContains(response, "Asha's draft")` passes even when the draft is on the page** —
   the apostrophe renders as `&#x27;`. A test that asserts an *absence* against escaped text always
   passes. Keep test fixtures free of characters HTML escapes, or pass `html=True`.
2. **Throttle state survives a test.** `TestCase` rolls back the database, not the cache. Without
   `cache.clear()` in `setUp`, a `429` appears in whichever test happens to run sixth — and once the
   detail page is rate-limited, that applies to the Day-9 HTML suites too, not just the API ones.
   Rather than send 31 requests, `PageRateLimitTests` uses
   `@override_settings(PAGE_THROTTLE_RATES={"blog-detail": "3/min"})`, which also proves the limit
   comes from settings rather than from the decorator's default.
3. **`check --deploy` cannot be tested in-process.** The `if not DEBUG:` block runs once, at import,
   so `override_settings(DEBUG=False)` changes nothing. `DeploymentChecklistTests` shells out to a
   subprocess with a production environment, which is the only way to test the real thing.

**CHECKPOINT 10** — 85 tests, green (39 from Day 9, 33 in `blog/test_security.py`, 13 in
`accounts/tests.py`), and the room can point at the one test that would have caught each of the six
holes from Part 1.

> **DOCS** — [Testing in Django](https://docs.djangoproject.com/en/5.2/topics/testing/) ·
> [DRF testing](https://www.django-rest-framework.org/api-guide/testing/) ·
> [`force_login`](https://docs.djangoproject.com/en/5.2/topics/testing/tools/#django.test.Client.force_login)

\newpage

# Part 11 — Commit and push

**TYPE**

```bash
python manage.py check
python manage.py check --deploy   # six warnings on a dev environment is correct
python manage.py test
git status
```

**EXPECT** — `git status` lists the files you touched and **not** `.env`, `db.sqlite3` or `venv/`.

**TYPE**

```bash
git add -A
git commit -m "day 10: API security — ownership, throttling, token hygiene, deploy settings"
git push -u origin <first_name>/day10
```

Open the pull request against `main` and put the Part 1 scoreboard in the description: what the app
let you do before, and the commit that stopped each one.

## 11.1 Prove it worked

**TYPE** — the four-line version of today, for the PR description:

```bash
curl -s -o /dev/null -w "anon  GET  /api/blogs/        -> %{http_code}\n" http://127.0.0.1:8000/api/blogs/
curl -s -o /dev/null -w "anon  GET  /blogs/posts/new/  -> %{http_code}\n" http://127.0.0.1:8000/blogs/posts/new/
curl -s -o /dev/null -w "bello PATCH /api/blogs/2/     -> %{http_code}\n" -X PATCH \
  -H "Authorization: Bearer $BELLO" -H "Content-Type: application/json" \
  -d '{"title":"x"}' http://127.0.0.1:8000/api/blogs/2/
curl -s -o /dev/null -w "bello GET  /api/blogs/3/      -> %{http_code}\n" \
  -H "Authorization: Bearer $BELLO" http://127.0.0.1:8000/api/blogs/3/
```

**EXPECT**

```
anon  GET  /api/blogs/        -> 401
anon  GET  /blogs/posts/new/  -> 302
bello PATCH /api/blogs/2/     -> 403
bello GET  /api/blogs/3/      -> 404
```

Four numbers, four different refusals: *I don't know you*, *log in first*, *not yours*, *no such
thing*. On Day 9 all four were `200`.

**CHECKPOINT 11** — the branch is pushed, the PR is open, CI (if you have it) is green.

\newpage

# Appendix A — Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `403` on every write with a valid token, before you changed anything | Day 8's `DjangoModelPermissionsOrAnonReadOnly` is still in `REST_FRAMEWORK` | Part 2 replaces it |
| `AttributeError: 'BlogViewSet' object has no attribute 'queryset'` | `DjangoModelPermissions` needs `.queryset`, and Part 4 removed it | You are still on the old default — finish Part 2 |
| `TypeError: Field 'id' expected a number but got <SimpleLazyObject: AnonymousUser>` | `Q(owner=request.user)` with an anonymous caller | The `if not user.is_authenticated` branch in `visible_blogs` |
| Every request returns `429` and will not stop | Local-memory throttle cache | Restart the server, or wait out the window |
| A page you refreshed a few times is a `429` | `blog-detail` allows 30/min per caller | Expected. Raise `PAGE_THROTTLE_RATES` or sign in — a signed-in caller gets its own counter |
| Sixty reads got through in one minute | Fixed window: 30 at the end of one window, 30 at the start of the next | Known and documented in 5.4. Use DRF's sliding window if the burst matters |
| Tests fail with `429` in random places | Cache is not rolled back between tests | `cache.clear()` in `setUp` |
| `@login_required` redirects to a DRF error page | `LOGIN_URL` still defaults to `/accounts/login/`, which is the JSON endpoint | Part 8.2 |
| `ImproperlyConfigured: DJANGO_SECRET_KEY must be set` | `DJANGO_DEBUG=0` with no key | Export a key, or unset `DJANGO_DEBUG` |
| Everything is a `301` to `https://` on localhost | `DEBUG=0`, so `SECURE_SSL_REDIRECT` is on | Expected. Use `-H "X-Forwarded-Proto: https"` or go back to `DEBUG=1` |
| `400 Bad Request` with `DEBUG=0` | `Host` header not in `ALLOWED_HOSTS` | Add the host to `DJANGO_ALLOWED_HOSTS` |
| `assertNotContains` passes but the string is on the page | HTML escaping — `'` renders as `&#x27;` | Use fixtures without escapable characters |
| `manage.py test` cannot find `blog.test_security` | File is next to `tests.py`, both are importable, no `__init__` needed | Check the filename starts with `test` |
| CSS class assertions fail after Part 8.3 | `.nav-user` / `.muted` used in a template but not defined in `style.css` | Add them; that test exists to catch this |
| Windows: `$BELLO` is empty | PowerShell does not expand `$(...)` the same way | Use the block below |

**PowerShell equivalents**

```powershell
$body = '{"username":"bello","password":"lab-passphrase-2026"}'
$r = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/accounts/login/ `
     -ContentType "application/json" -Body $body
$BELLO = $r.access

Invoke-WebRequest -Method Patch -Uri http://127.0.0.1:8000/api/blogs/2/ `
  -Headers @{ Authorization = "Bearer $BELLO" } `
  -ContentType "application/json" -Body '{"title":"Defaced"}'
```

`Invoke-WebRequest` throws on a 4xx, so wrap it in `try { } catch { $_.Exception.Response.StatusCode }`
to see the status codes this guide asks you to read.

**The public-router footnote.** `DefaultRouter` generates an `APIRootView` that inherits
`DEFAULT_PERMISSION_CLASSES`, so anonymous `GET /api/` is now a `401`. If you want the index public
while everything under it stays closed:

```python
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter


class PublicRootRouter(DefaultRouter):
    def get_api_root_view(self, api_urls=None):
        view = super().get_api_root_view(api_urls=api_urls)
        view.cls.permission_classes = [AllowAny]
        return view
```

\newpage

# Appendix B — Official documentation index

**Django 5.2 — security**

* [Security overview](https://docs.djangoproject.com/en/5.2/topics/security/)
* [Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
* [`SECRET_KEY`](https://docs.djangoproject.com/en/5.2/ref/settings/#secret-key) ·
  [`ALLOWED_HOSTS`](https://docs.djangoproject.com/en/5.2/ref/settings/#allowed-hosts) ·
  [`DEBUG`](https://docs.djangoproject.com/en/5.2/ref/settings/#debug)
* [Security middleware](https://docs.djangoproject.com/en/5.2/ref/middleware/#module-django.middleware.security)
* [Clickjacking protection](https://docs.djangoproject.com/en/5.2/ref/clickjacking/) ·
  [CSRF protection](https://docs.djangoproject.com/en/5.2/ref/csrf/)
* [HTTPS settings](https://docs.djangoproject.com/en/5.2/topics/security/#ssl-https)

**Django 5.2 — auth**

* [Using the auth system](https://docs.djangoproject.com/en/5.2/topics/auth/default/) ·
  [`login_required`](https://docs.djangoproject.com/en/5.2/topics/auth/default/#the-login-required-decorator)
* [Password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/)
* [Customising authentication](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/) ·
  [`AUTH_USER_MODEL`](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model)
* [`PermissionDenied`](https://docs.djangoproject.com/en/5.2/ref/exceptions/#permissiondenied)
* [`Q` objects](https://docs.djangoproject.com/en/5.2/topics/db/queries/#complex-lookups-with-q-objects)
* [Cache framework](https://docs.djangoproject.com/en/5.2/topics/cache/)

**Django REST Framework 3.18**

* [Permissions](https://www.django-rest-framework.org/api-guide/permissions/) ·
  [object-level](https://www.django-rest-framework.org/api-guide/permissions/#object-level-permissions) ·
  [custom](https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions)
* [Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
* [Throttling](https://www.django-rest-framework.org/api-guide/throttling/)
* [Pagination](https://www.django-rest-framework.org/api-guide/pagination/)
* [Filtering against the current user](https://www.django-rest-framework.org/api-guide/filtering/#filtering-against-the-current-user)
* [Serializer `read_only_fields`](https://www.django-rest-framework.org/api-guide/serializers/#specifying-read-only-fields)
* [Testing](https://www.django-rest-framework.org/api-guide/testing/)

**Simple JWT 5.5**

* [Settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html)
* [Blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html)
* [Customising token claims](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/customizing_token_claims.html)

**Standards and background**

* [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)
* [OWASP Cheat Sheet — REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
* [RFC 7519 — JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519) (§11 is the security section)
* [Django security releases](https://docs.djangoproject.com/en/5.2/releases/security/) — subscribe

\newpage

# Appendix C — Command cheat sheet

```bash
# the checks
python manage.py check                 # does it import and configure
python manage.py check --deploy        # is it fit to serve
python manage.py test                  # do the refusals still refuse
python manage.py test blog.test_security accounts.tests

# the deploy environment, one line at a time
export DJANGO_DEBUG=0
export DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key as k; print(k())')"
export DJANGO_ALLOWED_HOSTS=example.com
python manage.py check --deploy
unset DJANGO_DEBUG DJANGO_SECRET_KEY DJANGO_ALLOWED_HOSTS

# the migration
python manage.py makemigrations blog
python manage.py sqlmigrate blog 0004      # read the SQL before running it
python manage.py migrate

# tokens
LOGIN=http://127.0.0.1:8000/accounts/login/
TOK=$(curl -s -X POST $LOGIN -H "Content-Type: application/json" \
      -d '{"username":"asha","password":"lab-passphrase-2026"}' \
      | python -c "import json,sys; print(json.load(sys.stdin)['access'])")

# read a token payload without the key
python -c "
import base64, json, sys
print(json.dumps(json.loads(base64.urlsafe_b64decode(sys.argv[1].split('.')[1] + '==')), indent=2))
" "$TOK"

# the four refusals
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/blogs/                      # 401
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/blogs/posts/new/                # 302
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH -H "Authorization: Bearer $TOK" \
     -H "Content-Type: application/json" -d '{"title":"x"}' \
     http://127.0.0.1:8000/api/blogs/1/                                                        # 403
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $TOK" \
     http://127.0.0.1:8000/api/blogs/999/                                                      # 404

# trip the login throttle (DRF, 5/min)
for i in $(seq 6); do curl -s -o /dev/null -w "%{http_code} " -X POST $LOGIN \
  -H "Content-Type: application/json" -d '{"username":"asha","password":"guess"}'; done; echo

# trip the page throttle (ours, 30/min)
for i in $(seq 31); do curl -s -o /dev/null -w "%{http_code} " \
  http://127.0.0.1:8000/blogs/posts/1/; done; echo

# secrets hygiene
grep -rn "SECRET_KEY" config/settings.py
git log -p --all -- config/settings.py | grep -c "django-insecure"
```

\newpage

# Appendix D — Trainer notes

## D.1 The live-demo order that lands best

1. **Do Part 1 as theatre, before any theory.** Two terminals, two users, one `PATCH`. Let the room
   watch bello rewrite asha's post and get a `200`. Do not explain first — ask "what just happened"
   afterwards. The whole day is downhill from that `200`.
2. **Then the two-question table** (Part 2). Draw it on the board and leave it up all day; you will
   point at it six times.
3. **Type `blog/permissions.py` live.** It is twenty lines and it is the intellectual centre of the
   day. Ask the room what `has_object_permission` should return for `owner=None` *before* you write
   the `is not None`.
4. **Do the mass-assignment demo with a straight face** — send `"owner": 3`, get `"owner": "asha"`,
   say nothing, wait. Someone will ask why it was ignored, and that question is the lesson.
5. **Run the throttle loop.** Six lines of shell, one `429`. Then run the *correct* password and get
   a `429` too, and ask whether that is a bug. Follow it straight into 5.4: ask the room whether
   that same protection covers `/blogs/posts/1/`, let someone say yes, then run the 31-request loop
   on the unfixed page.
6. **Decode a JWT on the projector.** This is the moment people who have shipped JWTs go quiet. Have
   a token from a real service of your own ready if you are comfortable — the payload of a token
   from a well-known app makes the point faster than ours does.
7. **Part 8's twenty-six failures.** Run `manage.py test` immediately after adding `@login_required`
   and let the wall of red sit on screen for a while before saying anything.
8. **Finish on `check --deploy`.** Six warnings, then the environment, then zero. It is the tidiest
   ending the day has.

## D.2 Things that reliably confuse the room

| Confusion | What to say |
| --- | --- |
| "Isn't `IsAuthenticated` enough?" | It answers *who*, never *which row*. Show 1.3 again. |
| 401 vs 403 | "I don't know you" vs "I know you and no". Then note DRF returns 403 for a missing credential when no authenticator offers a `WWW-Authenticate` header. |
| Why the draft is 404 and the published post is 403 | Because 403 admits the row exists. Existence is information when the row is private. |
| `author` vs `owner` | Attribution vs authority. Three posts can share an author; only one account may edit a row. |
| "CSRF protects the form, so it's secure" | CSRF stops *another site* posting the form. It says nothing about who may post it. Demo 1.4. |
| "We hid the Edit button" | Show `curl` hitting the URL directly. Hiding is courtesy; the view is the control. |
| JWT "encryption" | Base64-decode one live. Signed ≠ encrypted. |
| Why logout leaves the access token alive | There is no list to add it to. That is what stateless means, and why the lifetime is 15 minutes. |
| Throttle rates in tests | The cache is not a database and `TestCase` does not roll it back. |
| `bool("0")` | Write it in the shell: `python -c 'print(bool("0"))'` → `True`. |

## D.3 Time budget

| Part | Minutes | Notes |
| --- | --- | --- |
| Start here + seed | 10 | Have the seed snippet in the chat window before you begin |
| 1 — Attack it | 30 | Do not rush this; it pays for the rest of the day |
| 2 — Two questions | 15 | Mostly talking |
| 3 — Ownership | 40 | Model, migration, permission class, serializer, `perform_create` |
| 4 — Queryset scoping | 20 | Include the 403-vs-404 discussion |
| — break — | 10 | |
| 5 — Throttling | 30 | Two loops: DRF's on login, then ours on the detail page (5.4) |
| 6 — Tokens | 30 | Decoding a JWT is the highlight |
| 7 — Registration | 15 | Fast; it is mostly reading a serializer |
| 8 — HTML side | 35 | The test breakage takes longer than the code |
| 9 — Settings | 25 | `check --deploy` twice |
| 10 — Tests | 20 | Do not type all 39 new tests in class; pull the files from the branch |
| 11 — Commit | 10 | |

Roughly 4.75 hours with the break. If you are short, cut Part 7 (read it aloud from the serializer)
and hand out Part 10's files rather than typing them.

## D.4 Reference branch

The finished day is on **`dharmendra/day10`**, left unmerged on purpose — `main` stays at the end of
Day 9 so that tomorrow's *Start here* still hands students a broken app to fix. Every fenced block
above was taken from that branch, and every **EXPECT** is captured output, including the failures:
the `200` on bello's `PATCH` in Part 1, the six `check --deploy` warnings, and the
`FAILED (failures=21, errors=5)` in Part 8.

The Part 1 walkthrough was captured against a clean checkout of Day 9 in a scratch directory rather
than the trainer's working copy — worth doing again if the day is re-run, because a half-fixed
working copy produces confusing "before" output.

## D.5 Marking the exercise

If you set the day as an assessment, the four numbers in 11.1 are the rubric — `401 / 302 / 403 /
404`. Everything else is discussion. A submission that returns those four codes and has
`python manage.py check --deploy` clean under a production environment has done the day, whatever
its code looks like.

\newpage

# Appendix E — Beyond today, and where to read about it

Today covered the application's own access control. These are the next things a real deployment
needs, in roughly the order they start to matter.

**Browser clients**

* **CORS** — a JavaScript front end on another origin cannot call this API until the server says so.
  [`django-cors-headers`](https://github.com/adamchainz/django-cors-headers). Note that CORS is a
  *browser* control: it does not protect the API from anything that is not a browser.
* **Where to keep a token in a browser** — `localStorage` is readable by any script on the page,
  including an injected one. `httpOnly` cookies are not, but then you need CSRF protection again.
  There is no free option; there is only the trade you pick knowingly.
* **Content Security Policy** — [`django-csp`](https://django-csp.readthedocs.io/), the strongest
  single defence against XSS after Django's own template autoescaping.

**Accounts**

* **Per-account lockout** — [`django-axes`](https://django-axes.readthedocs.io/) locks the *account*
  after N failures, where our throttle limits the *IP*. Distributed credential stuffing defeats
  per-IP limits by definition.
* **Rate limiting off the shelf** — [`django-ratelimit`](https://django-ratelimit.readthedocs.io/)
  does what `blog/throttling.py` does, with key functions, method filters and a sliding window.
  Ours is forty lines so the mechanism is visible; theirs is what you ship.
* **Two-factor** — [`django-otp`](https://django-otp.readthedocs.io/) /
  [`django-two-factor-auth`](https://django-two-factor-auth.readthedocs.io/).
* **A real login page** — wire `path("accounts/", include("django.contrib.auth.urls"))` and write
  `registration/login.html`, instead of borrowing the admin's as Part 8.2 does.
* **Email verification and password reset** — Django ships the reset flow; use it rather than
  writing one.

**Authorisation at scale**

* **Per-object permissions in the database** — [`django-guardian`](https://django-guardian.readthedocs.io/)
  when "owner" becomes "these fourteen people, in these three roles".
* **Groups and `auth_permission`** — Django's own model-level permissions, which
  `DjangoModelPermissions` maps onto. Worth revisiting now that you know why the pasted default was
  wrong.
* **Multi-tenancy** — the queryset-scoping pattern from Part 4 is the whole idea, applied to a
  tenant id instead of an owner. Get it wrong once and it is a data breach, so it belongs in a
  mixin with its own tests.

**Operations**

* **Secrets management** — environment variables are the floor, not the ceiling. AWS Secrets
  Manager, GCP Secret Manager, Vault, or your platform's equivalent.
* **Dependency scanning** — `pip-audit`, GitHub Dependabot. Most real breaches are an unpatched
  dependency, not a clever attack on your code.
* **Structured audit logging** — log *who* did *what* to *which row*. Every `403` in this project
  is currently silent; a real system counts them and alerts on a spike.
* **Security headers, verified** — <https://securityheaders.com> against a staging domain.
* **Django's own security releases** — subscribe to
  [django-announce](https://docs.djangoproject.com/en/5.2/internals/mailing-lists/#django-announce).

**Reading**

* [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) —
  the checklist Part 1's scoreboard is drawn from.
* [Django security topic guide](https://docs.djangoproject.com/en/5.2/topics/security/) — short, and
  every paragraph is load-bearing.
* [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
