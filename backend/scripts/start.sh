#!/usr/bin/env bash
# Production container entrypoint: apply migrations, then serve with gunicorn.
# Render (and most PaaS) inject the listen port via $PORT.
set -euo pipefail

python manage.py migrate --noinput

# exec replaces the shell so gunicorn is PID 1 and receives SIGTERM directly,
# giving in-flight requests --graceful-timeout seconds to finish on shutdown.
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-30}" \
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
  --access-logfile - \
  --error-logfile -
