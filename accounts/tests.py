from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase


class LoginAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='raja3',
            password='apexnum0118',
        )

    def test_login_returns_tokens_without_csrf_cookie(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'raja3', 'password': 'apexnum0118'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
