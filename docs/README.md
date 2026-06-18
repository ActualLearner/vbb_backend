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
