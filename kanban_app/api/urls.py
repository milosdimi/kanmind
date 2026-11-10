"""URL routes of the kanban app."""
from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import BoardViewSet, EmailCheckView

router = SimpleRouter()
router.register("boards", BoardViewSet, basename="board")

urlpatterns = [
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
] + router.urls
