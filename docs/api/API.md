# VBB Backend — API Contract

Hand-authored reference for the Virtual Blood Bank REST API. The authoritative
behavioural spec is `docs/SRS.pdf` / `docs/SDS.pdf`; this document describes the
**wire contract** of the implemented backend.

- **Base URL:** `/api/v1/`
- **Format:** JSON (`Content-Type: application/json`)
- **Transport:** HTTPS in production (TLS 1.2+)
- **Auth:** JWT bearer tokens (see [Authentication](#authentication))

---

## Conventions

### Identifiers & timestamps
- All resource IDs are **UUID** strings (e.g. `"3f1c…"`).
- Timestamps are ISO-8601 UTC (e.g. `"2026-06-18T07:30:00Z"`); date-only fields use `YYYY-MM-DD`.

### Pagination
List endpoints use page-number pagination (default page size **25**):

```json
{
  "count": 53,
  "next": "http://host/api/v1/blood-requests/?page=2",
  "previous": null,
  "results": [ /* objects */ ]
}
```
Query params: `?page=<n>`. **Not paginated:** `…/inventory-summary/`, `/dashboard/`,
`/district-inventory/`, and the `donation-centers/nearby/` action (return plain arrays).

### Errors
| Status | Meaning | Body |
| :-- | :-- | :-- |
| `400` | Validation error | `{"field": ["message"]}`, or `{"error": "..."}` for lifecycle transitions |
| `401` | Missing/invalid/expired token | `{"detail": "Authentication credentials were not provided."}` |
| `403` | Authenticated but not permitted (wrong role/facility, or password change pending) | `{"detail": "..."}` |
| `404` | Not found (or not visible to the caller) | `{"detail": "Not found."}` |

### Enumerations
- **Role:** `PROFESSIONAL`, `ADMIN`
- **Blood type:** `A+ A- B+ B- AB+ AB- O+ O-`
- **Request status:** `PENDING ACCEPTED REJECTED IN_TRANSIT FULFILLED CANCELLED`
- **Notification type:** `NEW_REQUEST REQUEST_ACCEPTED REQUEST_REJECTED REQUEST_IN_TRANSIT REQUEST_FULFILLED REQUEST_CANCELLED LOW_STOCK EXPIRING_SOON`

### Roles & authorization (SDS §2.3.2)
- **PROFESSIONAL** — clinical workflows for **their own facility**: add inventory, create requests, accept/reject/ship (when fulfilling), receive/cancel (when requesting).
- **ADMIN** — user & facility management only; **no** clinical actions; read-only elsewhere.

---

## Authentication

JWT via `djangorestframework-simplejwt`. Obtain a token, then send it on every
request:

```
Authorization: Bearer <access_token>
```

- **Access token** lifetime: **30 minutes** (maps to the 30-min inactivity logout).
- **Refresh token** lifetime: **7 days** (maps to "Remember Me"). Refresh tokens rotate.
- **Forced password change:** a newly provisioned user has `must_change_password = true`.
  Until they call `change-password`, every endpoint **except** `auth/login`,
  `auth/refresh`, `auth/me`, and `auth/change-password` returns `403`.

### `POST /api/v1/auth/login/`
Obtain an access/refresh pair. `username` accepts an **email, phone number, or username**.

Request:
```json
{ "username": "pro1@example.com", "password": "Str0ng!Pass1" }
```
Response `200`:
```json
{ "access": "<jwt>", "refresh": "<jwt>" }
```
Failure `401`: `{"detail": "No active account found with the given credentials"}`
(also returned for an inactive/deactivated account).

**Access-token claims:** `user_id`, `role`, `facility_id` (or `null`), `full_name`,
`must_change_password`, plus standard `exp`, `iat`, `jti`, `token_type`.

### `POST /api/v1/auth/refresh/`
Request: `{ "refresh": "<jwt>" }` → `200` `{ "access": "<jwt>", "refresh": "<jwt>" }`.

### `GET /api/v1/auth/me/`
Returns the caller's profile. → `200`:
```json
{
  "id": "uuid", "username": "pro1", "email": "pro1@example.com",
  "full_name": "Abebe Bekele", "phone_number": "+251911223344",
  "role": "PROFESSIONAL", "facility": "uuid", "must_change_password": false
}
```

### `PATCH /api/v1/auth/me/`
Updatable fields: `full_name`, `phone_number`. (Email, role, facility are read-only here.)

### `POST /api/v1/auth/change-password/`
Request:
```json
{ "current_password": "OldPass1!", "new_password": "NewStr0ng!Pass" }
```
`200` `{"detail": "Password updated."}`. Clears `must_change_password`.
`400` if the current password is wrong or the new password fails complexity
(≥8 chars incl. upper, lower, digit, special).

---

## Facilities

Object:
```json
{
  "id": "uuid", "name": "Black Lion Hospital",
  "region": "Addis Ababa", "zone": "Lideta", "woreda": 3,
  "street": "", "city": "Addis Ababa",
  "latitude": "9.013200", "longitude": "38.761700",
  "contact_phone": "+251111234501", "is_active": true
}
```

| Method | Path | Permission | Notes |
| :-- | :-- | :-- | :-- |
| `GET` | `/facilities/` | Authenticated | Paginated list. |
| `GET` | `/facilities/{id}/` | Authenticated | Single facility. |
| `POST`/`PUT`/`PATCH`/`DELETE` | `/facilities/{id}/` | **ADMIN** | Manage facilities. |

---

## Users (administration)

ADMIN only. Object (read):
```json
{
  "id": "uuid", "username": "pro1", "email": "pro1@example.com",
  "full_name": "Abebe Bekele", "phone_number": "+251911223344",
  "role": "PROFESSIONAL", "facility": "uuid",
  "is_active": true, "must_change_password": false,
  "last_login": "2026-06-18T07:30:00Z", "date_joined": "2026-06-01T09:00:00Z"
}
```

| Method | Path | Permission | Notes |
| :-- | :-- | :-- | :-- |
| `GET` | `/users/` | ADMIN | Paginated list. |
| `POST` | `/users/` | ADMIN | Create a user (see below). |
| `GET`/`PUT`/`PATCH`/`DELETE` | `/users/{id}/` | ADMIN | |
| `POST` | `/users/{id}/deactivate/` | ADMIN | Sets `is_active=false`. `400` if targeting self. |
| `POST` | `/users/{id}/reactivate/` | ADMIN | Sets `is_active=true`. |
| `POST` | `/users/{id}/assign-role/` | ADMIN | Body `{"role": "ADMIN"\|"PROFESSIONAL"}`. |
| `GET` | `/facilities/{id}/staff/` | ADMIN | Users at a facility (nested). |

**`POST /users/`** request:
```json
{
  "username": "newbie", "email": "n@example.com",
  "full_name": "New Bie", "phone_number": "+251933333333",
  "role": "PROFESSIONAL", "facility": "uuid",
  "password": "optional — generated if omitted"
}
```
Response `201` — the standard user object **plus** a one-time
`"temporary_password": "<generated>"`. The new user is created with
`must_change_password = true`.

---

## Inventory (nested under a facility)

Blood units are tracked individually (one row per unit). Object:
```json
{
  "id": "uuid", "blood_type": "A+",
  "facility": { /* facility object */ },
  "donated_at": "2026-06-10T08:00:00Z", "expires_at": "2026-07-22",
  "is_expiring_soon": false, "is_expired": false
}
```
`is_expiring_soon` = expires within 7 days and not yet expired.

| Method | Path | Permission | Query / Body |
| :-- | :-- | :-- | :-- |
| `GET` | `/facilities/{fid}/inventory/` | Authenticated | `?blood_type=A+` |
| `POST` | `/facilities/{fid}/inventory/` | **PROFESSIONAL**, own facility | body below |
| `GET` | `/facilities/{fid}/inventory-summary/` | Authenticated | aggregate counts (not paginated) |

**`POST` body:** `{ "blood_type": "O+", "facility_id": "<fid>", "expires_at": "2026-08-01" }`.
Adding to another facility returns `403`.

**Inventory summary** item: `{ "facility_id": "uuid", "facility_name": "…", "blood_type": "A+", "total_units": 12 }`.

### `GET /api/v1/district-inventory/`
Aggregated inventory for every active facility in the caller's woreda (district).
Auth required. Query: `?search=<facility name>`, `?blood_type=A+`. Returns a plain
array of inventory-summary items. `400` if the caller has no facility.

---

## Blood Requests

Object:
```json
{
  "id": "uuid",
  "requesting_facility": { /* facility */ },
  "fulfilling_facility": { /* facility */ },
  "requested_by": "pro1",
  "blood_type": "A+", "units_requested": 2,
  "notes": "urgent — PPH case", "rejection_reason": "",
  "status": "PENDING",
  "created_at": "…", "updated_at": "…",
  "acceptance_timestamp": null, "dispatch_timestamp": null, "fulfillment_timestamp": null,
  "status_events": [
    { "id": "uuid", "from_status": "PENDING", "to_status": "ACCEPTED",
      "actor": "ful_pro", "created_at": "…" }
  ]
}
```

| Method | Path | Permission | Query / Body |
| :-- | :-- | :-- | :-- |
| `GET` | `/blood-requests/` | Authenticated | `?status=PENDING` (repeatable), `?blood_type=A+`, `?type=incoming\|outgoing` |
| `POST` | `/blood-requests/` | **PROFESSIONAL** | create (below) |
| `GET` | `/blood-requests/{id}/` | Authenticated | single request |

**`POST` body** (writable fields only):
```json
{ "fulfilling_facility_id": "uuid", "blood_type": "A+", "units_requested": 2, "notes": "optional" }
```
`requesting_facility` and `requested_by` are set from the token. `400` if requesting
from your own facility or if the fulfilling facility lacks enough units.

### Lifecycle actions
All are `POST` to `/blood-requests/{id}/<action>/`. Success returns the updated
request object; an invalid state transition returns `400 {"error": "..."}`; a
caller without the right role/facility returns `403`.

| Action | Allowed from | Performed by | Effect |
| :-- | :-- | :-- | :-- |
| `accept/` | `PENDING` | PROFESSIONAL, fulfilling | Deducts oldest units; sets `acceptance_timestamp`; notifies requester (+ low-stock alert). Auto-rejects with `400` if stock is now insufficient. |
| `reject/` | `PENDING` | PROFESSIONAL, fulfilling | Body `{"reason": "optional"}` → `rejection_reason`. Notifies requester. |
| `ship/` | `ACCEPTED` | PROFESSIONAL, fulfilling | Sets `dispatch_timestamp`; status → `IN_TRANSIT`. |
| `receive/` | `IN_TRANSIT` | PROFESSIONAL, requesting | Creates units at requesting facility; sets `fulfillment_timestamp`; status → `FULFILLED`. |
| `cancel/` | `PENDING` or `ACCEPTED` | PROFESSIONAL, requesting | Status → `CANCELLED`; if it was `ACCEPTED`, reserved stock is restored to the fulfilling facility. |

---

## Dashboard

### `GET /api/v1/dashboard/`
Facility summary for the caller (not paginated). `400` if the caller has no facility.
```json
{
  "inventory_summary": [ { "blood_type": "A+", "total_units": 12 } ],
  "low_stock_alerts": ["AB-"],
  "expiring_soon_alerts": ["A+"],
  "incoming_requests_count": 1, "incoming_requests_ids": ["uuid"],
  "outgoing_requests_count": 2, "outgoing_requests_ids": ["uuid", "uuid"]
}
```

---

## Donation Centers

Read-only directory, visible to any authenticated user. Object:
```json
{
  "id": "uuid", "name": "National Blood Bank - Addis",
  "street": "", "city": "Addis Ababa",
  "latitude": "9.030000", "longitude": "38.740000",
  "operating_hours": "Mon-Sat 8AM-6PM", "contact_info": "+251115524948",
  "distance_km": 1.84
}
```
`distance_km` appears only in the `nearby` response.

| Method | Path | Notes |
| :-- | :-- | :-- |
| `GET` | `/donation-centers/` | Paginated list. |
| `GET` | `/donation-centers/{id}/` | Single center. |
| `GET` | `/donation-centers/nearby/?lat=&lng=` | Plain array ordered by distance; centers without coordinates sort last. Without `lat`/`lng`, returns `{"detail": "...", "results": [...]}` in name order. |

---

## Notifications

Per-user delivered notifications. Object:
```json
{
  "id": "uuid", "event": "uuid", "event_type": "request_accepted",
  "payload": { "request_id": "uuid", "message": "Request … was accepted." },
  "read": false, "delivered_at": "2026-06-18T07:31:00Z"
}
```

| Method | Path | Notes |
| :-- | :-- | :-- |
| `GET` | `/notifications/` | Paginated; **only the caller's own** records. |
| `POST` | `/notifications/{id}/mark_read/` | Sets `read=true`. `404` for another user's record. |

Delivery is asynchronous: transitions persist a `NotificationEvent`, and the
`dispatch_notifications` management command fans events out to recipients over the
FCM push channel (see ADR-0007).

---

## Health

### `GET /healthz/`
Unauthenticated liveness probe (no DB access). → `200 {"status": "ok"}`.
