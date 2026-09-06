"""Day 10 — what the auth endpoints must refuse.

The `accounts` app is the door. Everything else in the project trusts whatever
comes through it, so the tests here are about what must *not* happen:
passwords must not come back out, extra JSON keys must not grant staff rights,
a spent refresh token must not work twice, and a stolen access token must
expire on its own.
"""

import base64
import json

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken


class AuthTestCase(APITestCase):
    """Login and register share a 5/min throttle, so clear it between tests."""

    def setUp(self):
        super().setUp()
        cache.clear()


class RegistrationTests(AuthTestCase):
    url_name = "register"

    def test_a_password_goes_in_and_never_comes_back(self):
        response = self.client.post(reverse(self.url_name), {
            "username": "asha", "email": "asha@example.com",
            "password": "lab-passphrase-2026",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        self.assertEqual(set(response.data), {"id", "username", "email"})

    def test_the_password_is_stored_hashed(self):
        self.client.post(reverse(self.url_name), {
            "username": "asha", "password": "lab-passphrase-2026",
        })
        user = User.objects.get(username="asha")
        self.assertNotEqual(user.password, "lab-passphrase-2026")
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password("lab-passphrase-2026"))

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

    def test_a_weak_password_is_refused_here_rather_than_later(self):
        for password in ["123456", "password", "asha"]:
            with self.subTest(password=password):
                cache.clear()
                response = self.client.post(reverse(self.url_name), {
                    "username": "asha", "password": password,
                })
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("password", response.data)
        self.assertFalse(User.objects.filter(username="asha").exists())


class TokenTests(AuthTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("asha", password="lab-passphrase-2026")

    def login(self):
        response = self.client.post(reverse("login"), {
            "username": "asha", "password": "lab-passphrase-2026",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_login_returns_both_tokens_and_the_user(self):
        data = self.login()
        self.assertEqual(set(data), {"access", "refresh", "user"})
        self.assertEqual(data["user"]["username"], "asha")
        self.assertNotIn("password", data["user"])

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

    def test_a_protected_endpoint_needs_the_header(self):
        url = reverse("user-info")
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

        access = self.login()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "asha")

    def test_a_tampered_token_is_rejected(self):
        """Flip one character of the payload and the signature stops matching."""
        access = self.login()["access"]
        header, payload, signature = access.split(".")
        forged = f"{header}.{payload[:-2]}XX.{signature}"

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {forged}")
        self.assertEqual(
            self.client.get(reverse("user-info")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_an_expired_access_token_stops_working(self):
        """This is why the lifetime is 15 minutes: nothing else revokes it."""
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-token.lifetime)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(reverse("user-info"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("expired", str(response.data).lower())


class RefreshAndLogoutTests(AuthTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("asha", password="lab-passphrase-2026")

    def login(self):
        return self.client.post(reverse("login"), {
            "username": "asha", "password": "lab-passphrase-2026",
        }).data

    def test_refreshing_rotates_the_refresh_token_and_kills_the_old_one(self):
        first = self.login()["refresh"]

        rotated = self.client.post(reverse("refresh"), {"refresh": first})
        self.assertEqual(rotated.status_code, status.HTTP_200_OK)
        self.assertNotEqual(rotated.data["refresh"], first)

        replayed = self.client.post(reverse("refresh"), {"refresh": first})
        self.assertEqual(replayed.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("blacklisted", str(replayed.data).lower())

    def test_logout_blacklists_the_refresh_token(self):
        tokens = self.login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        logout = self.client.post(reverse("logout"), {"refresh": tokens["refresh"]})
        self.assertEqual(logout.status_code, status.HTTP_205_RESET_CONTENT)

        reused = self.client.post(reverse("refresh"), {"refresh": tokens["refresh"]})
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_needs_a_credential_of_its_own(self):
        tokens = self.login()
        self.assertEqual(
            self.client.post(reverse("logout"), {"refresh": tokens["refresh"]}).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_the_access_token_survives_logout_until_it_expires(self):
        """The honest limit of JWT logout, and the reason for short lifetimes."""
        tokens = self.login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.client.post(reverse("logout"), {"refresh": tokens["refresh"]})

        still_works = self.client.get(reverse("user-info"))
        self.assertEqual(still_works.status_code, status.HTTP_200_OK)
