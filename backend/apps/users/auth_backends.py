"""Authenticate by email or Ethiopian phone number (SRS VBB-FUN-UM-004)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """Allow login with an email address, phone number, or username.

    Inactive accounts are rejected by ``user_can_authenticate`` (inherited),
    satisfying SRS VBB-UC-007 4b ("Your account has been deactivated").
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("email") or kwargs.get("phone_number")
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(
                Q(username__iexact=username)
                | Q(email__iexact=username)
                | Q(phone_number=username)
            )
        except User.DoesNotExist:
            # Run the default hasher once to mitigate timing attacks.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = (
                User.objects.filter(
                    Q(username__iexact=username)
                    | Q(email__iexact=username)
                    | Q(phone_number=username)
                )
                .order_by("id")
                .first()
            )

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
