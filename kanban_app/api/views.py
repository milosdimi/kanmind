"""API views for boards and the email check."""
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import UserSerializer
from kanban_app.models import Board
from .permissions import IsBoardOwner, IsBoardOwnerOrMember
from .serializers import (
    BoardDetailSerializer,
    BoardListSerializer,
    BoardUpdateSerializer,
    EmailQuerySerializer,
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
