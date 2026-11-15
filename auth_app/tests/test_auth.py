"""Tests for the registration and login endpoints."""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class RegistrationTests(APITestCase):
    """POST /api/registration/"""

    def setUp(self):
        """Prepare the URL and valid sign up data."""
        self.url = reverse("registration")
        self.data = {
            "fullname": "Max Mustermann",
            "email": "max@mail.de",
            "password": "secret123",
            "repeated_password": "secret123",
        }

    def test_register_returns_token_and_user_data(self):
        """Valid data creates a user and returns 201 with a token."""
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="max@mail.de")
        self.assertEqual(response.data, {
            "token": Token.objects.get(user=user).key,
            "fullname": "Max Mustermann",
            "email": "max@mail.de",
            "user_id": user.id,
        })

    def test_register_splits_fullname(self):
        """The full name is stored as first and last name."""
        self.data["fullname"] = "Anna Maria Muster"
        self.client.post(self.url, self.data, format="json")
        user = User.objects.get(email="max@mail.de")
        self.assertEqual(user.first_name, "Anna")
        self.assertEqual(user.last_name, "Maria Muster")

    def test_register_with_existing_email_fails(self):
        """An email can only be registered once (case insensitive)."""
        self.client.post(self.url, self.data, format="json")
        self.data["email"] = "MAX@mail.de"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_with_different_passwords_fails(self):
        """Both passwords must be identical."""
        self.data["repeated_password"] = "other123"
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("repeated_password", response.data)

    def test_register_with_missing_fields_fails(self):
        """An empty request returns 400 and creates no user."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.exists())


class LoginTests(APITestCase):
    """POST /api/login/"""

    def setUp(self):
        """Create a user who can log in."""
        self.url = reverse("login")
        self.user = User.objects.create_user(
            username="max@mail.de", email="max@mail.de",
            password="secret123", first_name="Max", last_name="Mustermann",
        )

    def test_login_returns_token_and_user_data(self):
        """Correct credentials return 200 with token and user data."""
        data = {"email": "max@mail.de", "password": "secret123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], self.user.id)
        self.assertEqual(response.data["fullname"], "Max Mustermann")
        self.assertEqual(
            response.data["token"], Token.objects.get(user=self.user).key
        )

    def test_login_with_wrong_password_fails(self):
        """A wrong password returns 400."""
        data = {"email": "max@mail.de", "password": "wrong"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_unknown_email_fails(self):
        """An unknown email returns 400."""
        data = {"email": "nobody@mail.de", "password": "secret123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_ignores_invalid_token(self):
        """An outdated token in the header must not block the login."""
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid")
        data = {"email": "max@mail.de", "password": "secret123"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
