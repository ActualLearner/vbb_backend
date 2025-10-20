# ADR 0003: Deprecate compatibility shims for api/domain split

Date: 2026-05-09

Status: Accepted (completed 2026-06-07)

Context

We introduced compatibility shims that re-export new `api/` and `domain/` modules
to enable a non-breaking migration. These shims preserve import paths while the
codebase is migrated incrementally.

Decision

We will record a deprecation schedule for compatibility shims and remove them
once all internal and external imports have migrated to the new paths.

Plan

- Maintain shims for the short term (development + staged rollout).
- Add tests that assert both import paths work during the migration window.
- After a migration milestone (e.g., all internal code references removed), remove
  the shims and update the ADR to Accepted/Completed.

Consequences

- Positive: Keeps runtime stable during migration.
- Negative: Temporary maintenance cost; small overhead in IDE navigation.

Resolution

- 2026-06-07: Migration completed. All internal imports now reference the
  `api/` and `domain/` subpackages directly. The compatibility shim modules
  (`inventory/serializers.py`, `views.py`, `urls.py`, `authorizers.py`,
  `lifecycle.py`, `transitions.py`, `dashboard.py`) have been removed. The
  test suite passes against the new paths.
