# ADR 0002: Asynchronous notification dispatch without Celery

Date: 2026-05-09

Status: Accepted

## Context

The system must deliver Notification Events asynchronously through push and SMS channels.
The deployment target does not support Celery reliably under current budget and operational constraints.
We still need non-blocking API requests, user-level unread tracking, and operational simplicity.

## Decision

Adopt a scheduled management-command dispatcher as the asynchronous seam for notification delivery.

- Transition flows emit Notification Events inside the transaction boundary.
- A management command dispatches pending events on a schedule (for example every minute).
- Delivery fan-out goes through channel adapters (push adapter and SMS adapter).
- Delivery attempt details are logged to stdout and not persisted as delivery-attempt rows.
- Notification read/unread state is tracked at the user level in Notification Records.

## Rationale

- Meets asynchronous requirement without adding queue infrastructure.
- Keeps write-path latency low because HTTP requests only emit events.
- Keeps operations simple for low-cost deployments.
- Preserves a clean seam so migration to Celery later remains possible.

## Consequences

Positive:

- No external worker stack is required for phase 1.
- Failures are observable via logs.
- Architecture remains modular through adapter seams.

Negative:

- Throughput is lower than queue-backed workers.
- Retry sophistication is limited in phase 1.
- Dispatch schedule granularity controls delivery latency.

## Alternatives considered

### 1. Celery worker queue

- Pros: robust retries, high throughput, mature ecosystem.
- Cons: extra infrastructure and operational cost not acceptable now.

### 2. Inline synchronous delivery in request handlers

- Pros: simplest implementation.
- Cons: violates asynchronous requirement and increases API latency/failure surface.

### 3. Signal-triggered background threads

- Pros: minimal code change.
- Cons: weak reliability model, hard to supervise, poor production predictability.

## Migration path

If delivery volume or reliability requirements increase, replace scheduler-triggered command execution with queue-backed workers while preserving the same adapter interfaces and Notification Event contract.

## Addendum (2026-07)

The dispatcher command gained a long-running worker mode: `dispatch_notifications --loop [--interval N]` (default 60 s) runs one batch per cycle in-process, with graceful SIGTERM/SIGINT shutdown (finish the in-flight batch, exit 0) and per-cycle exception isolation. This stays within this ADR's no-broker decision — it is the same management command supervised by the container runtime rather than an external scheduler — and is now the recommended production path once infrastructure allows; one-shot mode remains for cron-style scheduling. Each event is additionally claimed and delivered in its own transaction (`select_for_update(skip_locked=True)`), giving at-least-once push delivery and exactly-once in-app records, and making concurrent dispatchers safe. See docs/runbooks/notification-dispatcher.md.
