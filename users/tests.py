from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from .models import UserProfile


class UserProfileTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="profileuser",
            password="testpass123",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            bio="Test bio",
            phone="9800000000",
        )

    def test_profile_requires_authentication(self):
        response = self.client.get("/api/profile/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_get_profile_when_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bio"], "Test bio")
        self.assertEqual(response.data["phone"], "9800000000")
        
    def test_update_profile_when_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            "/api/profile/",
            {
                "bio": "Updated bio",
                "phone": "9811111111",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(response.data["bio"], "Updated bio")
        self.assertEqual(response.data["phone"], "9811111111")   