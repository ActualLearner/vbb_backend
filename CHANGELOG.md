# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- OpenAPI 3 schema at `/api/schema/` with interactive Swagger UI at
  `/api/docs/` (drf-spectacular; ADR-0010).
- `POST /api/v1/auth/logout/` blacklists the presented refresh token
  (ADR-0009).
- API rate limiting: anonymous 60/min, authenticated 240/min, and a dedicated
  10/min scope on login; all env-overridable (ADR-0009).
- CORS support with explicit, env-driven allowed origins for the web client
  (ADR-0009).
- Blocking `pip-audit` job in CI over production dependencies.
- Operational runbooks (`docs/runbooks/`): Render deployment, notification
  dispatcher, incident response.
- Dependabot configuration for pip (`backend/`) and GitHub Actions dependencies.
- This changelog.

### Changed

- **Breaking (pre-1.0):** all 4xx/5xx responses now use the
  drf-standardized-errors envelope `{"type", "errors": [{"code", "detail",
  "attr"}]}` (ADR-0010).
- Refresh-token rotation now blacklists the rotated-out token.
- Blood-request transition endpoints enforce the ADR-0008 role matrix
  per-action at the API permission layer (cancel/receive vs
  accept/reject/ship).
- Product scope now targets a web client alongside the mobile client (owner
  decision, 2026-07-26; see ADR-0009 and `docs/CONTEXT.md`). Docs updated
  accordingly.
- Tooling: pytest-django is the canonical test runner (hermetic
  `config.settings.test`, suite runs in ~3s); ruff replaces
  black/flake8/isort; CI enforces an 85% coverage gate; pre-commit added.

### Security

- Dependency upgrades resolving published advisories: Django 5.2.7 → 5.2.16,
  django-allauth 65.12.1 → 65.14.1, djangorestframework-simplejwt
  5.3.1 → 5.5.1.

## Backend baseline — retrospective (2025-10 → 2026-07)

Everything below was delivered before this changelog existed, summarized from
the git history. It constitutes the production-ready backend API baseline
(Phase 1 in `docs/product/PHASES.md`).

### Added

- **Project foundation** (Oct 2025): Django + DRF project with Docker/Compose
  development environment, PostgreSQL, split settings (base/dev/prod), and a
  Makefile task runner.
- **Core domain**: Facility and User models; BloodUnit and BloodRequest with a
  stateful lifecycle (pending → accepted/rejected → shipped → received, or
  cancelled) exposed through nested REST routes; per-transition timestamps,
  request notes, rejection reasons, and status history; cancel restores
  reserved stock.
- **Dashboard & discovery**: facility dashboard summary (inventory, requests,
  low-stock and expiring-soon alerts), district-wide inventory view, and
  filtering across inventory and request endpoints.
- **Authentication & authorization**: JWT auth with login by email or phone
  (ADR-0005), 30-minute access / 7-day refresh tokens, temporary-password
  provisioning with a forced first-login password change, and role-based
  access control — initially two roles (ADR-0006), then split into a
  three-role least-privilege matrix: ADMIN / SUPPLY / CLINICIAN (ADR-0008).
- **Notifications**: typed NotificationEvent emission from the request
  lifecycle, a scheduled `dispatch_notifications` management command
  (ADR-0002, no Celery), per-user NotificationRecord read/unread state with a
  mark-read endpoint, and Firebase Cloud Messaging push delivery (ADR-0007).
- **Donations & audit**: donation-center directory with nearest-by-distance
  lookup, and an immutable audit log for security-relevant actions.
- **Shared validators**: Ethiopian phone validation and password complexity
  rules; centralized, env-overridable domain constants (blood types, expiry
  days, low-stock threshold, woreda range, page size).
- **Infrastructure**: GitHub Actions CI (lint, test, Docker build), Render
  deployment blueprint (`render.yaml`) with managed Postgres and a `/healthz/`
  health check, production settings with structured stdout logging and
  WhiteNoise static files, multi-stage Dockerfile.
- **Documentation**: authoritative SRS/SDS PDFs with markdown summaries, a
  hand-authored API contract (`docs/api/API.md`), domain context, delivery
  phases, and ADRs 0001–0008.

### Changed

- Restructured into a monorepo with the Django project under `backend/`
  (clients planned as siblings).
- Split apps into layered `api/` (HTTP) and `domain/` (business logic)
  packages; flat test files replaced with structured test packages and
  factories.
- Replaced `requirements.txt` with `pyproject.toml`.
- UUIDs adopted as primary keys (ADR-0004); compatibility shims deprecated and
  removed (ADR-0003).
- Dropped the SMS notification channel in favour of FCM-only push, per the SDS
  contingency (ADR-0007).

### Fixed

- Blood-request transition actions routed through their matching authorizer
  methods, closing gaps in the RBAC permission matrix.
- Heavy data seeding moved out of migrations into an explicit `seed_dev_data`
  command.

### Removed

- Backend HTML signup/testing views and routes (accounts are provisioned by
  admins; a minimal login page remains for browsable-API testing).
