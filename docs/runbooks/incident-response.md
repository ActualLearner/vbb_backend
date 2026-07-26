# Runbook: Incident Response

Triage guide for production incidents. Roles are generic: **first responder**
(whoever notices/gets paged — triages and communicates), **operator** (has
Render dashboard access — executes remedies), **maintainer** (code owner —
decides on rollback/hotfix). One person may wear all three hats.

## Where things live

- **Logs:** everything (Django app logs, Gunicorn access/error, management
  command output) goes to **stdout** and is captured by Render → service →
  **Logs** tab. Log level is `DJANGO_LOG_LEVEL` (default `INFO`). There is no
  external log aggregator; logs are only as durable as Render's retention.
- **Database:** Render managed Postgres (`vbb-db`). Connection info and
  point-in-time recovery are in the database's dashboard page.
- **Health check:** `GET /healthz/` — no auth, no DB access. It proves the
  Django process is up, **not** that the DB is reachable.
- **Deploys/rollback:** see [deploy.md](deploy.md).

## First 5 minutes (any incident)

1. Confirm impact: `curl -s https://<service>.onrender.com/healthz/` and one
   authenticated API call.
2. Check Render **status** page and the service **Events** tab — was there a
   deploy, restart, or platform incident just before symptoms started?
3. Open the **Logs** tab and scan for tracebacks around the incident window.
4. Note the timeline as you go; blood requests are time-critical, so if the
   outage blocks live requests, facilities fall back to their manual
   (phone-based) process — communicate that early.

## API down / 5xx

1. `/healthz/` failing → the process isn't serving. Check Events for a crashed
   deploy or OOM restart; check logs for start-up tracebacks (bad env var,
   failed migration — `start.sh` exits on migration failure).
2. `/healthz/` OK but API routes 5xx → application error. Find the traceback in
   the logs; if it started with a deploy, roll back (see deploy.md) and open an
   issue with the traceback.
3. `/healthz/` OK but API routes 400 → almost always `ALLOWED_HOSTS` /
   `CSRF_TRUSTED_ORIGINS` after a domain change.
4. Slow but not down → check DB (below); on the free plan also consider cold
   starts and plan limits.

## Database issues

1. Symptoms: 500s with `OperationalError` / `could not connect`, or uniform
   slowness.
2. Check the `vbb-db` dashboard: status, storage (a full free-tier disk goes
   read-only), connection count (`CONN_MAX_AGE=600` keeps connections
   persistent; too many web workers can exhaust free-tier connection limits).
3. Verify `DATABASE_URL` on the web service matches the database's current
   connection string (it can change after a database recreate).
4. For data damage (bad migration, accidental delete): stop writes if possible,
   then use Render Postgres recovery/backups. Escalate to the maintainer before
   any restore — restores lose everything after the restore point.

## Auth failures

1. **Everyone** fails to log in → check logs for tracebacks on
   `POST /api/v1/auth/login/`; a rotated/changed `SECRET_KEY` invalidates all
   existing JWTs and sessions at once (users must log in again — that alone
   isn't an outage, but a *wrong* key or missing env var is).
2. **One user** fails → expired access token (30-minute lifetime; client should
   refresh — refresh tokens last 7 days), deactivated account, or a
   newly-provisioned user who must call `change-password` first (other
   endpoints stay locked until they do).
3. **403s rather than 401s** → role/permission matrix, not auth. Verify the
   user's role and facility against the action (ADR-0008): SUPPLY manages own
   stock and fulfills incoming requests; CLINICIAN creates/cancels/receives;
   ADMIN performs no clinical actions.
4. CSRF errors from browser clients → `CSRF_TRUSTED_ORIGINS` (see deploy.md).

## Notification backlog

Symptom: users stop receiving notifications; `NotificationEvent` rows
accumulate with `dispatched=False`.

1. Remember the current state: **the dispatcher is not scheduled in
   production** — see [notification-dispatcher.md](notification-dispatcher.md).
   A backlog usually just means nobody has run it.
2. Run `python manage.py dispatch_notifications` from the service shell;
   repeat until it reports no pending events (1000-event cap per run).
3. If runs succeed but pushes don't arrive, follow the failure-mode table in
   the dispatcher runbook (FCM credentials, device tokens, adapter config).
4. Delivery attempts exist only in stdout logs (no DB records), so for "did
   user X get notified?" questions, check `NotificationRecord` rows and the
   log lines from the relevant run.

## After the incident

1. Write a short timeline (detection → diagnosis → remedy) while it's fresh.
2. File issues for the root cause and for any gap that slowed you down
   (missing alerting, missing runbook step).
3. If the incident revealed a design decision worth revisiting (e.g. no
   delivery-attempt records, no dispatcher schedule), record it against the
   relevant ADR or Phase-2 items in `docs/product/PHASES.md`.
