# Runbook: Notification Dispatcher

The dispatcher is the Django management command
**`python manage.py dispatch_notifications`**
(`backend/apps/notifications/management/commands/dispatch_notifications.py`).
It is the asynchronous seam described in ADR-0002: API request handlers only
*emit* `NotificationEvent` rows; this command, run on a schedule, does the
actual delivery.

## How it works

1. Selects up to **1000** pending events (`dispatched=False`), oldest first.
2. For each event, inside its own transaction (with a
   `select_for_update(skip_locked=True)` claim, so concurrent dispatchers
   never process the same event twice), `DeliveryService.deliver_event()`:
   - resolves recipients — all users of the event's facility, or **all users**
     if the event has no facility (e.g. system-wide alerts);
   - creates a `NotificationRecord` per recipient (this is what
     `GET /api/v1/notifications/` serves and where read/unread state lives);
   - sends through each configured channel adapter.
3. Marks the event `dispatched=True` — committed atomically with the records.

**Delivery semantics: at-least-once for pushes, exactly-once for in-app
records.** Because the records and the `dispatched` flag commit in one
per-event transaction, a crash mid-event rolls everything for that event back
and it is retried on the next run. That retry may re-fire push notifications
that already went out before the crash (pushes are external side effects and
cannot be rolled back), so duplicates are possible — but events are never
lost, and `NotificationRecord` rows are never duplicated.

Adapters are chosen by the `NOTIFICATION_ADAPTERS` env var (comma-separated;
default `stdout`):

- `stdout` — logs the delivery line only (SRS 3.5.7 visibility).
- `fcm` (alias `push`) — Firebase Cloud Messaging. Requires
  `GOOGLE_APPLICATION_CREDENTIALS` or `FIREBASE_CREDENTIALS` pointing at a
  service-account JSON **and** a `device_token` on the recipient; otherwise it
  logs a `[fcm:simulated]` line instead of sending. See ADR-0007.

## Worker mode

The command also runs as a long-lived worker:

```sh
python manage.py dispatch_notifications --loop            # every 60s (default)
python manage.py dispatch_notifications --loop --interval 30
```

- Each cycle dispatches one batch (same logic as one-shot), then sleeps
  `--interval` seconds (default 60). Cycle summaries are logged at INFO
  (`Dispatch cycle N complete: X event(s), Y record(s)`).
- **Graceful shutdown**: on SIGTERM or SIGINT the worker finishes the
  in-flight batch, then exits 0 — safe for container deploys, which send
  SIGTERM. The between-cycle sleep is interruptible, so shutdown is prompt.
- **Crash resilience**: an exception in one cycle (transient DB or FCM
  failure) is logged (`Dispatch cycle N failed; retrying next interval`) and
  the loop continues; the process does not die.
- `--max-cycles N` exits after N cycles (mainly for testing).
- Local dev: the optional `worker` service in `backend/compose.yaml` runs
  this mode (`docker compose up worker`).

## Scheduling in production

**As of 2026-07-26, `render.yaml` ships a ready-to-enable worker block for
the dispatcher, but it is commented out — the dispatcher is not scheduled in
production.** Background workers (and cron jobs) are paid Render features and
the deployment is currently free-tier only; the blueprint spec offers no
suspend/disable flag, so an active block would start billing on the next
sync. Until it is enabled, pending events accumulate (`dispatched=False`) and
nothing is delivered unless the command is run by hand.

Run it manually from the Render service **Shell** tab:

```sh
python manage.py dispatch_notifications
```

**Recommended production path (once infra allows): the worker.** Uncomment
the `vbb-notification-worker` block in `render.yaml` and sync. Loop mode is
preferred over cron because it needs no scheduler, gives steady sub-minute
worst-case latency at the default 60s interval, shuts down gracefully on
deploys, and survives transient failures without an external supervisor.

**Alternative: cron.** The one-shot mode remains the default precisely so a
`cron` service (also paid on Render) can run it instead, e.g.:

```yaml
  - type: cron
    name: vbb-notification-dispatcher
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    schedule: "* * * * *"
    dockerCommand: python manage.py dispatch_notifications
```

Every minute matches ADR-0002's stated granularity — the dispatch interval is
the delivery latency, and blood requests are time-critical. Either variant
requires the same `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DATABASE_URL`, and
notification env vars as the web service. The free-tier fallback remains
invoking the command via the web service shell or an external scheduler
hitting a job runner.

### remove_expired_blood is separate

The related `remove_expired_blood` command (inventory app) is **not** covered
by the notification worker and deliberately has no loop mode: purging expired
units is a naturally daily task, so a scheduled one-shot run is the right
shape for it. Schedule it as a daily cron (e.g. `schedule: "0 3 * * *"` in a
Render cron service, or the host's crontab for self-managed deployments)
running `python manage.py remove_expired_blood`. It is likewise unscheduled
today; until then, run it manually from the service shell.

## Failure modes

| Symptom | Diagnosis | Remedy |
| :--- | :--- | :--- |
| Users report no notifications; `NotificationEvent` rows pile up with `dispatched=False` | Dispatcher not running (no schedule, or cron failing) | Run manually; fix/add the schedule |
| `[fcm:simulated]` lines in logs, no real pushes | Firebase credentials or user `device_token` missing | Set `FIREBASE_CREDENTIALS`/`GOOGLE_APPLICATION_CREDENTIALS`; confirm clients register device tokens; ensure `NOTIFICATION_ADAPTERS` includes `fcm` |
| `FCM send failed for user ...` / `Failed to initialize Firebase app` stack traces | Bad credentials, revoked token, or FCM outage | Check the credential file and Firebase console; stale device tokens fail per-user without blocking others |
| `Adapter ... failed for user ...` warnings | Adapter raised; the send to that user was skipped | The in-app `NotificationRecord` was still created (it's written before the send); investigate the logged exception |
| One run seems to deliver only part of the backlog | Per-run cap of 1000 events | Re-run until "No pending notification events found." |

**Design caveats (ADR-0002/ADR-0007, deliberate phase-1 tradeoffs):** delivery
attempts are logged to **stdout only** — there are no delivery-attempt rows in
the database, so push-delivery history is only as durable as your log
retention. There is also **no retry**: once an event is marked
`dispatched=True`, failed pushes for it are not re-attempted (the in-app record
still exists). Persisted attempts and retry/backoff are Phase 2
(`docs/product/PHASES.md`).

## Verifying delivery

1. **Command output** (stdout → Render Logs): each run prints
   `Dispatched <n> records for event <id> (<type>)` and a final total, or
   `No pending notification events found.`
2. **Database**: in Django admin or shell, confirm the event's
   `dispatched=True` and that `NotificationRecord` rows exist for the expected
   recipients with `delivered_at` set.
3. **API**: as a recipient, `GET /api/v1/notifications/` should list the
   notification (unread until `POST /api/v1/notifications/{id}/mark_read/`).
4. **Push**: check for `NOTIFY ...` (stdout adapter) or absence of
   `[fcm:simulated]` / error lines (FCM adapter) in the logs, and confirm
   receipt on a real device.
