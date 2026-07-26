# ADR 0009: Web client support, CORS, and token security hardening

Date: 2026-07-26

Status: Accepted

## Context

The SRS (VBB-DC-001) specified a mobile client only, and the backend's auth
posture reflected that: no CORS support (a native app needs none), refresh
tokens rotated but old ones stayed valid until expiry, no logout endpoint
(clients simply discarded tokens), and no API rate limiting.

An owner decision of 2026-07-26 — post-dating the SRS/SDS PDFs — adds a **web
client** alongside the mobile client (see `docs/CONTEXT.md`). A browser-based
client changes the threat model:

- The browser enforces the same-origin policy, so the API must grant the web
  client's origin via CORS — and a careless grant (wildcard origins) would
  extend to any site.
- Tokens held in a browser are more exposed (XSS, extension access, shared
  machines) than in a mobile keystore, so a leaked refresh token — valid for
  7 days per VBB-FUN-UM-007 — is a larger liability, and users need a real
  logout that revokes it server-side.
- A public browser-reachable login endpoint invites credential stuffing;
  SRS NFR-SEC lockout requirements assumed the mobile client's UI throttling,
  which a scripted attacker bypasses.

## Decision

Four changes, all in this repository:

1. **CORS with explicit origins** (`django-cors-headers`).
   `CORS_ALLOWED_ORIGINS` is env-driven and defaults to empty; dev settings
   default to the Vite dev server (`http://localhost:5173`).
   `CORS_ALLOW_ALL_ORIGINS` is never enabled. `CorsMiddleware` sits above
   `CommonMiddleware` per the package's documentation. `FRONTEND_URL` is now
   env-driven in base settings (prod no longer overrides it separately).
2. **Refresh-token rotation with blacklisting.**
   `rest_framework_simplejwt.token_blacklist` is installed and
   `BLACKLIST_AFTER_ROTATION=True`: every refresh both rotates the token and
   blacklists the used one, so a stolen refresh token dies as soon as the
   legitimate client refreshes.
3. **Logout endpoint** (`POST /api/v1/auth/logout/`, authenticated). Accepts
   `{"refresh": "<token>"}` and blacklists it; returns 205 on success, 400 on
   a missing/invalid token. The access token remains valid until expiry (≤30
   minutes) — acceptable given the short lifetime, and it avoids per-request
   blacklist lookups on access tokens.
4. **API throttling.** Default DRF throttles: anonymous 60/min, authenticated
   240/min, both env-overridable (`THROTTLE_ANON_RATE`, `THROTTLE_USER_RATE`).
   The login view gets a dedicated scoped throttle, `auth` at 10/min
   (`THROTTLE_AUTH_RATE`), so credential stuffing is rate-limited
   independently of general anonymous traffic.

## Consequences

- The web client works against the API from an explicitly allowed origin;
  nothing is opened to other origins.
- Logout is now a server-side revocation, not just client-side token disposal
  — a stolen refresh token can be invalidated immediately.
- The blacklist adds two tables (`token_blacklist` migrations ship with
  simplejwt) and one DB lookup per refresh — negligible at current scale. The
  `OutstandingToken` table grows with logins; pruning via the package's
  `flushexpiredtokens` command can be scheduled when volume warrants it.
- Throttle state lives in the default cache (per-process locmem today). Rates
  are enforced per worker process until a shared cache (e.g. Redis) is
  configured — good enough as a brake on credential stuffing, not a hard
  global guarantee.
- Test settings raise the throttle rates so the suite's rapid-fire requests
  don't trip them; throttling behaviour itself is covered by dedicated tests
  using `override_settings`.

## Alternatives considered

- **Cookie-based sessions for the web client:** avoids storing JWTs in the
  browser but forks the auth model per client and reintroduces CSRF surface;
  one JWT flow for both clients keeps the API uniform (ADR-0005).
- **Blacklisting access tokens on logout too:** a per-request DB check on
  every API call to shave at most 30 minutes off a stolen access token's
  life — poor trade at this risk level.
- **Lockout counters per account (SRS-style):** deferred; scoped throttling
  addresses the scripted-attack case without introducing an
  account-denial-of-service vector (an attacker locking out a victim by
  spamming wrong passwords).
