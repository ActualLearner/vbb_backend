# Delivery Phases

> **Note:** `docs/SRS.pdf` and `docs/SDS.pdf` are the authoritative specifications.
> The backend is now feature-complete against those PDFs (auth/JWT, RBAC matrix,
> user lifecycle, request notes/timestamps/history, donor-center mapping,
> district inventory, expiring-soon alerts, FCM push, audit trail). The phase
> breakdown below is retained for historical context. Design deviations are
> recorded in `docs/architecture/decisions/` (ADR-0004 … ADR-0007).

## Objective

Define what is in scope for each delivery phase so architecture and implementation sequencing stay aligned.

## Phase 1: Production-Ready API Baseline

### Included

- Authentication and facility-based authorization
- Blood inventory API and Blood Request lifecycle API
- Centralized inventory domain configuration constants
- Notification Event emission from transition seam
- Scheduled asynchronous notification dispatch via management command
- Push and SMS adapter interfaces with initial provider integration
- User-level Notification Record read/unread state
- REST endpoint to mark notifications as read
- Removal of backend HTML signup/testing views and routes
- Core unit test coverage for lifecycle and authorization

### Exit Criteria

- No HTML testing endpoints remain in backend API runtime.
- Notification Events are dispatched asynchronously without blocking request handlers.
- Read/unread notification behavior is visible and correct at user level.
- SRS functional requirements 3.1 to 3.6 are met for backend API baseline.

## Phase 2: Reliability and Scale Hardening

### Included

- Optional queue-backed worker infrastructure if load requires it
- Advanced retry/backoff and dead-letter handling for notification delivery
- Expanded integration test suite and phase-finalization end-to-end coverage
- Operational dashboards and alerting improvements

### Exit Criteria

- Delivery throughput and failure handling meet production SLO targets.
- Integration coverage validates complete request-to-notification flows.

## Deferred Decisions

- Whether to migrate from scheduled command dispatch to queue-backed workers
- Whether to persist delivery-attempt telemetry in the database

## References

- docs/product/SRS.md
- docs/product/SDS.md
- docs/architecture/decisions/ADR-0001-blood-request-transitions.md
- docs/architecture/decisions/ADR-0002-async-notification-dispatch-without-celery.md
