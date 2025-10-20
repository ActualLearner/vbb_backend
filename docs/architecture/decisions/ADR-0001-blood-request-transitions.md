# ADR 0001: Centralize Blood Request transition orchestration

Date: 2026-05-08

Status: Accepted

## Context

The codebase currently spreads Blood Request behaviour across multiple modules: view action routing and side-effects, a lifecycle implementation that mutates DB state, an authorizer and DRF permissions, and serializer validation that duplicates some preconditions. Notifications and low-stock handling are printed or handled via signals. This scattering makes it hard to reason about, test, and evolve Blood Request behaviour.

## Decision

Introduce a single external seam for Blood Request state transitions, the "Blood Request transition module". It will:

- Expose transition methods: `accept`, `reject`, `ship`, `receive`, `cancel`.
- Enforce authorization intent at the seam.
- Delegate transactional DB mutations to `BloodRequestLifecycleService` (implementation detail).
- Emit domain `NotificationEvent` records instead of delivering notifications inline.
- Return a stable result object that contains error state, remaining counts, low-stock flags, and any emitted event ids.

Views become thin adapters that forward intents to the seam and serialize the result. DRF permission classes stay as route-level gates but domain authorization intent moves into the seam to avoid duplication.

## Migration plan

1. Add `apps/inventory/transitions.py` (the seam) and implement `BloodRequestTransitionService`.
2. Add a lightweight domain event model `NotificationEvent` in `apps/notifications/models.py`.
3. Update `apps/inventory/views.py` to call the new transition seam for lifecycle actions.
4. Update tests in `apps/inventory/tests.py` to exercise the seam directly and adjust any assertions that depended on implementation location.

## Consequences

- Locality and leverage improve: policy, orchestration, and event emission are concentrated.
- Tests become more focused; lifecycle internals remain testable as implementation detail.
- No external API changes; only internal wiring is modified.

## Alternatives considered

- Keep behaviour spread and document it: avoided due to high maintenance cost.
- Move all logic into views: avoided to preserve testability and locality.
