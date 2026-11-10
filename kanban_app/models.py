"""Data models of the kanban app: boards, tasks and comments."""
from django.contrib.auth.models import User
from django.db import models


class Board(models.Model):
    """A kanban board with an owner and a list of members."""

    title = models.CharField(max_length=63)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_boards"
    )
    members = models.ManyToManyField(
        User, related_name="member_boards", blank=True
    )

    class Meta:
        verbose_name = "Board"
        verbose_name_plural = "Boards"
        ordering = ["id"]

    def __str__(self):
        return self.title


class Task(models.Model):
    """A task inside a board with status, priority, assignee and reviewer."""

    STATUS_CHOICES = [
        ("to-do", "To do"),
        ("in-progress", "In progress"),
        ("review", "Review"),
        ("done", "Done"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    board = models.ForeignKey(
        Board, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_tasks",
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewing_tasks",
    )
    due_date = models.DateField()
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_tasks"
    )

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["id"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    """A comment written by a user on a task."""

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} on {self.task}"
