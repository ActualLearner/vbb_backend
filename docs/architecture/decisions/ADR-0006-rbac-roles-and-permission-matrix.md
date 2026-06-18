# ADR 0006: Two-role RBAC and the SDS permission matrix

Date: 2026-06-17

Status: Accepted

## Context

The SDS (§2.3) defines exactly two roles and a permission matrix the "backend
API will enforce for every request":

- **PROFESSIONAL** (doctors, nurses, technicians): all clinical workflows —
  update own-facility inventory, create blood requests, respond to incoming
  requests, advance request status. Scoped to their own facility.
- **ADMIN** (facility administrator): user and facility management only;
  **no** clinical actions; read-only elsewhere.

The original code used roles `ADMIN` + `FACILITY_REPRESENTATIVE` and treated
`ADMIN` as a super-capable actor that could perform clinical actions — the
inverse of the SDS. The SRS database section (DB-002) lists job titles (Doctor,
Nurse, Administrator, Blood Bank Technician), but the SDS matrix is the
authoritative, enforceable specification, so we collapse job titles into the two
RBAC roles.

## Decision

- Rename the role enum to `PROFESSIONAL` + `ADMIN`.
- Rewrite `BloodRequestAuthorizer` so clinical actions require the PROFESSIONAL
  role **and** an own-facility match; ADMIN is denied all clinical actions.
- Enforce the matrix in DRF: request creation and inventory writes require
  PROFESSIONAL; user and facility management require ADMIN; facilities are
  read-only for non-admins (previously any authenticated user could edit them —
  a real defect).

We keep `region/zone/woreda` on `Facility` rather than the SDS's single
`district` string: it is the correct Ethiopian administrative hierarchy and
`woreda` is the district used for district-inventory scoping.

## Consequences

- Server-side authorization now matches the SDS matrix exactly.
- A facility-editing privilege-escalation defect is closed.
- Existing tests were updated to the inverted ADMIN semantics.
