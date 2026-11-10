"""API views for registration and login."""
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    RegistrationSerializer,
    UserSerializer,
)


def build_auth_response(user):
    """Return the token and user data the frontend stores after login."""
    token, _ = Token.objects.get_or_create(user=user)
    user_data = UserSerializer(user).data
    return {
        "token": token.key,
        "fullname": user_data["fullname"],
        "email": user_data["email"],
        "user_id": user_data["id"],
    }


class RegistrationView(APIView):
    """POST /api/registration/ - create a new user account.

    Open on purpose: a visitor has no account yet. Authentication is
    disabled so an outdated token in the header cannot block the request.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the sign up data, create the user and return a token."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            build_auth_response(user), status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """POST /api/login/ - log in with email and password.

    Open on purpose: the user logs in to receive a token.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Check the credentials and return a token."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        return Response(build_auth_response(user), status=status.HTTP_200_OK)
