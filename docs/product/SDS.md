# Software Design Specification

> **This markdown is a condensed summary.** The authoritative design is in
> `docs/SDS.pdf`. Deviations from it (UUID PKs, JWT auth, two-role RBAC matrix,
> FCM-only delivery, per-unit inventory) are recorded in
> `docs/architecture/decisions/` (ADR-0004 … ADR-0007).

## 1. Overview

The backend is a Django and Django REST Framework application that manages Facilities, Users, Blood Inventory, Blood Requests, Dashboard Summaries, and asynchronous Notification Events.

The implementation currently consists of three major domain apps:

- users
- inventory
- notifications

## 2. Architectural Style

- The system follows a layered Django application structure.
- Domain models represent persistent business entities.
- Serializers define API payloads.
- Viewsets and API views expose REST endpoints.
- Permissions enforce role and facility boundaries.
- Transition seams emit Notification Events for asynchronous delivery.
- Scheduled dispatcher jobs process pending Notification Events through channel adapters.
- Management commands handle periodic maintenance tasks such as expired blood removal.

## 3. Core Domain Model

### 3.1 Facility

Facilities represent hospitals, clinics, or blood banks. A facility stores location data and owns both staff users and inventory.

### 3.2 User

The custom user model extends Django’s auth user and adds:

- role
- facility association

Roles are:

- System Administrator
- Facility Representative

### 3.3 Blood Unit

Blood units are stored per facility and blood type with a donated timestamp and expiration date.

### 3.4 Blood Request

Blood Requests connect a requesting Facility to a fulfilling Facility and move through the Blood Request Lifecycle:

- Pending
- Accepted
- Rejected
- In Transit
- Fulfilled
- Cancelled

## 4. Application Components

### 4.1 users app

- Exposes facility and user API endpoints.
- Contains the custom user model and facility model.
- Contains role-based permissions.
- Exposes API-only behavior for user and facility management.

### 4.2 inventory app

- Exposes blood unit inventory endpoints.
- Exposes blood request endpoints and lifecycle actions.
- Exposes dashboard aggregation.
- Provides filters for inventory and request queries.
- Provides the expired blood removal management command.

### 4.3 notifications app

- Stores Notification Event records emitted by Blood Request transition flows.
- Stores Notification Records with user-level read/unread state.
- Dispatches pending Notification Events asynchronously via scheduled management-command execution.
- Uses push and SMS channel adapters for provider-specific delivery behavior.

## 5. Request and Notification Flow

### 5.1 Blood Request Creation

1. A Facility Staff Member submits a Blood Request.
2. The backend assigns the requester’s Facility and the requesting User.
3. The serializer validates that the target Facility has enough stock at request time.
4. The Blood Request is saved in Pending state.
5. A Notification Event is created for the fulfilling Facility.
6. The scheduled notification dispatcher delivers the event asynchronously through push and SMS adapters.

### 5.2 Accept or Reject

1. The fulfilling Facility performs an accept or reject action.
2. The backend verifies the Blood Request is still Pending.
3. Accept deducts inventory atomically from the fulfilling Facility.
4. Reject updates the Blood Request state without inventory movement.
5. A Notification Event is created for the requesting Facility.
6. The scheduled notification dispatcher delivers the event asynchronously through push and SMS adapters.

### 5.3 Ship and Receive

1. Accepted Blood Requests may be marked In Transit.
2. The requesting Facility may then mark the Blood Request as received.
3. Receiving creates inventory at the requesting Facility.
4. The Blood Request moves to Fulfilled.

## 6. Persistence Design

### 6.1 User and Facility Storage

- Facilities are stored as first-class records.
- Users reference a facility through a foreign key.

### 6.2 Inventory Storage

- BloodUnit records store blood type, facility, donated time, and expiration date.

### 6.3 Request Storage

- BloodRequest records store both facilities, the requesting user, requested blood type, quantity, status, and timestamps.

### 6.4 Notification Storage

- Notification persistence is required so Unread Notifications remain visible until explicitly marked read.
- Notification Records track event type, recipient user, read status, and timestamps.
- Delivery attempt details are logged to stdout and are not persisted in phase 1.

## 7. API Design

### 7.1 Public Endpoints

- `/api/v1/facilities/`
- `/api/v1/users/`
- `/api/v1/blood-requests/`
- `/api/v1/facilities/{id}/inventory/`
- `/api/v1/facilities/{id}/inventory-summary/`
- `/api/v1/facilities/{id}/staff/`
- `/api/v1/dashboard/`

### 7.2 Lifecycle Actions

- Accept
- Reject
- Ship
- Receive
- Cancel

## 8. Security and Authorization

- Authenticated users can view facilities and dashboard data.
- Administrators manage users.
- Facility representatives can only mutate inventory for their own facility.
- Request lifecycle actions are constrained to either the fulfilling or requesting facility as appropriate.

## 9. Background Processing

- Notification delivery must occur asynchronously.
- The backend emits Notification Events during request workflows and dispatches them asynchronously through scheduled command execution.
- The backend should only dispatch notification jobs after the underlying transaction is committed.
- Expired blood removal is handled by a management command.

## 10. Testing Strategy

The system can be tested without a mobile client by verifying:

- database state changes
- request state transitions
- inventory deductions and additions
- notification event creation
- unread/read notification visibility rules
- delivery job invocation to push and SMS providers

Integration tests that cover end-to-end API and async dispatch flow are planned for the phase-finalization testing pass.
