# Documentation Map

## Authoritative Specifications

- SRS (authoritative): docs/SRS.pdf
- SDS (authoritative): docs/SDS.pdf

The markdown product docs below are condensed summaries of the PDFs.

## API Contract

- REST API reference (endpoints, payloads, auth, errors): [api/API.md](api/API.md)

## Product Docs

- SRS summary: docs/product/SRS.md
- SDS summary: docs/product/SDS.md
- Delivery phases: docs/product/PHASES.md

## Architecture Docs

- Domain context: [CONTEXT.md](CONTEXT.md)
- ADRs: docs/architecture/decisions/
  - ADR-0001 Blood Request transition seam
  - ADR-0002 Async notification dispatch without Celery
  - ADR-0003 Deprecate compatibility shims
  - ADR-0004 UUID primary keys
  - ADR-0005 JWT authentication
  - ADR-0006 Two-role RBAC and the SDS permission matrix
  - ADR-0007 FCM push delivery; drop SMS
  - ADR-0008 Three-role least-privilege RBAC
  - ADR-0009 Web client support, CORS, and token security hardening
  - ADR-0010 OpenAPI schema and standardized error envelope

## Runbooks

Operational guides for running the system in production:

- [Deploying to Render](runbooks/deploy.md) — blueprint, env vars, migrations, rollback
- [Notification dispatcher](runbooks/notification-dispatcher.md) — how dispatch works, scheduling, failure modes, verifying delivery
- [Incident response](runbooks/incident-response.md) — triage for API/DB/auth/notification incidents; where logs live
