"""Small helpers shared by permissions and serializers."""
from kanban_app.models import Board, Task


def get_board(obj):
    """Return the board a board, task or comment belongs to."""
    if isinstance(obj, Board):
        return obj
    if isinstance(obj, Task):
        return obj.board
    return obj.task.board


def is_board_member(board, user):
    """Check if the user is the owner or a member of the board."""
    if board.owner_id == user.id:
        return True
    return board.members.filter(id=user.id).exists()
