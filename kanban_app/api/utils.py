"""Small helpers shared by permissions and serializers."""
from kanban_app.models import Board


def get_board(obj):
    """Return the board itself or the board a task belongs to."""
    if isinstance(obj, Board):
        return obj
    return obj.board


def is_board_member(board, user):
    """Check if the user is the owner or a member of the board."""
    if board.owner_id == user.id:
        return True
    return board.members.filter(id=user.id).exists()
