"""Production settings.

Reads all sensitive/environment-specific values from the environment. Designed
for a containerized deployment behind a TLS-terminating proxy (e.g. Render) with
a managed PostgreSQL database provided via ``DATABASE_URL``.
"""

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# --- Allowed hosts / CSRF ---------------------------------------------------
# ALLOWED_HOSTS is a comma-separated env var. On Render, the external hostname
# is injected as RENDER_EXTERNAL_HOSTNAME and is appended automatically.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# --- Database ---------------------------------------------------------------
# Single DATABASE_URL drives the managed Postgres connection. Persistent
# connections + health checks reduce per-request connection overhead.
DATABASES = {
    "default": {
        **env.db("DATABASE_URL"),
        "CONN_MAX_AGE": env.int("CONN_MAX_AGE", default=600),
        "CONN_HEALTH_CHECKS": True,
    }
}

# --- Static files -----------------------------------------------------------
# WhiteNoise serves compressed, hashed static assets from the app container.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# --- Security ---------------------------------------------------------------
# TLS is terminated at the platform proxy, which forwards X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# --- Email ------------------------------------------------------------------
# Defaults to SMTP; configure via env. Falls back to console if unset so the
# app never hard-fails on a missing mail server.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="Virtual Blood Bank <no-reply@vbb.local>"
)

# --- Frontend URLs ----------------------------------------------------------
# FRONTEND_URL is env-driven in base.py, which also derives
# HEADLESS_FRONTEND_URLS from it, so no production override is needed here.
