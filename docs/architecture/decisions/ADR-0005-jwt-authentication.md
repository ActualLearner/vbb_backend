# ADR 0005: JWT authentication for the API

Date: 2026-06-17

Status: Accepted

## Context

The SDS (§2.3.3) mandates JWT authentication: on login the server issues a
signed token whose payload carries the user id and role, and the API gateway
validates the token and enforces the permission matrix on every request. The
original backend authenticated the API via django-allauth headless sessions
with social providers (GitHub/Google) that are irrelevant to rural Ethiopian
healthcare workers.

## Decision

Adopt `djangorestframework-simplejwt` as the API authentication mechanism.

- `DEFAULT_AUTHENTICATION_CLASSES` = `JWTAuthentication`, then
  `SessionAuthentication` (so the Django admin and browsable API still work).
- A custom `EmailOrPhoneBackend` lets users authenticate with an email address
  or an Ethiopian phone number (SRS VBB-FUN-UM-004); inactive users are rejected
  (SRS VBB-UC-007 4b).
- The obtain serializer embeds `role`, `facility_id`, `full_name` and
  `must_change_password` claims so the client and gateway avoid extra lookups.
- Access-token lifetime = 30 minutes (maps to the SRS inactivity logout,
  VBB-FUN-UM-005); refresh lifetime = 7 days (maps to "Remember Me",
  VBB-FUN-UM-007).

allauth remains installed for account/email-reset flows but is no longer the API
auth path.

## Consequences

- Stateless, mobile-friendly auth matching the SDS.
- The 30-minute / 7-day token lifetimes implement two SRS requirements directly.
- Email-based password reset is provided by allauth; phone-based reset is
  deferred (it requires an SMS gateway — see ADR-0007).
