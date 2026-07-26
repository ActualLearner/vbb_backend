# VBB Backend Context

> **Source of truth:** `docs/SRS.pdf` and `docs/SDS.pdf` are the authoritative
> specifications. The markdown files under `docs/` summarize them for quick
> reference. Where this document once diverged from the PDFs it has been
> reconciled; design deviations are recorded in `docs/architecture/decisions/`.

## Product Scope

- The current repository is the backend API for the Virtual Blood Bank product.
- The product targets **two clients — a mobile client and a web client** — on
  top of this backend API. The SRS (VBB-DC-001) specified a mobile client only;
  the addition of a web client is an owner decision of 2026-07-26 that
  post-dates the SRS/SDS PDFs. It is recorded here as a deliberate deviation
  and is being captured in ADR-0009 (web client support, CORS, and token
  security hardening); the PDFs have not been revised.
- Both clients are future deliverables and out of scope for this repository.
- The backend is feature-complete against the PDFs (see deviations).

## Canonical Terms

- Facility: A hospital, clinic, or blood bank that holds inventory and participates in requests. Has region/zone/woreda (the woreda is the district), address, contact phone, and an active flag.
- User: An authenticated account tied to a facility, with an Ethiopian phone number and a role.
- Role — ADMIN: A facility administrator who manages users and facilities and reads everything; performs no clinical actions.
- Role — SUPPLY: Inventory/supply staff who manage their facility's stock and fulfill incoming requests (accept/reject/ship).
- Role — CLINICIAN: Clinical staff who raise requests and confirm receipt (create/cancel/receive). See ADR-0008 for the three-role least-privilege matrix.
- Blood Unit: One unit of blood stored at a facility with a blood type and expiration date.
- Blood Request: A request for one or more blood units from one facility to another. Carries optional notes, a rejection reason, and per-transition timestamps.
- Blood Request Lifecycle: The allowed states and transitions; a status-history record is appended on each transition.
- Notification Event / Record: A backend event and its per-user delivery record (read/unread state).
- Notification Dispatcher: A scheduled backend process that delivers pending events asynchronously.
- Delivery Channel Adapter: A channel implementation; the active push channel is FCM (SMS dropped — see ADR-0007).
- Donation Center: An informational location where donors can give blood (directory + nearest-by-distance).
- Audit Log: An immutable record of security-relevant actions (SRS NFR-SEC-006).
- Dashboard Summary: The facility overview of inventory, incoming/outgoing requests, low-stock and expiring-soon alerts.

## Authentication & Authorization

- The API authenticates with JWT (SDS §2.3.3); tokens carry role and facility claims. Login is by email or phone (ADR-0005).
- Access tokens last 30 minutes (inactivity logout); refresh tokens last 7 days ("Remember Me").
- Newly provisioned users receive a temporary password and must change it on first use before other endpoints unlock.
- Authorization follows the SDS §2.3.2 permission matrix (ADR-0006).

## Notification Rules

- Notifications are delivered asynchronously via the scheduled dispatcher.
- The active delivery channel is push (FCM); SMS was dropped per the SDS contingency (ADR-0007).
- Blood Request Lifecycle actions run only when the current state allows them.
- Notification read state is tracked at the user level.
- Delivery attempts are logged to stdout and are not stored as delivery-attempt records.
- Notifications remain visible while unread and disappear only after the user marks them read.

## Domain Configuration

The application maintains centralized domain constants in `apps/inventory/config.py`. This ensures consistent behavior across the application and simplifies adjustments to clinical parameters and business rules:

- **Blood Types** (`BLOOD_TYPES`): All valid blood type choices (A+, A-, B+, B-, AB+, AB-, O+, O-) referenced by BloodUnit and BloodRequest models.
- **Low Stock Threshold** (`LOW_STOCK_THRESHOLD`): Units threshold (default: 5) at or below which a blood type triggers a low-stock alert. Configurable via `INVENTORY_LOW_STOCK_THRESHOLD` environment variable.
- **Standard Expiry Days** (`STANDARD_EXPIRY_DAYS`): Days until a blood unit expires after donation (default: 42). Configurable via `INVENTORY_STANDARD_EXPIRY_DAYS` environment variable.
- **Woreda Range** (`WOREDA_MIN`, `WOREDA_MAX`): Valid range for Ethiopian woreda (district) codes (1-20, configurable via `FACILITY_WOREDA_MAX`).
- **API Pagination** (`PAGE_SIZE`): Default page size for paginated endpoints (default: 25, configurable via `API_PAGE_SIZE`).

All constants support environment variable overrides for different deployment environments (dev/staging/prod).
