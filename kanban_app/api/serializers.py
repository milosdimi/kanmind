"""Serializers for boards, tasks and comments."""
from django.contrib.auth.models import User
from rest_framework import serializers

from auth_app.api.serializers import UserSerializer
from kanban_app.models import Board, Task


class EmailQuerySerializer(serializers.Serializer):
    """Validates the email query parameter of the email check."""

    email = serializers.EmailField()


class BoardTaskSerializer(serializers.ModelSerializer):
    """Task as shown inside the board detail view."""

    assignee = UserSerializer(read_only=True)
    reviewer = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "status", "priority",
            "assignee", "reviewer", "due_date", "comments_count",
        ]

    def get_comments_count(self, obj):
        """Return the number of comments of the task."""
        return obj.comments.count()


class BoardListSerializer(serializers.ModelSerializer):
    """Board overview with counters; also used to create a board."""

    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(),
        write_only=True, required=False,
    )
    owner_id = serializers.ReadOnlyField()
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = [
            "id", "title", "members", "member_count", "ticket_count",
            "tasks_to_do_count", "tasks_high_prio_count", "owner_id",
        ]

    def get_member_count(self, obj):
        """Return the number of board members."""
        return obj.members.count()

    def get_ticket_count(self, obj):
        """Return the number of tasks on the board."""
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        """Return the number of tasks with status 'to-do'."""
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        """Return the number of tasks with priority 'high'."""
        return obj.tasks.filter(priority="high").count()


class BoardDetailSerializer(serializers.ModelSerializer):
    """Single board with its members and tasks."""

    owner_id = serializers.ReadOnlyField()
    members = UserSerializer(many=True, read_only=True)
    tasks = BoardTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """Changes title and members; answers with owner and member data."""

    members = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), write_only=True
    )
    owner_data = UserSerializer(source="owner", read_only=True)
    members_data = UserSerializer(
        source="members", many=True, read_only=True
    )

    class Meta:
        model = Board
        fields = ["id", "title", "members", "owner_data", "members_data"]
