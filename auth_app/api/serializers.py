"""Serializers for registration, login and the short user representation."""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Short user representation: id, email and full name."""

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]

    def get_fullname(self, obj):
        """Join first and last name to the full name."""
        return f"{obj.first_name} {obj.last_name}".strip()


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates the sign up data and creates a new user."""

    fullname = serializers.CharField(write_only=True, max_length=150)
    email = serializers.EmailField()
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["fullname", "email", "password", "repeated_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        """Reject an email address that is already registered."""
        email = value.lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("This email is already in use.")
        return email

    def validate(self, attrs):
        """Make sure both passwords are identical."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create the user; the email doubles as Django username."""
        fullname = validated_data["fullname"].strip()
        first_name, _, last_name = fullname.partition(" ")
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name.strip(),
        )


class LoginSerializer(serializers.Serializer):
    """Checks email and password and returns the matching user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the user by email and password."""
        user = User.objects.filter(email__iexact=attrs["email"]).first()
        if user:
            user = authenticate(
                username=user.username, password=attrs["password"]
            )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        attrs["user"] = user
        return attrs
