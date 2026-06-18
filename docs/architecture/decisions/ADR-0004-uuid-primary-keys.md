# ADR 0004: UUID primary keys for all entities

Date: 2026-06-17

Status: Accepted

## Context

The SDS object model (SDS §4) specifies UUID identifiers for every entity
(`facilityId`, `userId`, `requestId`, `inventoryId`, `notificationId`,
`centerId`). The original implementation used Django's default integer
auto-increment primary keys. Identifiers are exposed in API URLs
(`/api/v1/blood-requests/{id}/accept/`) and serialized responses, so sequential
integer keys are enumerable — a meaningful concern for a health system holding
facility and request data.

## Decision

Use `UUIDField(primary_key=True, default=uuid.uuid4)` on all models
(`Facility`, `User`, `BloodUnit`, `BloodRequest`, `BloodRequestStatusEvent`,
`NotificationEvent`, `NotificationRecord`, `DonationCenter`, `AuditLog`).

Because the application is not yet deployed, initial migrations were regenerated
from scratch rather than written as data-preserving conversions. Development
seed data moved out of a migration and into the `seed_dev_data` command.

## Consequences

- Identifiers are non-enumerable, matching the SDS and reducing resource-
  enumeration risk.
- API responses return string UUIDs; aggregate endpoints stringify ids.
- No live data existed, so the regenerated migrations carry no migration debt.
