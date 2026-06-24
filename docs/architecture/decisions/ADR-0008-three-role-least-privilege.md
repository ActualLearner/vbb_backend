# ADR 0008: Three-role least-privilege RBAC

Date: 2026-06-21

Status: Accepted (supersedes the role model of ADR-0006)

## Context

ADR-0006 adopted the SDS's two roles: `ADMIN` and `PROFESSIONAL`, where
PROFESSIONAL performed *all* clinical actions for a facility. In review we found
that single role conflates two genuinely different jobs:

- **Inventory custody / supply** — logging stock and fulfilling incoming
  requests (accept/reject/ship). Desk-oriented, data-entry work.
- **Requesting care** — a clinician raising a request during an emergency and
  confirming its receipt.

Bundling both into one role weakens least-privilege and prevents clean,
role-specific dashboards in the planned frontends.

## Decision

Split `PROFESSIONAL` into two roles, giving three total:

| Role | Capabilities | Scope |
| :-- | :-- | :-- |
| **ADMIN** | Manage users & facilities; read everything. **No clinical actions.** | — |
| **SUPPLY** | Add/update inventory; accept / reject / ship incoming requests. | own facility (fulfilling) |
| **CLINICIAN** | Create request; cancel request; **receive** (confirm arrival). | own facility (requesting) |

`receive` is owned by the **clinician** (the requester confirms what they
asked for arrived), not by supply.

This is an authorization + presentation change only. The inventory and
blood-request **domain logic is unchanged**; only `BloodRequestAuthorizer`, the
DRF permission classes/viewset wiring, the `User.Role` enum, the seed command,
and tests changed.

## Consequences

- Tighter least-privilege and clearer accountability in the audit log (who
  manages stock vs. who requests) — valuable for a blood-safety system.
- Enables clean per-role dashboards in the frontend(s).
- One open product question deferred: whether a single user may hold more than
  one role (relevant for very small clinics where one person does both jobs).
  v1 ships **single role per user**; revisit with capability flags / multi-role
  if dual-hat staffing proves common.

## Alternatives considered

- **Keep the 2-role model (ADR-0006):** simpler, but cannot express
  least-privilege between stock custody and requesting, and forces an
  everything-or-nothing clinical dashboard.
- **Capability flags instead of roles:** maximally flexible, but more machinery
  than warranted now; the role presets cover the common cases.
