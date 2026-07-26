# Runbook: Notification Dispatcher

The dispatcher is the Django management command
**`python manage.py dispatch_notifications`**
(`backend/apps/notifications/management/commands/dispatch_notifications.py`).
It is the asynchronous seam described in ADR-0002: API request handlers only
*emit* `NotificationEvent` rows; this command, run on a schedule, does the
actual delivery.

## How it works

1. Selects up to **1000** pending events (`dispatched=False`), oldest first.
2. For each event, `DeliveryService.deliver_event()`:
   - resolves recipients — all users of the event's facility, or **all users**
     if the event has no facility (e.g. system-wide alerts);
   - creates a `NotificationRecord` per recipient (this is what
     `GET /api/v1/notifications/` serves and where read/unread state lives);
   - sends through each configured channel adapter.
3. Marks the event `dispatched=True`.

Adapters are chosen by the `NOTIFICATION_ADAPTERS` env var (comma-separated;
default `stdout`):

- `stdout` — logs the delivery line only (SRS 3.5.7 visibility).
- `fcm` (alias `push`) — Firebase Cloud Messaging. Requires
  `GOOGLE_APPLICATION_CREDENTIALS` or `FIREBASE_CREDENTIALS` pointing at a
  service-account JSON **and** a `device_token` on the recipient; otherwise it
  logs a `[fcm:simulated]` line instead of sending. See ADR-0007.

## Scheduling in production

**As of 2026-07-26, `render.yaml` defines no cron job or worker for the
dispatcher — it is not scheduled in production.** Until that is added, pending
events accumulate (`dispatched=False`) and nothing is delivered unless the
command is run by hand.

Run it manually from the Render service **Shell** tab:

```sh
python manage.py dispatch_notifications
```

Recommended schedule: **every minute** (ADR-0002's stated granularity — the
dispatch interval is the delivery latency, and blood requests are
time-critical). The natural fix is a `cron` service in `render.yaml` reusing
the same image and env vars, e.g.:

```yaml
  - type: cron
    name: vbb-notification-dispatcher
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    schedule: "* * * * *"
    dockerCommand: python manage.py dispatch_notifications
```

(Requires the same `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `DATABASE_URL`, and
notification env vars as the web service. Note Render cron jobs are a paid
feature; the fallback on the free tier is invoking the command via the web
service shell or an external scheduler hitting a job runner.)

The related `remove_expired_blood` command (inventory app) is also designed for
scheduled execution and is likewise unscheduled today; a daily run is
sufficient for it.

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
