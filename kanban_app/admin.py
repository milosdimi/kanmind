"""Admin configuration for boards, tasks and comments."""
from django.contrib import admin

from .models import Board, Comment, Task


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    """Admin view for boards."""

    list_display = ["id", "title", "owner"]
    search_fields = ["title"]
    filter_horizontal = ["members"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin view for tasks."""

    list_display = ["id", "title", "board", "status", "priority", "due_date"]
    list_filter = ["status", "priority"]
    search_fields = ["title", "description"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin view for comments."""

    list_display = ["id", "task", "author", "created_at"]
    search_fields = ["content"]
