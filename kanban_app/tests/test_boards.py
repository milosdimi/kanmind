"""Tests for the board endpoints."""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from kanban_app.models import Board, Task


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

    def test_get_unknown_board_returns_404(self):
        """A board that does not exist returns 404."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("board-detail", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_board_as_member_returns_200(self):
        """A member of the board can see it."""
        self.client.force_authenticate(user=self.member)
        url = reverse("board-detail", args=[self.board.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_board_as_non_owner_returns_403(self):
        """A member who is not the owner cannot delete the board."""
        self.client.force_authenticate(user=self.member)
        url = reverse("board-detail", args=[self.board.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_shows_only_own_boards(self):
        """The list contains boards the user owns or is a member of."""
        outsider = User.objects.create_user(username="out", password="pw")
        Board.objects.create(title="Fremdes Board", owner=outsider)
        self.client.force_authenticate(user=self.member)
        response = self.client.get(reverse("board-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Projekt X")

    def test_list_counts_members_and_tasks(self):
        """The list shows the member, task, to-do and high prio counters."""
        Task.objects.create(
            board=self.board, title="T", status="to-do", priority="high",
            due_date="2026-12-01", created_by=self.owner,
        )
        self.client.force_authenticate(user=self.owner)
        board = self.client.get(reverse("board-list")).data[0]
        self.assertEqual(board["member_count"], 1)
        self.assertEqual(board["ticket_count"], 1)
        self.assertEqual(board["tasks_to_do_count"], 1)
        self.assertEqual(board["tasks_high_prio_count"], 1)

    def test_create_board_with_unknown_member_fails(self):
        """An unknown user id in members returns 400."""
        self.client.force_authenticate(user=self.owner)
        data = {"title": "Neues Board", "members": [999]}
        response = self.client.post(reverse("board-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_board_shows_members_and_tasks(self):
        """The detail view contains owner_id, members and tasks."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("board-detail", args=[self.board.id])
        response = self.client.get(url)
        self.assertEqual(response.data["owner_id"], self.owner.id)
        self.assertEqual(response.data["members"][0]["id"], self.member.id)
        self.assertEqual(response.data["tasks"], [])

    def test_get_board_as_outsider_returns_403(self):
        """A user who is neither owner nor member gets 403."""
        outsider = User.objects.create_user(username="out", password="pw")
        self.client.force_authenticate(user=outsider)
        url = reverse("board-detail", args=[self.board.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_board_as_member_returns_owner_and_members(self):
        """A member can change title and members (PATCH)."""
        self.client.force_authenticate(user=self.member)
        url = reverse("board-detail", args=[self.board.id])
        data = {"title": "Neuer Titel", "members": [self.owner.id]}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Neuer Titel")
        self.assertEqual(response.data["owner_data"]["id"], self.owner.id)
        self.assertEqual(response.data["members_data"][0]["id"], self.owner.id)

    def test_put_is_not_allowed(self):
        """Only PATCH is offered for updates, PUT returns 405."""
        self.client.force_authenticate(user=self.owner)
        url = reverse("board-detail", args=[self.board.id])
        response = self.client.put(url, {"title": "X"}, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_delete_board_as_owner_deletes_tasks(self):
        """The owner can delete the board, its tasks are removed too."""
        Task.objects.create(
            board=self.board, title="T", status="to-do", priority="low",
            due_date="2026-12-01", created_by=self.owner,
        )
        self.client.force_authenticate(user=self.owner)
        url = reverse("board-detail", args=[self.board.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.exists())


class EmailCheckTests(APITestCase):
    """Tests for /api/email-check/"""

    def setUp(self):
        """Create a user to search for and log in as this user."""
        self.user = User.objects.create_user(
            username="max@mail.de", email="max@mail.de", password="pw",
            first_name="Max", last_name="Mustermann",
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("email-check")

    def test_existing_email_returns_user(self):
        """A registered email returns id, email and full name."""
        response = self.client.get(self.url, {"email": "MAX@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "id": self.user.id,
            "email": "max@mail.de",
            "fullname": "Max Mustermann",
        })

    def test_unknown_email_returns_404(self):
        """An email without user returns 404."""
        response = self.client.get(self.url, {"email": "nobody@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_or_missing_email_returns_400(self):
        """A wrong format or a missing email returns 400."""
        response = self.client.get(self.url, {"email": "keinemail"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_check_without_token_fails(self):
        """Without login the email check returns 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {"email": "max@mail.de"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
