from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = []

# Allow the Vite dev server origin by default so the web client works out of
# the box; an explicit CORS_ALLOWED_ORIGINS env var still wins.
if not CORS_ALLOWED_ORIGINS:  # noqa: F405
    CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]

# Database
# Default development Postgres config (requires env vars / Docker).
# Tests use config.settings.test (in-memory SQLite) via pytest.
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
