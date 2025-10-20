# flake8: noqa
import sys

from .base import *

DEBUG = True

ALLOWED_HOSTS = []

# Database
# In development we normally use Postgres (via env vars). When running
# tests locally (manage.py test) it's convenient to fall back to an
# in-memory SQLite DB so tests can run without Docker. This preserves
# production/dev behaviour while making local test runs robust.
if any(arg for arg in sys.argv if arg.startswith("test")):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    # Default development Postgres config (requires env vars / Docker)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "HOST": env("POSTGRES_HOST"),
            "PORT": env("POSTGRES_PORT"),
        }
    }

# SMTP Configs
# This will make it so that the email is outputted to the terminal by default.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
