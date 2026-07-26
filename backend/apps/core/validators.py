"""Shared validators (SRS NFR-SEC-004, VBB-FUN-UM-004, DB-001/002)."""

import re
import secrets

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext as _


def generate_temp_password(length: int = 12) -> str:
    """Generate a temporary password satisfying the complexity policy.

    Guarantees at least one uppercase, lowercase, digit and special character
    (SRS NFR-SEC-004) so it passes ``PasswordComplexityValidator``.
    """
    upper = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    lower = "abcdefghijkmnpqrstuvwxyz"
    digits = "23456789"
    special = "!@#$%^&*-_"
    alphabet = upper + lower + digits + special
    required = [
        secrets.choice(upper),
        secrets.choice(lower),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    rest = [secrets.choice(alphabet) for _ in range(max(length, 8) - len(required))]
    chars = required + rest
    # Shuffle without revealing the fixed positions of the required classes.
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


# Ethiopian phone numbers: optional +251 or leading 0, then a 9-digit subscriber
# number beginning with 9 (mobile) or 7. Accepts e.g. +251911223344, 0911223344.
ethiopian_phone_validator = RegexValidator(
    regex=r"^(?:\+251|0)(?:9|7)\d{8}$",
    message=_(
        "Enter a valid Ethiopian phone number (e.g. +251911223344 or 0911223344)."
    ),
)


class PasswordComplexityValidator:
    """Require upper, lower, digit, and special characters (SRS NFR-SEC-004)."""

    SPECIAL = r"[^A-Za-z0-9]"

    def validate(self, password, user=None):
        errors = []
        if not re.search(r"[A-Z]", password):
            errors.append(_("an uppercase letter"))
        if not re.search(r"[a-z]", password):
            errors.append(_("a lowercase letter"))
        if not re.search(r"\d", password):
            errors.append(_("a digit"))
        if not re.search(self.SPECIAL, password):
            errors.append(_("a special character"))
        if errors:
            raise ValidationError(
                _("Password must contain %(items)s.") % {"items": ", ".join(errors)},
                code="password_not_complex",
            )

    def get_help_text(self):
        return _(
            "Your password must contain an uppercase letter, a lowercase "
            "letter, a digit, and a special character."
        )
