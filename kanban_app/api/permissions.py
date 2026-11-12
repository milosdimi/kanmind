"""Object permissions for boards, tasks and comments."""
from rest_framework.permissions import BasePermission

from .utils import get_board, is_board_member


class IsBoardOwnerOrMember(BasePermission):
    """Allow access only to the owner or a member of the related board.

    Works for boards, tasks and comments: the board is looked up first.
    """

    message = "You must be the owner or a member of this board."

    def has_object_permission(self, request, view, obj):
        """Check if the user owns the board or is one of its members."""
        return is_board_member(get_board(obj), request.user)


class IsBoardOwner(BasePermission):
    """Allow access only to the owner of the board."""

    message = "Only the owner of this board can do this."

    def has_object_permission(self, request, view, obj):
        """Check if the user owns the board."""
        return obj.owner_id == request.user.id


class IsTaskCreatorOrBoardOwner(BasePermission):
    """Allow access only to the creator of the task or the board owner."""

    message = "Only the creator of the task or the board owner can do this."

    def has_object_permission(self, request, view, obj):
        """Check if the user created the task or owns its board."""
        user_id = request.user.id
        return obj.created_by_id == user_id or obj.board.owner_id == user_id


class IsCommentAuthor(BasePermission):
    """Allow access only to the author of the comment."""

    message = "Only the author of this comment can delete it."

    def has_object_permission(self, request, view, obj):
        """Check if the user wrote the comment."""
        return obj.author_id == request.user.id
