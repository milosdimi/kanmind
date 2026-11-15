"""Create the guest user that the frontend uses for its guest login."""
from django.contrib.auth.hashers import make_password
from django.db import migrations

GUEST_EMAIL = "guest@kanmind.de"
GUEST_PASSWORD = "guest1234"


def create_guest_user(apps, schema_editor):
    """Add the guest user once; an existing user is left unchanged."""
    user_model = apps.get_model("auth", "User")
    user_model.objects.get_or_create(
        username=GUEST_EMAIL,
        defaults={
            "email": GUEST_EMAIL,
            "first_name": "Guest",
            "last_name": "User",
            "password": make_password(GUEST_PASSWORD),
        },
    )


def remove_guest_user(apps, schema_editor):
    """Delete the guest user when the migration is reversed."""
    user_model = apps.get_model("auth", "User")
    user_model.objects.filter(username=GUEST_EMAIL).delete()


class Migration(migrations.Migration):
    """Data migration: guest user for the frontend's guest login."""

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("authtoken", "0004_alter_tokenproxy_options"),
    ]

    operations = [
        migrations.RunPython(create_guest_user, remove_guest_user),
    ]
