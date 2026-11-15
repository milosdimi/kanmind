"""Tests for the board endpoints."""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from kanban_app.models import Board


class BoardTests(APITestCase):
    """Tests for /api/boards/"""

    def setUp(self):
        """Create an owner, a member and a board."""
        self.owner = User.objects.create_user(
            username="owner@mail.de", email="owner@mail.de", password="pw"
        )
        self.member = User.objects.create_user(
            username="member@mail.de", email="member@mail.de", password="pw"
        )
        self.board = Board.objects.create(title="Projekt X", owner=self.owner)
        self.board.members.add(self.member)

    def test_list_boards_without_token_fails(self):
        """Without login the list returns 401."""
        url = reverse("board-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_board_returns_201(self):
        """A logged in user can create a board."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("board-list")
        data = {"title": "Neues Board", "members": [self.member.id]}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner_id"], self.owner.id)
