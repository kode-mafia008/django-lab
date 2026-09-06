"""Day 10 — the security rules, written down as assertions.

A permission is a claim about what the app refuses to do. A claim nobody
tests is a comment. Each test here names one refusal:

* an anonymous caller cannot read the API at all;
* an authenticated caller cannot write somebody else's row;
* nobody can see somebody else's draft;
* the server, not the client, decides who owns a new row;
* the HTML pages enforce the same rules as the API, separately;
* `check --deploy` passes with the production environment set.
"""

import os
import subprocess
import sys

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management.utils import get_random_secret_key
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from blog.models import Author, Blog


class OwnershipAPITests(APITestCase):
    """Authentication says who you are. It never says what you may touch."""

    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen")
        cls.asha = User.objects.create_user("asha", password="lab-passphrase-2026")
        cls.bello = User.objects.create_user("bello", password="lab-passphrase-2026")

        cls.asha_post = Blog.objects.create(
            title="Asha public post",
            content="x",
            author=cls.austen,
            owner=cls.asha,
            published=True,
        )
        cls.asha_draft = Blog.objects.create(
            title="Asha secret draft", content="x", author=cls.austen, owner=cls.asha
        )
        # Written before ownership existed. Nobody owns it, so nobody may
        # change it — the check fails closed.
        cls.orphan = Blog.objects.create(
            title="An orphan post", content="x", author=cls.austen, published=True
        )

    def setUp(self):
        cache.clear()

    def test_anonymous_gets_401_not_a_row(self):
        self.assertEqual(
            self.client.get(reverse("api:blog-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

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

    def test_the_owner_still_can(self):
        self.client.force_authenticate(user=self.asha)
        url = reverse("api:blog-detail", args=[self.asha_post.pk])
        self.assertEqual(
            self.client.patch(url, {"title": "Retitled by its owner"}).status_code,
            status.HTTP_200_OK,
        )

    def test_an_unowned_row_is_read_only_for_everyone(self):
        url = reverse("api:blog-detail", args=[self.orphan.pk])
        for user in [self.asha, self.bello]:
            with self.subTest(user=user.username):
                self.client.force_authenticate(user=user)
                self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
                self.assertEqual(
                    self.client.patch(url, {"title": "Claimed"}).status_code,
                    status.HTTP_403_FORBIDDEN,
                )

    def test_someone_elses_draft_is_a_404_not_a_403(self):
        """A 403 confirms the row exists. A queryset that excludes it does not."""
        self.client.force_authenticate(user=self.bello)
        response = self.client.get(reverse("api:blog-detail", args=[self.asha_draft.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_the_list_hides_other_peoples_drafts(self):
        self.client.force_authenticate(user=self.bello)
        titles = [row["title"] for row in self.client.get(reverse("api:blog-list")).data["results"]]
        self.assertIn("Asha public post", titles)
        self.assertNotIn("Asha secret draft", titles)

    def test_you_can_see_your_own_drafts(self):
        self.client.force_authenticate(user=self.asha)
        titles = [row["title"] for row in self.client.get(reverse("api:blog-list")).data["results"]]
        self.assertIn("Asha secret draft", titles)

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

    def test_an_unowned_row_still_reports_an_owner_key(self):
        """A response shape that changes per row is a bug waiting to happen."""
        self.client.force_authenticate(user=self.asha)
        response = self.client.get(reverse("api:blog-detail", args=[self.orphan.pk]))
        self.assertIn("owner", response.data)
        self.assertIsNone(response.data["owner"])

    def test_the_list_is_paginated(self):
        """An unbounded list endpoint is a denial-of-service tool you shipped."""
        self.client.force_authenticate(user=self.asha)
        response = self.client.get(reverse("api:blog-list"))
        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})
        self.assertLessEqual(len(response.data["results"]), settings.REST_FRAMEWORK["PAGE_SIZE"])


class ThrottleTests(APITestCase):
    """Rate limits, proved by tripping them."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("asha", password="lab-passphrase-2026")

    def setUp(self):
        cache.clear()

    def test_the_sixth_login_attempt_in_a_minute_is_refused(self):
        url = reverse("login")
        body = {"username": "asha", "password": "wrong-guess"}

        for attempt in range(5):
            with self.subTest(attempt=attempt):
                self.assertEqual(
                    self.client.post(url, body).status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

        blocked = self.client.post(url, body)
        self.assertEqual(blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        # The correct password does not help — the throttle runs before the
        # view, so it never gets as far as checking credentials.
        correct = self.client.post(url, {"username": "asha", "password": "lab-passphrase-2026"})
        self.assertEqual(correct.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_a_throttled_response_says_when_to_come_back(self):
        url = reverse("login")
        for _ in range(6):
            response = self.client.post(url, {"username": "asha", "password": "no"})
        self.assertIn("Retry-After", response.headers)
        self.assertIn("throttled", str(response.data["detail"]).lower())

    def test_registration_is_throttled_too(self):
        url = reverse("register")
        for i in range(5):
            self.client.post(url, {"username": f"bot{i}", "password": "lab-passphrase-2026"})
        blocked = self.client.post(url, {"username": "bot99", "password": "lab-passphrase-2026"})
        self.assertEqual(blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(User.objects.filter(username="bot99").exists())


class HTMLPageSecurityTests(TestCase):
    """The API's permission classes protect the API and nothing else."""

    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen")
        cls.asha = User.objects.create_user("asha", password="lab-passphrase-2026")
        cls.bello = User.objects.create_user("bello", password="lab-passphrase-2026")
        cls.post = Blog.objects.create(
            title="Asha public post",
            content="x",
            author=cls.austen,
            owner=cls.asha,
            published=True,
        )
        cls.draft = Blog.objects.create(
            title="Asha secret draft", content="x", author=cls.austen, owner=cls.asha
        )

    def setUp(self):
        # `blog_detail` is rate-limited, and the counter is in the cache, which
        # `TestCase` does not roll back.
        cache.clear()

    def test_anonymous_is_redirected_away_from_every_write_page(self):
        pages = [
            reverse("blog:post-create"),
            reverse("blog:post-update", args=[self.post.pk]),
            reverse("blog:post-delete", args=[self.post.pk]),
        ]
        for url in pages:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], f"{settings.LOGIN_URL}?next={url}")

    def test_anonymous_cannot_post_a_new_row_either(self):
        """A redirect on GET is cosmetic if POST still writes."""
        self.client.post(reverse("blog:post-create"), {
            "title": "Written by nobody", "author": self.austen.pk, "content": "x",
        })
        self.assertFalse(Blog.objects.filter(title="Written by nobody").exists())

    def test_a_logged_in_stranger_gets_403_on_your_post(self):
        self.client.force_login(self.bello)
        for name in ["blog:post-update", "blog:post-delete"]:
            with self.subTest(name=name):
                url = reverse(name, args=[self.post.pk])
                self.assertEqual(self.client.get(url).status_code, 403)
                self.client.post(url, {
                    "title": "Defaced by bello", "author": self.austen.pk, "content": "x",
                })
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Asha public post")
        self.assertTrue(Blog.objects.filter(pk=self.post.pk).exists())

    def test_the_create_page_stamps_the_logged_in_user_as_owner(self):
        self.client.force_login(self.bello)
        self.client.post(reverse("blog:post-create"), {
            "title": "Written by bello", "author": self.austen.pk, "content": "x",
        })
        self.assertEqual(Blog.objects.get(title="Written by bello").owner, self.bello)

    def test_drafts_are_invisible_to_everyone_but_their_owner(self):
        detail = reverse("blog:post-detail", args=[self.draft.pk])
        listing = reverse("blog:post-list")

        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertNotContains(self.client.get(listing), "Asha secret draft")

        self.client.force_login(self.bello)
        self.assertEqual(self.client.get(detail).status_code, 404)

        self.client.force_login(self.asha)
        self.assertEqual(self.client.get(detail).status_code, 200)
        self.assertContains(self.client.get(listing), "Asha secret draft")

    def test_the_page_offers_no_button_it_would_refuse(self):
        """Hiding the link is not the control. It is the courtesy."""
        self.client.force_login(self.bello)
        body = self.client.get(reverse("blog:post-detail", args=[self.post.pk])).content.decode()
        self.assertNotIn(reverse("blog:post-update", args=[self.post.pk]), body)
        self.assertNotIn(reverse("blog:post-delete", args=[self.post.pk]), body)

    def test_an_anonymous_visitor_is_offered_a_login_not_a_new_post_link(self):
        body = self.client.get(reverse("blog:post-list")).content.decode()
        self.assertNotIn(reverse("blog:post-create"), body)
        self.assertIn(reverse("admin:login"), body)


@override_settings(PAGE_THROTTLE_RATES={"blog-detail": "3/min"})
class PageRateLimitTests(TestCase):
    """The HTML pages are not covered by DRF's throttles, so they carry their own.

    The rate is overridden to 3/min here rather than tripped 31 times: the
    decorator reads `settings.PAGE_THROTTLE_RATES`, so overriding it also
    proves the setting is the thing in charge.
    """

    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen")
        cls.asha = User.objects.create_user("asha", password="lab-passphrase-2026")
        cls.bello = User.objects.create_user("bello", password="lab-passphrase-2026")
        cls.post = Blog.objects.create(
            title="Asha public post",
            content="x",
            author=cls.austen,
            owner=cls.asha,
            published=True,
        )

    def setUp(self):
        cache.clear()

    def detail(self):
        return self.client.get(reverse("blog:post-detail", args=[self.post.pk]))

    def test_the_fourth_view_in_a_minute_is_refused(self):
        for view_number in range(3):
            with self.subTest(view_number=view_number):
                self.assertEqual(self.detail().status_code, 200)

        blocked = self.detail()
        self.assertEqual(blocked.status_code, 429)
        self.assertContains(blocked, "Too many requests", status_code=429)

    def test_a_throttled_response_says_when_to_come_back(self):
        for _ in range(4):
            response = self.detail()
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)
        self.assertTrue(1 <= int(response.headers["Retry-After"]) <= 60)

    def test_the_counter_is_per_caller_not_global(self):
        """One user reading a lot must not lock everybody else out."""
        self.client.force_login(self.asha)
        for _ in range(4):
            self.detail()
        self.assertEqual(self.detail().status_code, 429)

        self.client.force_login(self.bello)
        self.assertEqual(self.detail().status_code, 200)

    def test_signing_in_starts_a_separate_counter_from_the_anonymous_one(self):
        for _ in range(4):
            self.detail()
        self.assertEqual(self.detail().status_code, 429)

        self.client.force_login(self.asha)
        self.assertEqual(self.detail().status_code, 200)

    def test_only_the_scoped_view_is_limited(self):
        for _ in range(4):
            self.detail()
        self.assertEqual(self.detail().status_code, 429)
        # The list page shares no counter with the detail page.
        self.assertEqual(self.client.get(reverse("blog:post-list")).status_code, 200)

    def test_the_limit_is_read_from_settings_not_hardcoded(self):
        with override_settings(PAGE_THROTTLE_RATES={"blog-detail": "1/min"}):
            cache.clear()
            self.assertEqual(self.detail().status_code, 200)
            self.assertEqual(self.detail().status_code, 429)


class RateParsingTests(TestCase):
    def test_every_period_spelling_drf_accepts(self):
        from blog.throttling import parse_rate

        cases = {
            "5/s": (5, 1), "5/sec": (5, 1), "5/second": (5, 1),
            "30/m": (30, 60), "30/min": (30, 60), "30/minute": (30, 60),
            "100/h": (100, 3600), "100/hour": (100, 3600),
            "1000/d": (1000, 86400), "1000/day": (1000, 86400),
        }
        for rate, expected in cases.items():
            with self.subTest(rate=rate):
                self.assertEqual(parse_rate(rate), expected)


class SettingsTests(TestCase):
    """The settings that are security decisions, not preferences."""

    def test_the_api_is_closed_by_default(self):
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"],
            ["rest_framework.permissions.IsAuthenticated"],
        )

    def test_refresh_tokens_rotate_and_the_old_one_is_blacklisted(self):
        self.assertTrue(settings.SIMPLE_JWT["ROTATE_REFRESH_TOKENS"])
        self.assertTrue(settings.SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"])
        self.assertIn("rest_framework_simplejwt.token_blacklist", settings.INSTALLED_APPS)

    def test_access_tokens_are_short_lived(self):
        self.assertLessEqual(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(), 30 * 60)

    def test_the_secret_key_is_not_written_in_the_settings_file(self):
        source = (settings.BASE_DIR / "config" / "settings.py").read_text()
        self.assertNotIn(settings.SECRET_KEY, source.replace("dev-only-never-deploy-this-key", ""))
        self.assertIn("DJANGO_SECRET_KEY", source)


class DeploymentChecklistTests(TestCase):
    """`check --deploy` is Django's own list of what a server needs.

    Run in a subprocess with a production environment, because the `if not
    DEBUG:` block in settings.py is evaluated once, at import.
    """

    def test_check_deploy_is_clean_with_the_production_environment(self):
        env = {
            **os.environ,
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": get_random_secret_key(),
            "DJANGO_ALLOWED_HOSTS": "example.com",
        }
        result = subprocess.run(
            [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_missing_secret_key_refuses_to_start_in_production(self):
        env = {**os.environ, "DJANGO_DEBUG": "0", "DJANGO_SECRET_KEY": ""}
        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=settings.BASE_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be set", result.stderr)
