# ADR 0007: FCM push delivery; drop SMS

Date: 2026-06-17

Status: Accepted

## Context

The SRS describes two notification channels — push (FCM/APNs) and SMS via a
third-party gateway. The SDS (§1.3) explicitly records SMS as a contingency:
"if a suitable SMS gateway [is unavailable] ... the design will be modified to
enhance ... push notifications." The project has no budget for paid providers.

## Decision

- Deliver notifications over **Firebase Cloud Messaging** only. FCM is free and
  reaches both Android and iOS, so a separate APNs integration is unnecessary.
- **Drop the SMS channel** per the SDS contingency.
- `FcmAdapter` initializes Firebase from `GOOGLE_APPLICATION_CREDENTIALS` /
  `FIREBASE_CREDENTIALS` and targets each user's `device_token`. Without
  credentials or a token it logs a simulated delivery, so the asynchronous
  dispatch pipeline (ADR-0002) works in development without paid infrastructure.
- Delivery attempts are logged to stdout (SRS 3.5.7); notification `message`
  bodies honour the SDS 4.8 length bounds (10–500 chars).

## Consequences

- One free push channel; no recurring provider cost.
- Phone-based password reset (which would need SMS) is out of scope.
- Real FCM delivery activates by supplying Firebase credentials — no code change.
