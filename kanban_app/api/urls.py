"""URL routes of the kanban app."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    AssignedTasksView,
    BoardViewSet,
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
] + router.urls
