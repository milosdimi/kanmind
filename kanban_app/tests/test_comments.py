"""Tests for the comment endpoints."""
from django.urls import reverse
from rest_framework import status

from kanban_app.models import Comment
from kanban_app.tests.test_tasks import TaskTestBase


class CommentTests(TaskTestBase):
    """Tests for /api/tasks/{task_id}/comments/"""

    def test_member_can_create_comment(self):
        """A member writes a comment: 201 with the author's name."""
        self.client.force_authenticate(user=self.member)
        url = reverse("task-comments", args=[self.task.id])
        data = {"content": "Hallo"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], "Test")

    def test_member_can_list_comments(self):
        """A member gets the list of comments."""
        Comment.objects.create(
            task=self.task, author=self.member, content="Hallo"
            )
        self.client.force_authenticate(user=self.member)
        url = reverse("task-comments", args=[self.task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_empty_comment_returns_400(self):
        """An empty comment returns 400."""
        self.client.force_authenticate(user=self.member)
        url = reverse("task-comments", args=[self.task.id])
        data = {"content": ""}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comments_of_unknown_task_return_404(self):
        """A task that does not exist returns 404."""
        self.client.force_authenticate(user=self.member)
        url = reverse("task-comments", args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_can_not_read_comments(self):
        """A user who is not on the board gets 403."""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("task-comments", args=[self.task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete_comment(self):
        """The author can delete the comment."""
        comment = Comment.objects.create(
            task=self.task, author=self.member, content="Hallo"
            )
        self.client.force_authenticate(user=self.member)
        url = reverse("task-comment-detail", args=[self.task.id, comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_user_can_not_delete_comment(self):
        """Only the author can delete a comment."""
        comment = Comment.objects.create(
            task=self.task, author=self.member, content="Hallo"
            )
        self.client.force_authenticate(user=self.owner)
        url = reverse("task-comment-detail", args=[self.task.id, comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_string_representation(self):
        """Board, task and comment show a readable name."""
        comment = Comment.objects.create(
            task=self.task, author=self.member, content="Hallo"
        )
        self.assertEqual(str(self.board), "Projekt X")
        self.assertEqual(str(self.task), "Task")
        self.assertIn("Task", str(comment))
