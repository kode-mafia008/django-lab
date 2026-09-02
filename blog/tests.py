from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Author


class AuthorAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )

    def test_get_authors_without_login(self):
        response = self.client.get("/api/authors/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_author_without_login(self):
        response = self.client.post(
            "/api/authors/",
            {
                "name": "Anonymous Author",
                "email": "anonymous@example.com"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_create_author_with_login(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/authors/",
            {
                "name": "Test Author",
                "email": "test@example.com"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(Author.objects.count(), 1)