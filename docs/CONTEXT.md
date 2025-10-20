# VBB Backend Context

## Product Scope

- The current repository is the backend API for the Virtual Blood Bank product.
- The mobile client is planned future work and is out of scope for the current release.
- The product should be described as one system with two components: a mobile client and a backend API, but only the backend is being finalized now.

## Canonical Terms

- Facility: A hospital, clinic, or blood bank that can hold inventory and participate in requests.
- User: An authenticated account tied to a facility or system administration role.
- System Administrator: A user with platform-wide administrative access.
- Facility Representative: A user who manages inventory and requests for a specific facility.
- Facility Staff Member: Any authenticated user attached to a facility.
- Blood Unit: One unit of blood stored at a facility with a blood type and expiration date.
- Blood Request: A request for one or more blood units from one facility to another.
- Blood Request Lifecycle: The allowed states and transitions for a blood request.
- Notification Event: A backend event that may produce push and SMS notifications.
- Notification Record: A persisted notification entry used to track delivery state and read state.
- Unread Notification: A notification that remains visible to the user until they explicitly mark it as read.
- Notification Dispatcher: A scheduled backend process that reads pending Notification Events and delivers them asynchronously.
- Delivery Channel Adapter: A channel-specific implementation that sends a notification to one channel (push or SMS).
- Dashboard Summary: The facility-level overview of inventory, incoming requests, outgoing requests, and low-stock alerts.
- Low Stock Alert: A warning that a blood type's inventory has fallen to or below the configured threshold.

## Notification Rules

- Notifications are delivered asynchronously.
- One backend notification event fans out to two delivery channels: push and SMS.
- Blood Request Lifecycle actions are performed only when the current state allows them.
- Notification read state is tracked at the user level.
- Delivery attempts are logged to stdout and are not stored as delivery-attempt records.
- Notifications remain visible while unread.
- Notifications disappear from the user-visible list only after the user explicitly marks them as read.

## Domain Configuration

The application maintains centralized domain constants in `apps/inventory/config.py`. This ensures consistent behavior across the application and simplifies adjustments to clinical parameters and business rules:

- **Blood Types** (`BLOOD_TYPES`): All valid blood type choices (A+, A-, B+, B-, AB+, AB-, O+, O-) referenced by BloodUnit and BloodRequest models.
- **Low Stock Threshold** (`LOW_STOCK_THRESHOLD`): Units threshold (default: 5) at or below which a blood type triggers a low-stock alert. Configurable via `INVENTORY_LOW_STOCK_THRESHOLD` environment variable.
- **Standard Expiry Days** (`STANDARD_EXPIRY_DAYS`): Days until a blood unit expires after donation (default: 42). Configurable via `INVENTORY_STANDARD_EXPIRY_DAYS` environment variable.
- **Woreda Range** (`WOREDA_MIN`, `WOREDA_MAX`): Valid range for Ethiopian woreda (district) codes (1-20, configurable via `FACILITY_WOREDA_MAX`).
- **API Pagination** (`PAGE_SIZE`): Default page size for paginated endpoints (default: 25, configurable via `API_PAGE_SIZE`).

All constants support environment variable overrides for different deployment environments (dev/staging/prod).
