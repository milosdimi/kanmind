"""Object permissions for boards."""
from rest_framework.permissions import BasePermission


class IsBoardOwnerOrMember(BasePermission):
    """Allow access only to the owner or a member of the board."""

    message = "You must be the owner or a member of this board."

    def has_object_permission(self, request, view, obj):
        """Check if the user owns the board or is one of its members."""
        user = request.user
        if obj.owner_id == user.id:
            return True
        return obj.members.filter(id=user.id).exists()


class IsBoardOwner(BasePermission):
    """Allow access only to the owner of the board."""

    message = "Only the owner of this board can do this."

    def has_object_permission(self, request, view, obj):
        """Check if the user owns the board."""
        return obj.owner_id == request.user.id
