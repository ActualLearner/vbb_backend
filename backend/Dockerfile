# --------------BASE STAGE--------------#
FROM python:3.12.3-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .


#--------------DEVELOPMENT STAGE--------------#
FROM base AS dev

# Install development-only dependencies from pyproject extras.
RUN pip install --no-cache-dir ".[dev]"

# Expose the port that the application listens on & run the application.
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


#--------------PRODUCTION STAGE--------------#
FROM base AS prod

ENV DJANGO_SETTINGS_MODULE=config.settings.prod

# Collect static assets at build time. Settings are evaluated on import, so we
# supply throwaway values for the required env vars; collectstatic never touches
# the database or uses the real secret.
RUN SECRET_KEY=build-only-dummy \
    DATABASE_URL=postgres://build:build@localhost:5432/build \
    python manage.py collectstatic --no-input

# Run as an unprivileged user. Grant ownership so migrations/static work at runtime.
RUN addgroup --system app && adduser --system --group app \
    && chmod +x scripts/start.sh \
    && chown -R app:app /app
USER app

EXPOSE 8000

# Migrate then serve. Render injects $PORT.
CMD ["./scripts/start.sh"]
