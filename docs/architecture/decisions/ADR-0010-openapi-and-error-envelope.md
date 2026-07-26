# ADR 0010: OpenAPI schema and standardized error envelope

Date: 2026-07-26

Status: Accepted

## Context

The API contract lives in a hand-written document (`docs/api/API.md`) that has
already drifted from the code more than once. Two clients — the mobile app and
the planned web client (ADR-0009) — now consume the API, and each team needs a
reliable, machine-readable contract to generate typed clients from.

Error responses were also inconsistent: DRF's default `{"field": ["msg"]}` /
`{"detail": "..."}` shapes coexisted with an ad-hoc `{"error": "..."}` body for
blood-request lifecycle transitions, so clients had to special-case error
parsing per endpoint.

## Decision

- Generate an **OpenAPI 3 schema** with `drf-spectacular`, served at
  `/api/schema/`, with Swagger UI at `/api/docs/`. Both are public
  (`AllowAny`): the schema is not sensitive and the client teams need it
  without credentials. Swagger UI assets come from
  `drf-spectacular[sidecar]`, so the docs work offline — no CDN dependency
  (relevant for rural connectivity).
- Standardize every 4xx/5xx body with `drf-standardized-errors`:

  ```json
  {
    "type": "validation_error",
    "errors": [{ "code": "invalid", "detail": "...", "attr": "field" }]
  }
  ```

  Its `AutoSchema` (layered on drf-spectacular's) documents these error
  responses per operation, and its enum postprocessing hook plus
  `ENUM_NAME_OVERRIDES` keep dynamically generated error-code enums from
  colliding.
- Lifecycle transition failures now raise `ValidationError` instead of
  returning `{"error": "..."}`, so they flow through the same envelope.
- `status` / `from_status` / `to_status` share one named
  `BloodRequestStatusEnum` component instead of three colliding enums.

## Consequences

- **Breaking change** to all error bodies. Acceptable pre-1.0: neither client
  has shipped, and both teams asked for the envelope before writing their
  error handling.
- Clients generate typed API bindings from `/api/schema/`; the schema cannot
  drift from the code. `API.md` remains as narrative documentation, but where
  they disagree the generated schema wins.
- `manage.py spectacular --validate` runs clean; keeping it that way is now
  part of the definition of done for API changes.
