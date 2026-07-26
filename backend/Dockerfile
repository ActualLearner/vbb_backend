# --------------BASE STAGE--------------#
# python:3.12-slim pinned by multi-arch index digest for reproducible builds.
# Refresh the digest with: docker buildx imagetools inspect python:3.12-slim
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Unprivileged runtime user shared by every stage. UID/GID default to 1000 so
# bind-mounted source in dev keeps host-compatible ownership.
ARG UID=1000
ARG GID=1000
RUN groupadd --gid "${GID}" app \
    && useradd --uid "${UID}" --gid app --create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Install runtime dependencies BEFORE copying the source so the (slow)
# dependency layer stays cached across source-only changes. The project
# installs itself as a package, so extract the pinned dependency list from
# pyproject.toml and install just that here; the project itself is installed
# with --no-deps in the stages below.
COPY pyproject.toml ./
RUN python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']; print('\n'.join(d))" > /tmp/requirements.txt \
    && pip install -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt


#--------------DEVELOPMENT STAGE--------------#
FROM base AS dev

# Dev-only dependencies from the pyproject extras, also cached independently
# of source changes.
RUN python -c "import tomllib; d = tomllib.load(open('pyproject.toml', 'rb'))['project']['optional-dependencies']['dev']; print('\n'.join(d))" > /tmp/requirements-dev.txt \
    && pip install -r /tmp/requirements-dev.txt \
    && rm /tmp/requirements-dev.txt

# Copy the source and install the project itself (dependencies are already
# installed above, so this layer rebuilds fast). Remove the in-tree build
# artifacts setuptools leaves behind.
COPY . .
RUN pip install --no-deps . \
    && rm -rf build ./*.egg-info

# Run as the unprivileged user; compose bind-mounts the source over /app.
USER app

# Expose the port that the application listens on & run the application.
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


#--------------PRODUCTION STAGE--------------#
FROM base AS prod

LABEL org.opencontainers.image.source="https://github.com/ActualLearner/vbb_backend" \
    org.opencontainers.image.description="Virtual Blood Bank backend (Django + gunicorn)" \
    org.opencontainers.image.licenses="NOASSERTION"

ENV DJANGO_SETTINGS_MODULE=config.settings.prod

COPY . .
RUN pip install --no-deps . \
    && rm -rf build ./*.egg-info \
    && chmod +x scripts/start.sh

# Collect static assets at build time. Settings are evaluated on import, so we
# supply throwaway values for the required env vars; collectstatic never touches
# the database or uses the real secret.
RUN SECRET_KEY=build-only-dummy \
    DATABASE_URL=postgres://build:build@localhost:5432/build \
    python manage.py collectstatic --no-input

# Run as an unprivileged user. /app stays root-owned and read-only to the app
# user: nothing writes to it at runtime (whitenoise serves the prebuilt
# staticfiles; gunicorn uses /tmp; migrations only touch the database).
USER app

EXPOSE 8000

# Probe the liveness endpoint with the stdlib (no curl in slim images). The
# X-Forwarded-Proto header satisfies SECURE_PROXY_SSL_HEADER so the probe is
# not bounced by the production HTTPS redirect, and the Host header is taken
# from RENDER_EXTERNAL_HOSTNAME (when set) so the probe passes ALLOWED_HOSTS.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; req = urllib.request.Request('http://127.0.0.1:%s/healthz/' % os.environ.get('PORT', '8000'), headers={'X-Forwarded-Proto': 'https', 'Host': os.environ.get('RENDER_EXTERNAL_HOSTNAME') or '127.0.0.1'}); urllib.request.urlopen(req, timeout=4)"

# Migrate then serve. Render injects $PORT.
CMD ["./scripts/start.sh"]
