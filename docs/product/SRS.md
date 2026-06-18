# Software Requirements Specification

> **This markdown is a condensed summary.** The authoritative requirements are in
> `docs/SRS.pdf` (and `docs/SDS.pdf` for design). The backend implements the PDF
> scope; design deviations are recorded in `docs/architecture/decisions/`.

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements for the Virtual Blood Bank backend system. The backend supports inventory management, Blood Request Lifecycle actions, user authentication, and asynchronous notifications for operational events.

### 1.2 Scope

The current release covers the backend API only. The mobile client is a planned future component and is not part of the current delivery baseline.

### 1.3 Product Perspective

The full product is intended to consist of two components:

- A mobile client used by healthcare workers.
- A backend system that handles authentication, inventory, Blood Request Lifecycle actions, notifications, and administrative workflows.

This specification finalizes the backend now and treats the mobile client as future scope.

### 1.4 Users

- System Administrator
- Facility Representative
- Facility Staff Member

## 2. Overall Description

### 2.1 User Needs

- Administrators need to manage users and facilities.
- Facility staff need to view inventory by facility and blood type.
- Facility Staff Members need to create, accept, reject, ship, receive, and cancel Blood Requests according to role and request state.
- Users need to receive notifications for important request events and low-stock conditions.

### 2.2 Assumptions and Dependencies

- The backend uses third-party services for push notifications and SMS delivery.
- Notification delivery is asynchronous.
- Asynchronous notification delivery is implemented through scheduled backend dispatch jobs in the current release baseline.
- The system stores notifications internally so unread items remain visible until explicitly marked read.
- Expired blood units are removed from inventory by backend maintenance processes.

## 3. Functional Requirements

### 3.1 Authentication and Account Management

- The system shall allow users to authenticate against a backend account.
- The system shall associate each non-administrative user with a facility.
- The system shall support facility-based access control.

### 3.2 Facility Management

- The system shall allow authenticated users to view facilities.
- The system shall allow administrators to manage facilities and users.

### 3.3 Inventory Management

- The system shall store blood units by blood type, facility, and expiration date.
- The system shall allow a facility representative to add blood units to their own facility inventory.
- The system shall allow authenticated users to view facility inventory.
- The system shall exclude expired blood units from active inventory use.

### 3.4 Blood Request Management

- The system shall allow authenticated users to create blood requests for another facility.
- The system shall prevent users from requesting blood from their own facility.
- The system shall support the following Blood Request states: Pending, Accepted, Rejected, In Transit, Fulfilled, and Cancelled.
- The system shall allow the fulfilling facility to accept, reject, or ship a request.
- The system shall allow the requesting facility to receive or cancel a request when the request state allows it.
- The system shall update inventory when a request is accepted or received.

### 3.5 Notifications

- The system shall generate a Notification Event when a Blood Request is created.
- The system shall generate a Notification Event when a Blood Request is accepted or rejected.
- The system shall deliver each notification event through push and SMS channels.
- The system shall perform notification delivery asynchronously.
- The system shall persist Notification Records internally so Unread Notifications remain visible to users.
- The system shall track Notification Record read status at the user level.
- The system shall log notification delivery attempts to stdout.
- The system shall hide Notification Records from the user-visible list only after the user explicitly marks them as read.

### 3.6 Dashboard

- The system shall provide a Dashboard Summary for the authenticated user’s Facility.
- The dashboard shall include inventory summary, low-stock alerts, incoming request counts, and outgoing request counts.

## 4. External Interface Requirements

### 4.1 API Interface

- The system shall expose REST API endpoints for facilities, users, inventory, blood requests, and dashboard data.
- The system shall support nested facility inventory endpoints.

### 4.2 Third-Party Services

- The system shall integrate with third-party push notification providers.
- The system shall integrate with third-party SMS providers.

## 5. Nonfunctional Requirements

- The system shall preserve request integrity when updating blood inventory and blood request state.
- The system shall avoid sending notifications for transactions that do not complete successfully.
- The system shall support role-based authorization for all sensitive actions.
- The system shall remain testable without a mobile client by verifying backend records, Blood Request state transitions, and Notification Record visibility.

## 6. Out of Scope for Current Release

- Mobile client implementation.
- Direct user-managed push token enrollment flows in the mobile app.
- Manual notification composition by end users.
- Queue-based notification infrastructure (for example Celery) in phase 1.
- HTML signup/testing pages in the backend service.

## 7. Delivery Phases

### 7.1 Phase 1: API Core and Async Dispatch Baseline

- Finalize inventory and Blood Request lifecycle APIs.
- Implement Notification Event emission and scheduled async dispatch.
- Implement Notification Record read/unread behavior at user level.
- Remove backend HTML signup/testing views.

### 7.2 Phase 2: Reliability and Scale Enhancements

- Add queue-backed worker infrastructure if needed.
- Add advanced retry policy and dead-letter handling if needed.
- Add broader integration coverage and load-oriented hardening.
