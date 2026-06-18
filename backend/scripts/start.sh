#!/usr/bin/env bash
# Production container entrypoint: apply migrations, then serve with gunicorn.
# Render (and most PaaS) inject the listen port via $PORT.
set -e

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-3}" \
  --access-logfile - \
  --error-logfile -
