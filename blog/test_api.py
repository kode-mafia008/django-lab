from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from blog.models import Author, Blog


class APINamespaceTests(APITestCase):
    """The API is addressed independently of the HTML pages."""

    def test_router_names_are_under_the_api_namespace(self):
        self.assertEqual(reverse("api:author-list"), "/api/authors/")
        self.assertEqual(reverse("api:author-detail", args=[1]), "/api/authors/1/")
        self.assertEqual(reverse("api:blog-list"), "/api/blogs/")
        self.assertEqual(reverse("api:blog-detail", args=[1]), "/api/blogs/1/")
        self.assertEqual(reverse("api:api-root"), "/api/")

    def test_the_old_nested_api_urls_are_gone(self):
        for url in ["/blogs/api/blogs/", "/blogs/api/", "/blogs/api/authors"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)

    def test_the_schema_routes_still_resolve_under_the_api_prefix(self):
        # `path("api/", include("blog.api_urls"))` is listed before the schema
        # routes. The router's patterns are anchored to `authors/` and `blogs/`,
        # so `api/schema/` falls through rather than being swallowed.
        for name in ["schema", "swagger-ui", "redoc"]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, status.HTTP_200_OK)

    def test_api_root_lists_both_resources(self):
        self.client.force_authenticate(user=User.objects.create_user("asha", password="x"))
        response = self.client.get(reverse("api:api-root"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"authors", "blogs"})

    def test_api_root_links_carry_the_namespace(self):
        self.client.force_authenticate(user=User.objects.create_user("asha", password="x"))
        response = self.client.get(reverse("api:api-root"))
        self.assertTrue(response.data["blogs"].endswith("/api/blogs/"))
        self.assertTrue(response.data["authors"].endswith("/api/authors/"))


class AuthorAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen", bio="Novelist.")
        cls.user = User.objects.create_user("asha", password="lab-passphrase-2026")

    def test_anonymous_is_locked_out(self):
        self.assertEqual(
            self.client.get(reverse("api:author-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authors_now_have_all_six_operations(self):
        self.client.force_authenticate(user=self.user)

        created = self.client.post(reverse("api:author-list"), {"name": "Frank Herbert"})
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        pk = created.data["id"]

        detail = reverse("api:author-detail", args=[pk])
        self.assertEqual(self.client.get(reverse("api:author-list")).status_code, 200)
        self.assertEqual(self.client.get(detail).status_code, 200)
        self.assertEqual(self.client.put(detail, {"name": "F. Herbert"}).status_code, 200)
        self.assertEqual(self.client.patch(detail, {"bio": "Wrote Dune."}).status_code, 200)
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertFalse(Author.objects.filter(pk=pk).exists())


class BlogAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.austen = Author.objects.create(name="Jane Austen")
        cls.user = User.objects.create_user("asha", password="lab-passphrase-2026")

    def test_anonymous_is_locked_out(self):
        self.assertEqual(
            self.client.get(reverse("api:blog-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_crud_round_trip(self):
        self.client.force_authenticate(user=self.user)

        created = self.client.post(reverse("api:blog-list"), {
            "title": "Written over the API",
            "content": "Body.",
            "author": self.austen.pk,
            "published": True,
        })
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["author"], self.austen.pk)

        detail = reverse("api:blog-detail", args=[created.data["id"]])
        patched = self.client.patch(detail, {"title": "Retitled over the API"})
        self.assertEqual(patched.status_code, status.HTTP_200_OK)
        self.assertEqual(Blog.objects.get().title, "Retitled over the API")

        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Blog.objects.exists())

    def test_unknown_author_is_a_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("api:blog-list"), {
            "title": "Ghost", "content": "x", "author": 9999,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("author", response.data)

    def test_the_api_and_the_html_form_write_to_the_same_table(self):
        """The split is in the URLs and the views, not in the data."""
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("api:blog-list"), {
            "title": "Made by the API", "content": "x", "author": self.austen.pk,
        })
        self.client.post(reverse("blog:post-create"), {
            "title": "Made by the form", "author": self.austen.pk, "content": "x",
        })
        self.assertEqual(Blog.objects.count(), 2)
