"""Test settings: fast and hermetic.

Used by pytest (see ``[tool.pytest.ini_options]`` in pyproject.toml). Inherits
from base — not dev — so the test run never depends on Postgres or a local
.env file.
"""

import os

# base.py requires SECRET_KEY. Provide a default so the suite runs without a
# real .env (e.g. in CI); a value from the environment/.env still wins.
os.environ.setdefault("SECRET_KEY", "test-only-insecure-secret-key")

from .base import *  # noqa: E402

DEBUG = False

# In-memory SQLite keeps the suite self-contained and fast.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# MD5 is insecure but ~100x faster than the default hasher; fine for tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Keep outgoing mail in memory so tests can assert on django.core.mail.outbox.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Plain storage backends: no manifest/collectstatic requirements, no disk I/O
# for uploaded files.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Serve static files via finders so WhiteNoise doesn't warn about a missing
# STATIC_ROOT (collectstatic is never run for tests).
WHITENOISE_AUTOREFRESH = True
WHITENOISE_USE_FINDERS = True
