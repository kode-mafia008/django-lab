---
title: "Day 4 — DRF, JWT Auth and OpenAPI Docs"
subtitle: "Turning yesterday's HTML-only project into an authenticated JSON API with generated documentation"
author: "Django Practical Lab — daily guide series"
date: "Django 5.2 LTS · DRF 3.18 · Simple JWT 5.5 · drf-spectacular 0.30"
---

# What we did today

| # | Task | Command / change | Result |
| --- | --- | --- | --- |
| 1 | Installed the API stack | `pip install djangorestframework djangorestframework-simplejwt drf-spectacular` | Four new entries in `INSTALLED_APPS` |
| 2 | Configured DRF | `REST_FRAMEWORK` in `config/settings.py` | JWT is the default authentication class |
| 3 | Configured Simple JWT | `SIMPLE_JWT` + the blacklist app | 30-minute access tokens, rotating refresh tokens |
| 4 | Created the auth app | `python manage.py startapp accounts` | A home for everything user-facing |
| 5 | Wrote four serializers | `accounts/serializers.py` | User, register, login, login-response |
| 6 | Wrote four views | `accounts/views.py` | `register`, `login`, `me`, `logout` |
| 7 | Routed them | `accounts/urls.py` + `include()` | `/accounts/...` answers JSON |
| 8 | Walked the whole flow | `curl` | 401 → register → login → 200 → logout → 401 |
| 9 | Generated the docs | `drf-spectacular` | `/api/schema/`, `/api/schema/swagger-ui/`, `/api/schema/redoc/` |

Everything below runs against what is in this repository, starting from `main` at the end of Day 3 — a `blog` app whose `Author` rows render as HTML pages, and no API layer at all.

## Conventions

Same as Days 1–3.

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
git switch -c <first_name>/day4
```

**TYPE**

```bash
python manage.py migrate
python manage.py runserver
```

**EXPECT** — the server starts, and <http://127.0.0.1:8000/blogs/> lists the authors you rendered yesterday.

**CHECKPOINT 0** — you are on branch `<first_name>/day4`, `migrate` is clean, the author list renders, and `pip list` shows Django but **not** `djangorestframework`. Today installs it.

If the author page is empty, create two or three rows in `/admin/` first. Today never touches the `Author` model, but a populated database makes the last exercise worth doing.

Stop the server with `Ctrl-C` before the next part.

\newpage

# Part 1 — Why an API needs its own kind of login

Yesterday's pages are for a person holding a browser. Today's endpoints are for a program — a React frontend, a Flutter app, another service, a cron job. That change of audience breaks the login mechanism you already have.

## 1.1 Sessions, and why they stop working

Django's built-in login is **session-based**. On a successful login the server creates a row in `django_session`, and hands the browser a `sessionid` cookie. Every later request carries the cookie; Django looks the row up and knows who you are.

Three things about that are fine for a website and awkward for an API:

| Session cookies | Consequence for an API |
| --- | --- |
| The server stores state | Every server in a cluster needs the same session store |
| The browser sends the cookie automatically | A mobile app has no cookie jar; a CORS request needs extra configuration |
| Logout means deleting a row | Which is genuinely reliable — hold that thought until Part 6.5 |

## 1.2 What a token does instead

A **JSON Web Token** carries the claim *and* the proof, and the server stores nothing. It is three base64url segments joined by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 . eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3OTkyNDM3LCJ1c2VyX2lkIjoiMiJ9 . sgYib3TTIGpmgnul_UdzWobEI6hwLoof0sxMxjbUr20
        header                                        payload                                              signature
```

- **Header** — the algorithm. `HS256` here.
- **Payload** — the claims. `user_id`, `exp` (expiry), `jti` (a unique token id), plus anything you add.
- **Signature** — `HMAC-SHA256(header.payload, SECRET_KEY)`.

**WHY the payload is not secret** — base64 is encoding, not encryption. Anyone holding the token can read `user_id` and `exp`; paste one into <https://jwt.io> and see. What they cannot do is *change* a claim, because they cannot recompute the signature without `SECRET_KEY`. So: never put anything in a token you would not print on a postcard, and never let `SECRET_KEY` reach a repository.

## 1.3 Two tokens, not one

Simple JWT issues a **pair**:

| Token | Lifetime today | Sent where | Job |
| --- | --- | --- | --- |
| `access` | 30 minutes | `Authorization: Bearer <token>` on every request | Prove who you are |
| `refresh` | 1 day | Body of `POST /accounts/refresh/` only | Buy a new access token |

**WHY two** — the access token travels constantly, so it is the one most likely to leak; keeping it short-lived limits the damage to half an hour. The refresh token moves rarely and can therefore live longer without being as exposed. This split is the entire reason the flow has two steps instead of one.

\newpage

# Part 2 — Install and configure the API stack

## 2.1 Install

**TYPE**

```bash
pip install djangorestframework djangorestframework-simplejwt drf-spectacular
```

**EXPECT** — a `Successfully installed` line naming those three plus nine dependencies:

```
Successfully installed PyYAML-6.0.3 attrs-26.1.0 djangorestframework-3.18.0
djangorestframework-simplejwt-5.5.1 drf-spectacular-0.30.0 inflection-0.5.1
jsonschema-4.26.0 jsonschema-specifications-2025.9.1 pyjwt-2.13.0
referencing-0.37.0 rpds-py-2026.6.3 uritemplate-4.2.0
```

| Package | What it gives you |
| --- | --- |
| `djangorestframework` | Serializers, generic views, permissions, the browsable API |
| `djangorestframework-simplejwt` | Token obtain / refresh / verify / blacklist, and the `PyJWT` plumbing under them |
| `drf-spectacular` | Reads your code, emits an OpenAPI 3 document, serves Swagger UI and ReDoc |

## 2.2 Pin them

**TYPE**

```bash
pip freeze > requirements.txt
cat requirements.txt
```

**EXPECT**

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

**WHY `>` and not `>>`** — `pip freeze > requirements.txt` *replaces* the file with the full resolved tree. Appending instead leaves the old lines in place, and you end up with `sqlparse` pinned twice. A duplicate is harmless until the two lines disagree, at which point installs become order-dependent. Always overwrite.

**CHECKPOINT 1** — `cat requirements.txt` shows fifteen lines, each name appearing exactly once.

## 2.3 Register the apps

**TYPE** — in `config/settings.py`, replace the `INSTALLED_APPS` list:

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

`accounts` does not exist yet — Part 3 creates it. Django will complain if you `runserver` before then; that is expected.

**WHY `token_blacklist` is a separate app** — it is the only part of Simple JWT that owns database tables. Listing it creates `token_blacklist_outstandingtoken` and `token_blacklist_blacklistedtoken`, which is what makes logout possible at all. Leave it out and `RefreshToken(...).blacklist()` raises at runtime, in the one code path nobody tests by hand.

## 2.4 Configure DRF

**TYPE** — append to `config/settings.py`:

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
}
```

Read it as three separate answers:

| Setting | Question it answers |
| --- | --- |
| `DEFAULT_AUTHENTICATION_CLASSES` | **Who are you?** Try the `Bearer` header first, fall back to the session cookie |
| `DEFAULT_PERMISSION_CLASSES` | **May you?** By default: only if you are somebody |
| `DEFAULT_SCHEMA_CLASS` | **How is this documented?** Hand it to drf-spectacular |

**WHY `SessionAuthentication` stays in the list** — it is what makes DRF's browsable API usable while you are logged into `/admin/` in the same browser. It costs nothing and saves a lot of token-pasting during development.

**WHY the default is `IsAuthenticated`** — defaults should fail closed. A view that forgets its `permission_classes` then rejects anonymous users instead of silently exposing data. The three views that *must* be open — register, login, refresh — say so explicitly, and an explicit `AllowAny` is easy to spot in review. The drf-spectacular README suggests `DjangoModelPermissionsOrAnonReadOnly` here; that one requires a model-backed `queryset` on every view and grants read access to the anonymous world, which is a surprising default to inherit before you have thought about it.

## 2.5 Configure Simple JWT

**TYPE** — append:

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

**TYPE** — and at the top of the file, above `from pathlib import Path`:

```python
from datetime import timedelta
```

| Setting | Effect |
| --- | --- |
| `ROTATE_REFRESH_TOKENS` | Every refresh returns a *new* refresh token as well as a new access token |
| `BLACKLIST_AFTER_ROTATION` | The refresh token you just spent is immediately dead |
| `AUTH_HEADER_TYPES` | The header word. `Bearer`, not `Token`, not `JWT` |
| `SIGNING_KEY` | Defaults to `SECRET_KEY`; written out so you can see what to change in production |

**WHY rotation plus blacklisting** — together they turn a stolen refresh token into a detectable event. If an attacker uses the token first, the real user's next refresh fails; if the user goes first, the attacker's fails. Either way somebody gets a `401` that should not have happened, instead of a quiet year of access. You will see this fire in Part 6.4.

## 2.6 Configure drf-spectacular

**TYPE** — append:

```python
# drf-spectacular
# https://drf-spectacular.readthedocs.io/en/latest/settings.html

SPECTACULAR_SETTINGS = {
    'TITLE': 'Django Lab API',
    'DESCRIPTION': 'JWT registration and login for the Django Lab. Built on Day 4.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': True},
}
```

**WHY `SERVE_PERMISSIONS`** — you just made `IsAuthenticated` the project default, and the schema view inherits it. Without this line `/api/schema/` returns `401` and Swagger UI renders an empty page, which is a confusing ten minutes for everyone. **WHY `SERVE_INCLUDE_SCHEMA: False`** — it keeps the schema endpoint from documenting itself. **WHY `persistAuthorization`** — Swagger UI remembers the token you pasted across reloads.

## 2.7 Create the blacklist tables

**TYPE**

```bash
python manage.py migrate
```

**EXPECT** — the tail of the output — twelve `token_blacklist` migrations apply:

```
  Applying token_blacklist.0001_initial... OK
  Applying token_blacklist.0002_outstandingtoken_jti_hex... OK
  ...
  Applying token_blacklist.0012_alter_outstandingtoken_user... OK
  Applying token_blacklist.0013_alter_blacklistedtoken_options_and_more... OK
```

**CHECKPOINT 2** — `python manage.py migrate` is clean. `python manage.py check` will still fail with `ModuleNotFoundError: No module named 'accounts'` until the next part; nothing else should be wrong.

\newpage

# Part 3 — The accounts app and its serializers

## 3.1 Create the app

**TYPE**

```bash
python manage.py startapp accounts
```

**EXPECT** — a new `accounts/` directory. You already listed it in `INSTALLED_APPS`, so:

**TYPE**

```bash
python manage.py check
```

**EXPECT**

```
System check identified no issues (0 silenced).
```

**WHY a separate app** — `blog` is about authors and posts; `accounts` is about who is allowed to touch them. Keeping them apart means you can lift `accounts` into the next project unchanged. Note that `accounts/models.py` stays empty all day: you are **not** writing a user model, you are using `django.contrib.auth.models.User`.

## 3.2 The user serializer

**TYPE** — `accounts/serializers.py`:

```python
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
```

**WHY list `fields` explicitly** — `fields = "__all__"` on `User` would serialize `password`, `is_superuser`, `is_staff` and every permission relation straight out to the client. The hash is not directly reversible, but publishing it hands an attacker an offline cracking target for free. On the user model, always name the fields.

## 3.3 The register serializer

**TYPE** — append:

```python
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
```

Three lines, three separate jobs:

- `write_only=True` — accepted on input, never rendered on output. Without it, the `201` response echoes the password back.
- `validators=[validate_password]` — runs `AUTH_PASSWORD_VALIDATORS` from `settings.py`, the same rules `createsuperuser` uses.
- `create()` — the important one.

**WHY `create()` must be overridden** — `ModelSerializer.create()` calls `User.objects.create(**validated_data)`, which writes `password` to the column **verbatim**. The row saves, the endpoint returns `201`, and everything looks fine. Then login fails forever, because `check_password()` compares the submitted password against what it assumes is a hash. This is the single most common bug in this file. Prove it to yourself:

**TYPE** — temporarily delete the `create()` method, restart the server, register a user, then:

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='asha')
print(repr(u.password))
print('check_password ->', u.check_password('lab-passphrase-2026'))"
```

**EXPECT**

```
'lab-passphrase-2026'
check_password -> False
```

The password is sitting in the database in plain text, and the user can never log in. `User.objects.create_user()` is the fix: it calls `set_password()`, which hashes with PBKDF2 and a per-user salt. Put the `create()` method back and delete that user before continuing.

**DOCS** — [Password management in Django](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/) · [`create_user()`](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/#django.contrib.auth.models.UserManager.create_user)

## 3.4 The login serializer

**TYPE** — append:

```python
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
```

Two different customisations that are easy to confuse:

| Method | Changes | Visible where |
| --- | --- | --- |
| `get_token()` | What is **inside** the signed token | Decode the token — `jwt.io`, or the payload segment |
| `validate()` | What the **login response body** contains | The JSON returned by `POST /accounts/login/` |

**WHY add `username` to the token** — a frontend can render "Signed in as asha" straight from the token it already holds, with no extra request. **WHY also return the whole user in the body** — because the frontend should not have to decode a JWT to fill in a profile header. **WHY not put the email in the token too** — every claim you add is bytes on every request, forever, and it goes stale the moment the user edits their profile. Tokens carry identity, not data.

## 3.5 The login response serializer

**TYPE** — append:

```python
class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
```

Nothing at runtime uses this class. It exists purely so drf-spectacular can document the login response correctly — Part 7.4 shows the wrong documentation it replaces. Note it subclasses plain `Serializer`, not `ModelSerializer`: there is no model behind a token pair.

**CHECKPOINT 3** — `accounts/serializers.py` holds four classes and `python manage.py check` is clean.

\newpage

# Part 4 — The views

**TYPE** — `accounts/views.py`, in full:

```python
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response(
                {"error": "Token is invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)
```

## 4.1 Reading the four views

**`RegisterView`** — `CreateAPIView` already implements `POST`. The `create()` override exists for one reason: to answer with `UserSerializer` instead of `RegisterSerializer`, so the response shape matches `/accounts/me/`. Two endpoints that describe the same object should return the same fields.

**WHY `permission_classes = [AllowAny]`** — the project default is `IsAuthenticated`. Without this line you would need an account to create an account.

**`LoginView`** — nine words of actual work. `TokenObtainPairView` does the authenticating; you are only swapping in your serializer.

**`MeView`** — the `get_object()` override is what makes it "me". `RetrieveAPIView` normally reads a `pk` out of the URL and looks the row up; here the object is already known, because authentication resolved it into `request.user`.

**WHY not `/accounts/users/<id>/`** — a URL with an id in it invites `GET /accounts/users/2/` and a permission check you have to remember to write. `/accounts/me/` cannot leak someone else's row, because it never accepts an id.

**`LogoutView`** — plain `APIView`, because there is no object and no queryset. Three outcomes:

| Case | Status |
| --- | --- |
| No `refresh` in the body | `400` with `{"error": "Refresh token is required"}` |
| A refresh token that is expired, malformed or already blacklisted | `400` with `{"error": "Token is invalid or expired"}` |
| A valid refresh token | `205 Reset Content`, no body |

**WHY `205` and not `200`** — `205 Reset Content` literally means *the client should clear the view it was working with*. For a logout it says "drop your stored tokens" in one status code.

**WHY logout only half-works** — the refresh token is blacklisted immediately, but the access token stays valid until it expires. There is no server-side list of live access tokens to remove it from; that is the price of statelessness. Your 30-minute `ACCESS_TOKEN_LIFETIME` is the actual bound on how long a logged-out session can still read data, which is a reason to keep it short.

**CHECKPOINT 4** — `python manage.py check` is clean. Nothing is reachable yet; no URLs are wired.

\newpage

# Part 5 — Routing

## 5.1 The app URLconf

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

**WHY the name is exactly `urlpatterns`** — `include()` looks for that module-level name and nothing else. Spell it `url_patterns` and Django does not raise; it finds no patterns and every URL under the prefix 404s, with no error message pointing at the typo. If your routes silently do not exist, check this line first.

**WHY `refresh` and `verify` are imported, not written** — Simple JWT ships both views. Refresh takes a refresh token and returns a new access token; verify takes any token and tells you whether the signature and expiry hold. Writing them yourself would be reimplementing the library.

## 5.2 The project URLconf

**TYPE** — `config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # HTML pages
    path("blogs/", include("blog.urls")),

    # JSON API
    path("accounts/", include("accounts.urls")),

    # OpenAPI schema and docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
```

Note `path("blogs/", ...)`: yesterday the author list lived at `/`, and today it moves under a prefix so the API routes read cleanly alongside it.

**WHY `url_name="schema"` appears twice** — both UIs need to fetch the schema document, and they find it by reversing that name. It has to match the `name=` on the `SpectacularAPIView` route exactly. Rename one without the other and both UIs load as a blank page with a 404 in the browser console.

**TYPE**

```bash
python manage.py runserver
```

**CHECKPOINT 5** — the server starts clean, <http://127.0.0.1:8000/blogs/> still lists authors, and <http://127.0.0.1:8000/accounts/me/> returns `401`, not `404`. A `404` here means the URLconf is not wired; re-read 5.1.

\newpage

# Part 6 — Walk the whole flow with curl

Leave `runserver` going in one terminal. Everything below runs in a second one. Each block is real captured output.

## 6.1 The wall

**TYPE**

```bash
curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/accounts/me/
```

**EXPECT**

```
{"detail":"Authentication credentials were not provided."}
HTTP 401
```

That is `DEFAULT_PERMISSION_CLASSES` doing its job. Everything after this is the work of getting past it.

## 6.2 Register

**TYPE** — a deliberately bad password first:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"asha","email":"asha@example.com","password":"password"}'
```

**EXPECT**

```
{"password":["This password is too common."]}
HTTP 400
```

**WHY that message and not others** — `validate_password` is attached as a *field* validator, so it receives the password and nothing else. `CommonPasswordValidator`, `MinimumLengthValidator` and `NumericPasswordValidator` all work on the string alone and fire normally. `UserAttributeSimilarityValidator` cannot: it needs the user object to compare against, and a field validator never sees one. Try `"asha1234"` and watch it be accepted despite containing the username. Passing the user through requires moving the check into `validate()`, where `attrs` holds the other fields — a good exercise, and a good reason not to assume "the validators are on" means every validator is running.

**TYPE**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"asha","email":"asha@example.com","password":"lab-passphrase-2026"}'
```

**EXPECT** — the `id` depends on how many users already exist, so yours may differ:

```
{"id":2,"username":"asha","email":"asha@example.com"}
HTTP 201
```

No `password` field in the response. That is `write_only=True`.

## 6.3 Log in

**TYPE**

```bash
curl -s -X POST http://127.0.0.1:8000/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"asha","password":"lab-passphrase-2026"}'
```

**EXPECT**

```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc4ODA3NzAzNywiaWF0IjoxNzg3OTkwNjM3LCJqdGkiOiIwNDllZDRmZmM1NGU0YmJiYTQ3NjdmNzA5ZTljMTA5NCIsInVzZXJfaWQiOiIyIiwidXNlcm5hbWUiOiJhc2hhIn0.ZM4fhxmUXkNOnKHXqKrdEkxp7QHI1qr1-q95KU9tbk4",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3OTkyNDM3LCJpYXQiOjE3ODc5OTA2MzcsImp0aSI6IjE5YzA2MGFiNGQyZjQ4YjBiNzBiOTEwZjBiMmExZjFmIiwidXNlcl9pZCI6IjIiLCJ1c2VybmFtZSI6ImFzaGEifQ.sgYib3TTIGpmgnul_UdzWobEI6hwLoof0sxMxjbUr20",
    "user": {
        "id": 2,
        "username": "asha",
        "email": "asha@example.com"
    }
}
```

The `user` key is `LoginSerializer.validate()`. The `"username":"asha"` inside the token payload is `get_token()` — paste the middle segment into <https://jwt.io> and read it.

**TYPE** — keep the tokens in shell variables:

```bash
ACCESS=<paste the access token>
REFRESH=<paste the refresh token>
```

**TYPE**

```bash
curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/accounts/me/ \
  -H "Authorization: Bearer $ACCESS"
```

**EXPECT**

```
{"id":2,"username":"asha","email":"asha@example.com"}
HTTP 200
```

**CHECKPOINT 6** — the same URL that returned `401` in 6.1 now returns your user. One header is the entire difference.

**TYPE** — verify:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/accounts/verify/ \
  -H "Content-Type: application/json" -d "{\"token\":\"$ACCESS\"}"
```

**EXPECT**

```
{}
HTTP 200
```

An empty body and a `200` means valid. `verify` answers one question and returns no data.

## 6.4 Refresh, and see rotation bite

**TYPE**

```bash
curl -s -X POST http://127.0.0.1:8000/accounts/refresh/ \
  -H "Content-Type: application/json" -d "{\"refresh\":\"$REFRESH\"}"
```

**EXPECT** — two tokens back, not one, because `ROTATE_REFRESH_TOKENS` is on:

```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl9..."
}
```

**TYPE** — now send the *same old* refresh token again:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/accounts/refresh/ \
  -H "Content-Type: application/json" -d "{\"refresh\":\"$REFRESH\"}"
```

**EXPECT**

```
{"detail":"Token is blacklisted","code":"token_not_valid"}
HTTP 401
```

That is `BLACKLIST_AFTER_ROTATION`. A refresh token is single-use: spend it, store the replacement, discard the old one. A frontend that keeps the original in `localStorage` and never overwrites it works perfectly for exactly one refresh and then logs the user out — a bug that reliably takes an afternoon to find, because it only shows up 30 minutes after login.

**TYPE** — hold on to the new one:

```bash
REFRESH=<paste the new refresh token>
```

## 6.5 Log out

**TYPE** — the missing-field path first:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/accounts/logout/ \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" -d '{}'
```

**EXPECT**

```
{"error":"Refresh token is required"}
HTTP 400
```

**TYPE**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/accounts/logout/ \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"
```

**EXPECT** — an empty body:

```

HTTP 205
```

**TYPE**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/accounts/refresh/ \
  -H "Content-Type: application/json" -d "{\"refresh\":\"$REFRESH\"}"
```

**EXPECT**

```
{"detail":"Token is blacklisted","code":"token_not_valid"}
HTTP 401
```

**TYPE** — and now the uncomfortable part:

```bash
curl -s -w "\nHTTP %{http_code}\n" http://127.0.0.1:8000/accounts/me/ \
  -H "Authorization: Bearer $ACCESS"
```

**EXPECT**

```
{"id":2,"username":"asha","email":"asha@example.com"}
HTTP 200
```

**WHY the "logged out" user is still reading data** — nothing revoked the access token, because nothing *can*. The server does not keep a list of issued access tokens; it just checks the signature and `exp` on each request. Logout kills the ability to get *new* access tokens, and the current one dies on its own schedule. If your product cannot tolerate that window, the options are a shorter `ACCESS_TOKEN_LIFETIME`, or checking a revocation list on every request — which is choosing sessions again, with extra steps.

**CHECKPOINT 7** — you have driven `401 → 201 → 200 → 401` end to end and can explain why the last `/accounts/me/` still succeeded.

\newpage

# Part 7 — Generated documentation

Everything so far was invisible to anyone who was not watching your terminal. drf-spectacular reads the same views and serializers and writes the contract down.

## 7.1 The three URLs

With the server running:

| URL | What it is |
| --- | --- |
| <http://127.0.0.1:8000/api/schema/> | The OpenAPI 3 document, downloaded as YAML |
| <http://127.0.0.1:8000/api/schema/swagger-ui/> | Swagger UI — interactive, sends real requests |
| <http://127.0.0.1:8000/api/schema/redoc/> | ReDoc — read-only, better for handing to another team |

**TYPE**

```bash
curl -s http://127.0.0.1:8000/api/schema/ | head -8
```

**EXPECT**

```yaml
openapi: 3.0.3
info:
  title: Django Lab API
  version: 1.0.0
  description: JWT registration and login for the Django Lab. Built on Day 4.
paths:
  /accounts/login/:
    post:
```

`title`, `version` and `description` are the `SPECTACULAR_SETTINGS` you wrote in 2.6. Everything under `paths:` was inferred from your code.

## 7.2 Generate it as a file

**TYPE**

```bash
python manage.py spectacular --file schema.yml --validate
```

**EXPECT** — not silence. Four errors, one unique:

```
accounts/views.py:38: Error [LogoutView]: unable to guess serializer. This is graceful
fallback handling for APIViews. Consider using GenericAPIView as view base class, if view
is under your control. Either way you may want to add a serializer_class (or method).
Ignoring view for now.

Schema generation summary:
Warnings: 0 (0 unique)
Errors:   4 (1 unique)
```

**WHY it cannot guess** — `RegisterView` and `MeView` declare a `serializer_class`, so spectacular reads the fields off it. `LogoutView` is a bare `APIView` whose body shape lives inside `request.data.get("refresh")` — ordinary Python that no static analysis can turn into a schema.

## 7.3 What the wrong documentation looks like

**TYPE**

```bash
grep -A 6 "responses:" schema.yml | head -20
```

Look at the `200` response of `/accounts/login/` in `schema.yml`:

```yaml
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Login'
```

The login endpoint is documented as *returning a username and a password*. It returns two tokens and a user. Spectacular assumed the response matches the request serializer, which is right for most endpoints and wrong for this one — and a frontend developer reading this page would write code against a shape that does not exist.

This is what `LoginResponseSerializer` was written for in 3.5.

## 7.4 Fix both with `@extend_schema`

**TYPE** — in `accounts/views.py`, add to the imports:

```python
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
```

**TYPE** — and change the `rest_framework` import line to bring in `serializers`:

```python
from rest_framework import generics, serializers, status
```

**TYPE** — extend the serializer import:

```python
from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)
```

**TYPE** — decorate `LoginView`:

```python
@extend_schema(
    responses={200: LoginResponseSerializer},
    description="Exchange a username and password for an access/refresh token pair.",
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
```

**TYPE** — and `LogoutView`:

```python
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    @extend_schema(
        request=inline_serializer(
            name="Logout",
            fields={"refresh": serializers.CharField()},
        ),
        responses={
            205: OpenApiResponse(description="Refresh token blacklisted."),
            400: OpenApiResponse(description="Refresh token missing, invalid or expired."),
        },
    )
    def post(self, request):
        ...
```

Leave the body of `post()` exactly as it was.

**TYPE**

```bash
python manage.py spectacular --file schema.yml --validate
```

**EXPECT** — silence, and exit code `0`. No summary block is printed when there is nothing to report.

The two paths now read correctly:

```yaml
  /accounts/login/:
    post:
      description: Exchange a username and password for an access/refresh token pair.
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LoginResponse'
  /accounts/logout/:
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Logout'
      security:
      - jwtAuth: []
      - cookieAuth: []
      responses:
        '205':
          description: Refresh token blacklisted.
        '400':
          description: Refresh token missing, invalid or expired.
```

**WHY `inline_serializer`** — the logout body has one field and no model. Writing a `LogoutSerializer` class for it would be a real class that no runtime code ever instantiates; `inline_serializer` describes the shape at the point of use instead.

**WHY `--validate` belongs in CI** — the schema is generated, so it silently drifts the moment somebody adds a view without a serializer. `python manage.py spectacular --validate --fail-on-warn` in a pipeline turns that drift into a failed build.

**CHECKPOINT 8** — `spectacular --validate` prints nothing and exits `0`.

## 7.5 Do not commit `schema.yml`

**TYPE**

```bash
rm schema.yml
```

It is generated output. Committing it means reviewing a 400-line diff every time a serializer field changes, and merge-conflicting on it constantly. Commit the code that generates it; generate the file in CI when you need to publish it.

\newpage

# Part 8 — Drive the API from Swagger UI

Open <http://127.0.0.1:8000/api/schema/swagger-ui/>.

1. Expand `POST /accounts/login/` → **Try it out** → fill in `asha` and `lab-passphrase-2026` → **Execute**. The response pane shows the token pair.
2. Copy the `access` value — the string only, no quotes.
3. Click **Authorize** at the top right. Type `Bearer `, a space, then paste the token. Click **Authorize**, then **Close**.
4. Expand `GET /accounts/me/` → **Try it out** → **Execute**.

**EXPECT** — `200` and your user object. Before step 3 the same call returns `401`.

**WHY you type `Bearer` by hand** — the schema's security scheme is a raw HTTP header, and `AUTH_HEADER_TYPES = ('Bearer',)` in your settings is what the server expects to find in front of the token. Paste the token alone and the header reads `Authorization: eyJhbGci...`, which the parser rejects. This trips up nearly everyone once.

Every request Swagger UI sends is a real request against your running server. This page is the whole day made visible: the same views, the same serializers, the same tokens, now documented and clickable.

\newpage

# Part 9 — Commit and push

**TYPE**

```bash
git status --short
```

**EXPECT**

```
 M config/settings.py
 M config/urls.py
 M requirements.txt
?? accounts/
```

If `schema.yml`, `db.sqlite3`, `venv/` or `__pycache__/` appear, stop and fix `.gitignore` before committing.

**TYPE**

```bash
git add accounts config/settings.py config/urls.py requirements.txt
git commit -m "Day 4: DRF, JWT auth and OpenAPI docs"
git push -u origin <first_name>/day4
```

Open a pull request against `main`.

## 9.1 Prove it worked

The most common broken branch of the day is one where `requirements.txt` was never re-frozen: the code imports `rest_framework`, nothing pins it, and the branch cannot be installed by anyone but you.

**TYPE** — in a directory outside your project:

```bash
git clone -b <first_name>/day4 <your-repo-url> day4-check
cd day4-check
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

**EXPECT** — `/accounts/me/` on port 8001 returns `401`, and `/api/schema/swagger-ui/` lists six `/accounts/` operations. If `pip install` produced a project that cannot import `rest_framework`, your `requirements.txt` is stale.

**CHECKPOINT 9** — a clean clone of your branch installs and runs.

\newpage

# Appendix A — Troubleshooting

| You see | It means | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'rest_framework'` | Installed outside the venv, or venv not active | Activate the venv, reinstall |
| `ModuleNotFoundError: No module named 'accounts'` | Listed in `INSTALLED_APPS` but `startapp accounts` not run | Run it (3.1) |
| `NameError: name 'timedelta' is not defined` | `SIMPLE_JWT` added without the import | `from datetime import timedelta` at the top of `settings.py` (2.5) |
| Every `/accounts/...` URL 404s | `url_patterns` instead of `urlpatterns` | Rename the list (5.1) |
| `/accounts/me/` 404s but `/admin/` works | `include("accounts.urls")` missing or commented out | Check `config/urls.py` (5.2) |
| Login always returns `401 No active account found` | `create()` not overridden, so the password was stored unhashed | `User.objects.create_user()` (3.3), then re-register |
| `401 {"detail":"Authentication credentials were not provided."}` | No `Authorization` header | Header must be `Authorization: Bearer <token>` |
| `401 {"detail":"Given token not valid for any token type"}` | Access token expired, or you pasted the refresh token | Refresh, or log in again |
| `401 {"detail":"Token is blacklisted"}` | That refresh token was already spent or logged out | Use the newest refresh token (6.4) |
| `AttributeError: 'AnonymousUser' object has no attribute ...` on `/accounts/me/` | `permission_classes` missing on `MeView` | `[IsAuthenticated]` (Part 4) |
| `MeView` 500s with "expected view to be called with a URL keyword argument named pk" | `get_object()` not overridden | Add it (Part 4) |
| `rest_framework_simplejwt.exceptions.TokenError` on logout | `token_blacklist` not in `INSTALLED_APPS`, or not migrated | Add it and `migrate` (2.3, 2.7) |
| `/api/schema/` returns `401` | The schema view inherited `IsAuthenticated` | `SERVE_PERMISSIONS` in `SPECTACULAR_SETTINGS` (2.6) |
| Swagger UI loads blank, console shows 404 for the schema | `url_name` does not match the `name=` on the schema route | Both must say `schema` (5.2) |
| Swagger UI **Authorize** appears to do nothing | Token pasted without the `Bearer ` prefix | Type `Bearer `, space, then the token (Part 8) |
| `spectacular` reports `unable to guess serializer` | A bare `APIView` with no serializer | `@extend_schema` on that method (7.4) |
| `403` where you expected `401` | You *are* authenticated; the permission class refused you | Read `permission_classes` on that view |
| `That port is already in use` | The first `runserver` is still up | `runserver 8001`, or stop the other one |

\newpage

# Appendix B — Official documentation index

**Django 5.2 — auth and settings**

- [Using the authentication system](https://docs.djangoproject.com/en/5.2/topics/auth/default/) · [`User` model reference](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/)
- [Password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/) · [`AUTH_PASSWORD_VALIDATORS`](https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators)
- [Customising authentication](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/) — read before you ever need a custom user model
- [URL dispatcher](https://docs.djangoproject.com/en/5.2/topics/http/urls/) · [`path()` and `include()`](https://docs.djangoproject.com/en/5.2/ref/urls/)
- [Settings reference](https://docs.djangoproject.com/en/5.2/ref/settings/) · [Deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

**Django REST Framework**

- [Home](https://www.django-rest-framework.org/) · [Quickstart](https://www.django-rest-framework.org/tutorial/quickstart/)
- [Serializers](https://www.django-rest-framework.org/api-guide/serializers/) · [Serializer fields](https://www.django-rest-framework.org/api-guide/fields/) · [Validators](https://www.django-rest-framework.org/api-guide/validators/)
- [Class-based views](https://www.django-rest-framework.org/api-guide/views/) · [Generic views](https://www.django-rest-framework.org/api-guide/generic-views/)
- [Authentication](https://www.django-rest-framework.org/api-guide/authentication/) · [Permissions](https://www.django-rest-framework.org/api-guide/permissions/) · [Status codes](https://www.django-rest-framework.org/api-guide/status-codes/)
- [Settings](https://www.django-rest-framework.org/api-guide/settings/) · [The browsable API](https://www.django-rest-framework.org/topics/browsable-api/) · [Testing](https://www.django-rest-framework.org/api-guide/testing/)

**Simple JWT**

- [Documentation home](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/) · [Getting started](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html)
- [Settings](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/settings.html) · [Token types](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/token_types.html)
- [Customising token claims](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/customizing_token_claims.html) · [Blacklist app](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/blacklist_app.html)

**drf-spectacular and OpenAPI**

- [Documentation home](https://drf-spectacular.readthedocs.io/en/latest/) · [Settings list](https://drf-spectacular.readthedocs.io/en/latest/settings.html)
- [Customisation and `@extend_schema`](https://drf-spectacular.readthedocs.io/en/latest/customization.html) · [FAQ](https://drf-spectacular.readthedocs.io/en/latest/faq.html)
- [OpenAPI specification](https://spec.openapis.org/oas/latest.html) · [Swagger UI](https://swagger.io/tools/swagger-ui/) · [ReDoc](https://redocly.com/redoc/)

**JWT background**

- [jwt.io — paste a token and read it](https://jwt.io) · [RFC 7519](https://www.rfc-editor.org/rfc/rfc7519) · [OWASP JWT cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

\newpage

# Appendix C — Command cheat sheet

```bash
# the API stack
pip install djangorestframework djangorestframework-simplejwt drf-spectacular
pip freeze > requirements.txt
python manage.py startapp accounts
python manage.py migrate                  # creates the token_blacklist tables

# schema
python manage.py spectacular                            # print to stdout
python manage.py spectacular --file schema.yml          # write it
python manage.py spectacular --validate --fail-on-warn  # CI form

# exercising the API
BASE=http://127.0.0.1:8000

curl -s -X POST $BASE/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"asha","email":"asha@example.com","password":"lab-passphrase-2026"}'

curl -s -X POST $BASE/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"asha","password":"lab-passphrase-2026"}'

curl -s $BASE/accounts/me/ -H "Authorization: Bearer $ACCESS"

curl -s -X POST $BASE/accounts/refresh/ \
  -H "Content-Type: application/json" -d "{\"refresh\":\"$REFRESH\"}"

curl -s -X POST $BASE/accounts/logout/ \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"

# inspecting
python manage.py shell -c "
from django.contrib.auth.models import User
u = User.objects.get(username='asha')
print(repr(u.password)[:40], u.check_password('lab-passphrase-2026'))"
echo ".tables" | python manage.py dbshell
python manage.py showmigrations token_blacklist
```

**The URL map after today**

| URL | What answers it |
| --- | --- |
| `/admin/` | Django admin |
| `/blogs/` | `blog.views.author_list` — HTML |
| `/blogs/authors/<id>/` | `blog.views.author_detail` — HTML |
| `/accounts/register/` | `RegisterView` — `201` with the new user |
| `/accounts/login/` | `LoginView` — the token pair plus the user |
| `/accounts/refresh/` | `TokenRefreshView` — rotates both tokens |
| `/accounts/verify/` | `TokenVerifyView` — `{}` and `200` if valid |
| `/accounts/logout/` | `LogoutView` — `205`, blacklists the refresh token |
| `/accounts/me/` | `MeView` — the authenticated user |
| `/api/schema/` | The OpenAPI document |
| `/api/schema/swagger-ui/` | Swagger UI |
| `/api/schema/redoc/` | ReDoc |

**Status codes used today**

| Code | Meaning here |
| --- | --- |
| `200` | Read succeeded |
| `201` | User created |
| `205` | Logged out — client should discard its tokens |
| `400` | The body was wrong: weak password, duplicate username, missing refresh token |
| `401` | No token, expired token, blacklisted token, or bad credentials |
| `403` | Authenticated, but not permitted |

\newpage

# Appendix D — Trainer notes

**Where this day came from** — Day 3 shipped the HTML pages *and* an API layer. The API half was reverted off `main` (PR #15) so the room could build it live rather than read it, which is what today is. `main` therefore starts at "authors render as HTML, no DRF installed", and the Day 3 guide's Parts 3–7 are the reference for the same material done at speed.

**Deltas from the live session (PR #16)** — the guide above is the corrected build, verified end to end. Five differences worth naming out loud, because everyone in the room has the uncorrected version on their branch:

| Live session | Guide | Why it matters |
| --- | --- | --- |
| `RegisterSerializer` with no `create()` | `User.objects.create_user()` | Passwords were stored in plain text; login could never succeed |
| `url_patterns = []` in `accounts/urls.py`, `include()` commented out | `urlpatterns` with six routes | Nothing under `/accounts/` was reachable |
| `rest_framework_simplejwt` and `token_blacklist` not in `INSTALLED_APPS` | Both listed, `migrate` run | `RefreshToken(...).blacklist()` raises without the tables |
| No `SIMPLE_JWT` block, no `DEFAULT_AUTHENTICATION_CLASSES` | Both written | `Authorization: Bearer` was never actually parsed |
| `UserView(RetrieveAPIView)` with no `get_object()` | `MeView.get_object()` returns `request.user` | Otherwise DRF looks for a `pk` in the URL and 500s |

Also: `DEFAULT_PERMISSION_CLASSES` moved from the drf-spectacular README's `DjangoModelPermissionsOrAnonReadOnly` to `IsAuthenticated` (2.4), and the duplicate `sqlparse` pin from an appended `pip freeze` is gone (2.2). Walking the room through this table is a better twenty minutes than re-teaching the parts that worked.

**Live-demo order that lands best**

1. Open `/blogs/` and ask: *how does a React app log into this?* The session cookie answer falls apart in about thirty seconds, and that is Part 1.
2. Do 6.1 before anything else. A `401` on an endpoint that does not exist yet is a cheap laugh and a clear target.
3. Teach the plaintext-password bug **as a bug**. Delete `create()`, register, then run the `shell -c` in 3.3 and let them see `'lab-passphrase-2026'` sitting in the column. Nobody forgets `create_user()` after watching that.
4. Register with `"password"` and then with `"asha1234"`. The first is rejected, the second is not. Ask why, then explain that field validators never see the user object. This is the highest-value ninety seconds in the day.
5. Paste a real access token into <https://jwt.io> on the projector. Change one character of the payload and watch the signature go red.
6. Run 6.4 twice in a row without pausing. The second `401` is the whole point of rotation, and it needs to be felt rather than described.
7. End Part 6 with the "logged out but `/accounts/me/` still returns 200" moment. Do not soften it — the honest limit of stateless auth is more useful than the marketing version.
8. Part 7 works backwards: show the wrong `$ref: Login` on the login response, ask why spectacular guessed that, *then* add `responses=`.

**Things that reliably confuse the room**

| Confusion | Say this |
| --- | --- |
| "Is the token encrypted?" | No. It is signed. Everyone can read it; nobody can forge it. |
| "Where is the token stored on the server?" | Nowhere. That is the entire trade. |
| "Then how does logout work?" | It half-works. The refresh token is blacklisted; the access token dies of old age. |
| "Why two tokens?" | One travels constantly and expires fast; the other moves rarely and lives longer. |
| "401 or 403?" | 401 = I do not know who you are. 403 = I know, and you still may not. |
| "Why does my second refresh fail?" | Rotation. You spent the token. Store the new one every time. |
| "Serializer or form?" | Forms for HTML pages, serializers for APIs. Same job, different wire format. |
| "Why is `LoginResponseSerializer` never imported by the views?" | It is, in 7.4 — for documentation only. It never touches a request. |
| "Do I commit `schema.yml`?" | No. It is generated. Commit the code that generates it. |
| "Do I commit `requirements.txt` after `pip freeze`?" | Yes, every single time you install anything. |

**The one to check before they leave** — `requirements.txt` was re-frozen with `>` and not `>>`. A branch with `accounts/` and no `djangorestframework` pin cannot be installed by anyone, and the duplicate-`sqlparse` version of the file is the tell that somebody appended.

**Second thing to check** — that `accounts/` is actually staged. `git add config` misses the whole app, and the branch then fails for every reviewer with `No module named 'accounts'`. Part 9.1 catches it; make them run the clone.

**Time budget** — Part 1 about 25 minutes (do not rush the two-token discussion), Part 2 about 30, Parts 3–4 about 60, Part 5 about 15, Part 6 about 50, Part 7 about 40, Part 8 about 15. Roughly four hours with questions. If the day runs short, Part 8 is homework — but Part 6.4 and 6.5 are not cuttable; they are the day.

**Carrying into Day 5** — the natural next steps are putting the `Author` API from the Day 3 guide behind these tokens (`IsAuthenticatedOrReadOnly` on a viewset makes the permission classes concrete rather than theoretical), then `APITestCase` so the flow in Part 6 becomes tests instead of a `curl` transcript, then a custom user model — which is worth showing early, because it cannot be changed after the first migration ships.

**Exercises, if the room is ahead**

1. Move `validate_password` from the field into `RegisterSerializer.validate()` and pass the user attributes, so `"asha1234"` is rejected too.
2. Give `RegisterView` a `throttle_classes` so registration cannot be scripted.
3. Add `email` to the token claims, then explain to the room why that is a bad idea.
4. Make `/accounts/me/` accept `PATCH` so a user can change their own email — and only their own.
