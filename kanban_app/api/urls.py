"""URL routes of the kanban app."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    AssignedTasksView,
    BoardViewSet,
    CommentDeleteView,
    CommentListCreateView,
    EmailCheckView,
    ReviewingTasksView,
    TaskViewSet,
)

router = SimpleRouter()
router.register("boards", BoardViewSet, basename="board")
router.register("tasks", TaskViewSet, basename="task")

# The fixed task routes come first, otherwise the router would read
# "assigned-to-me" as a task id.
urlpatterns = [
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path(
        "tasks/assigned-to-me/",
        AssignedTasksView.as_view(),
        name="tasks-assigned-to-me",
    ),
    path(
        "tasks/reviewing/",
        ReviewingTasksView.as_view(),
        name="tasks-reviewing",
    ),
    path(
        "tasks/<int:task_id>/comments/",
        CommentListCreateView.as_view(),
        name="task-comments",
    ),
    path(
        "tasks/<int:task_id>/comments/<int:comment_id>/",
        CommentDeleteView.as_view(),
        name="task-comment-detail",
    ),
] + router.urls
