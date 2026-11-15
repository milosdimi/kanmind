"""Tests for the task endpoints."""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from kanban_app.models import Board, Task


class TaskTestBase(APITestCase):
    """Shared data: an owner, a member, an outsider, a board and a task."""

    def setUp(self):
        """Create users, a board with one member and one task."""
        self.owner = self.create_user("owner@mail.de")
        self.member = self.create_user("member@mail.de")
        self.outsider = self.create_user("out@mail.de")
        self.board = Board.objects.create(title="Projekt X", owner=self.owner)
        self.board.members.add(self.member)
        self.task = Task.objects.create(
            board=self.board, title="Task", status="to-do",
            priority="medium", due_date="2026-12-01", created_by=self.owner,
            assignee=self.member, reviewer=self.owner,
        )

    def create_user(self, email):
        """Create a user whose username is the email."""
        return User.objects.create_user(
            username=email, email=email, password="pw", first_name="Test"
        )

    def task_data(self, **changes):
        """Return valid data for a new task, with optional changes."""
        data = {
            "board": self.board.id, "title": "Neuer Task",
            "description": "Beschreibung", "status": "review",
            "priority": "high", "assignee_id": self.member.id,
            "reviewer_id": self.owner.id, "due_date": "2026-12-24",
        }
        data.update(changes)
        return data


class CreateTaskTests(TaskTestBase):
    """POST /api/tasks/"""

    def post_task(self, user, **changes):
        """Log in as the user and send a new task."""
        self.client.force_authenticate(user=user)
        data = self.task_data(**changes)
        return self.client.post(reverse("task-list"), data, format="json")

    def test_member_can_create_task(self):
        """A member creates a task: 201 with user objects and creator."""
        response = self.post_task(self.member)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["board"], self.board.id)
        self.assertEqual(response.data["assignee"]["id"], self.member.id)
        self.assertEqual(response.data["comments_count"], 0)
        task = Task.objects.get(id=response.data["id"])
        self.assertEqual(task.created_by, self.member)

    def test_create_task_without_assignee_and_reviewer(self):
        """Assignee and reviewer are optional and stay empty."""
        response = self.post_task(
            self.member, assignee_id=None, reviewer_id=None
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["assignee"])

    def test_create_task_as_outsider_returns_403(self):
        """Only board members may create tasks."""
        response = self.post_task(self.outsider)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_task_on_unknown_board_returns_404(self):
        """A board id that does not exist returns 404."""
        response = self.post_task(self.member, board=999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_task_without_board_returns_400(self):
        """A missing or invalid board id returns 400."""
        response = self.post_task(self.member, board=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.post_task(self.member, board="abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_with_invalid_status_returns_400(self):
        """Only the documented status values are allowed."""
        response = self.post_task(self.member, status="falsch")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assignee_must_be_board_member(self):
        """An assignee outside the board returns 400."""
        response = self.post_task(self.member, assignee_id=self.outsider.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assignee_id", response.data)

    def test_create_task_without_token_returns_401(self):
        """Without login no task can be created."""
        data = self.task_data()
        response = self.client.post(reverse("task-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UpdateTaskTests(TaskTestBase):
    """PATCH /api/tasks/{task_id}/"""

    def patch_task(self, user, data, task_id=None):
        """Log in as the user and send a PATCH for the task."""
        self.client.force_authenticate(user=user)
        url = reverse("task-detail", args=[task_id or self.task.id])
        return self.client.patch(url, data, format="json")

    def test_member_can_update_task(self):
        """PATCH returns 200 without board and comments_count."""
        response = self.patch_task(self.member, {"status": "done"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "done")
        self.assertNotIn("board", response.data)
        self.assertNotIn("comments_count", response.data)

    def test_update_with_same_board_is_allowed(self):
        """Sending the current board id (like the frontend) is fine."""
        data = {"board": self.board.id, "assignee_id": None}
        response = self.patch_task(self.member, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["assignee"])

    def test_changing_the_board_returns_400(self):
        """A task can not be moved to another board."""
        other = Board.objects.create(title="Anderes", owner=self.owner)
        response = self.patch_task(self.owner, {"board": other.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_as_outsider_returns_403(self):
        """Only board members may update tasks."""
        response = self.patch_task(self.outsider, {"title": "Hack"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_unknown_task_returns_404(self):
        """A task id that does not exist returns 404."""
        response = self.patch_task(self.member, {"title": "X"}, task_id=999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DeleteTaskTests(TaskTestBase):
    """DELETE /api/tasks/{task_id}/"""

    def delete_task(self, user):
        """Log in as the user and delete the task."""
        self.client.force_authenticate(user=user)
        url = reverse("task-detail", args=[self.task.id])
        return self.client.delete(url)

    def test_board_owner_can_delete_task(self):
        """The board owner (here also the creator) can delete the task."""
        response = self.delete_task(self.owner)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.exists())

    def test_creator_can_delete_own_task(self):
        """A member who created the task can delete it."""
        self.task.created_by = self.member
        self.task.save()
        response = self.delete_task(self.member)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_member_who_is_not_creator_returns_403(self):
        """A member who did not create the task can not delete it."""
        response = self.delete_task(self.member)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Task.objects.exists())


class TaskListTests(TaskTestBase):
    """GET /api/tasks/assigned-to-me/ and /api/tasks/reviewing/"""

    def test_assigned_to_me_lists_tasks_of_assignee(self):
        """The assignee sees the task in assigned-to-me."""
        self.client.force_authenticate(user=self.member)
        response = self.client.get(reverse("tasks-assigned-to-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], self.task.id)
        self.assertEqual(response.data[0]["board"], self.board.id)

    def test_reviewing_lists_tasks_of_reviewer(self):
        """The reviewer sees the task in reviewing, not in assigned."""
        self.client.force_authenticate(user=self.owner)
        reviewing = self.client.get(reverse("tasks-reviewing"))
        assigned = self.client.get(reverse("tasks-assigned-to-me"))
        self.assertEqual(reviewing.data[0]["id"], self.task.id)
        self.assertEqual(assigned.data, [])

    def test_task_lists_without_token_return_401(self):
        """Both lists need a login."""
        for name in ["tasks-assigned-to-me", "tasks-reviewing"]:
            response = self.client.get(reverse(name))
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED
            )
