"""API views for boards, the email check and tasks."""
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import UserSerializer
from kanban_app.models import Board, Task
from .permissions import (
    IsBoardOwner,
    IsBoardOwnerOrMember,
    IsTaskCreatorOrBoardOwner,
)
from .serializers import (
    BoardDetailSerializer,
    BoardListSerializer,
    BoardUpdateSerializer,
    EmailQuerySerializer,
    TaskSerializer,
    TaskUpdateSerializer,
)


class BoardViewSet(viewsets.ModelViewSet):
    """List, create, show, update and delete boards.

    The list only contains boards the user owns or is a member of.
    Single boards are looked up in all boards, so a missing board
    gives 404 and a board without access gives 403.
    """

    queryset = Board.objects.all()
    serializer_class = BoardListSerializer
    permission_classes = [IsAuthenticated & IsBoardOwnerOrMember]
    http_method_names = ["get", "post", "patch", "delete", "options"]

    def get_queryset(self):
        """Limit the list to the boards of the current user."""
        if self.action != "list":
            return super().get_queryset()
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()

    def get_serializer_class(self):
        """Use a different serializer for detail and update."""
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action == "partial_update":
            return BoardUpdateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """Only the owner may delete a board."""
        if self.action == "destroy":
            return [IsAuthenticated(), IsBoardOwner()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Save the current user as owner of the new board."""
        serializer.save(owner=self.request.user)


class EmailCheckView(APIView):
    """GET /api/email-check/?email=... - find a user by email."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the user with this email or 404."""
        query = EmailQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        email = query.validated_data["email"]
        user = get_object_or_404(User, email__iexact=email)
        return Response(UserSerializer(user).data)


def get_board_from_request(request):
    """Return the board named in the request body.

    A missing or non-numeric id gives 400, an unknown id gives 404.
    """
    board_id = request.data.get("board")
    try:
        board_id = int(board_id)
    except (TypeError, ValueError):
        raise ValidationError({"board": ["A valid board id is required."]})
    return get_object_or_404(Board, pk=board_id)


class TaskViewSet(viewsets.ModelViewSet):
    """Create, update and delete tasks.

    Only members of the board may create or update its tasks.
    Only the creator of a task or the board owner may delete it.
    """

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated & IsBoardOwnerOrMember]
    http_method_names = ["post", "patch", "delete", "options"]

    def get_serializer_class(self):
        """Use the update serializer for PATCH."""
        if self.action == "partial_update":
            return TaskUpdateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """Only the creator or the board owner may delete a task."""
        if self.action == "destroy":
            return [IsAuthenticated(), IsTaskCreatorOrBoardOwner()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """Check the board first: 404 if missing, 403 if not a member."""
        board = get_board_from_request(request)
        self.check_object_permissions(request, board)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """Save the current user as creator of the task."""
        serializer.save(created_by=self.request.user)


class AssignedTasksView(generics.ListAPIView):
    """GET /api/tasks/assigned-to-me/ - tasks the user has to work on."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only tasks where the user is the assignee."""
        return super().get_queryset().filter(assignee=self.request.user)


class ReviewingTasksView(generics.ListAPIView):
    """GET /api/tasks/reviewing/ - tasks the user has to review."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only tasks where the user is the reviewer."""
        return super().get_queryset().filter(reviewer=self.request.user)
