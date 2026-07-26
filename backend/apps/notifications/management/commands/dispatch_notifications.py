"""Dispatch pending notification events (ADR-0002 scheduled dispatcher).

Two modes:

- One-shot (default): process one batch and exit. Cron-friendly.
- Worker (``--loop``): run forever, one batch per interval, until SIGTERM or
  SIGINT. Intended for a long-running worker process (see
  docs/runbooks/notification-dispatcher.md).

Delivery semantics — **at-least-once** for pushes, exactly-once for in-app
records: each event is processed inside its own transaction with a
``select_for_update(skip_locked=True)`` claim, so the ``NotificationRecord``
rows and the ``dispatched=True`` flag commit atomically. A crash mid-event
rolls the records back and the event is retried on the next run, which may
re-send the (already fired) push notifications — duplicates are possible,
lost events are not. The row lock also makes concurrent dispatchers safe:
two workers can never process the same event at once.
"""

import logging
import signal
import threading

from django.core.management.base import BaseCommand
from django.db import transaction

from notifications.delivery import DeliveryService
from notifications.models import NotificationEvent

logger = logging.getLogger(__name__)

#: Maximum number of events processed per batch/cycle.
BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Dispatch pending NotificationEvent rows to users (scheduled dispatcher)."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set by SIGTERM/SIGINT in --loop mode; tests may set it directly.
        self.stop_event = threading.Event()

    def add_arguments(self, parser):
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Run continuously, dispatching one batch per interval, until "
            "SIGTERM/SIGINT (graceful: the in-flight batch finishes first).",
        )
        parser.add_argument(
            "--interval",
            type=float,
            default=60.0,
            metavar="N",
            help="Seconds to sleep between dispatch cycles in --loop mode "
            "(default: 60).",
        )
        parser.add_argument(
            "--max-cycles",
            type=int,
            default=None,
            metavar="N",
            help="Exit after N cycles in --loop mode (mainly for testing).",
        )

    def handle(self, *args, **options):
        self.service = DeliveryService()
        if options["loop"]:
            self._run_loop(
                interval=options["interval"], max_cycles=options["max_cycles"]
            )
            return

        events, records = self._dispatch_batch()
        if events == 0:
            self.stdout.write("No pending notification events found.")
            return
        self.stdout.write(
            f"Dispatched {records} notification records from {events} events."
        )

    # -- one dispatch pass ---------------------------------------------------

    def _dispatch_batch(self) -> tuple[int, int]:
        """Dispatch up to BATCH_SIZE pending events; return (events, records).

        Each event is claimed and delivered inside its own transaction so a
        crash cannot leave an event half-delivered (records without the
        ``dispatched`` flag, or vice versa). See the module docstring for the
        resulting at-least-once semantics.
        """
        pending_ids = list(
            NotificationEvent.objects.filter(dispatched=False)
            .order_by("created_at")
            .values_list("id", flat=True)[:BATCH_SIZE]
        )
        events = records = 0
        for event_id in pending_ids:
            with transaction.atomic():
                event = (
                    NotificationEvent.objects.select_for_update(skip_locked=True)
                    .filter(id=event_id, dispatched=False)
                    .first()
                )
                if event is None:
                    # Claimed (or finished) by a concurrent dispatcher.
                    continue
                created = self.service.deliver_event(event)
            self.stdout.write(
                f"Dispatched {created} records for event {event.id} "
                f"({event.event_type})"
            )
            events += 1
            records += created
        return events, records

    # -- worker mode ---------------------------------------------------------

    def _run_loop(self, *, interval: float, max_cycles: int | None) -> None:
        previous_handlers = self._install_signal_handlers()
        logger.info("Notification dispatcher worker started (interval=%ss)", interval)
        cycles = 0
        try:
            while not self.stop_event.is_set():
                try:
                    events, records = self._dispatch_batch()
                    logger.info(
                        "Dispatch cycle %s complete: %s event(s), %s record(s)",
                        cycles + 1,
                        events,
                        records,
                    )
                except Exception:
                    # Transient DB/FCM errors must not kill the worker; the
                    # batch is retried on the next cycle (at-least-once).
                    logger.exception(
                        "Dispatch cycle %s failed; retrying next interval",
                        cycles + 1,
                    )
                cycles += 1
                if max_cycles is not None and cycles >= max_cycles:
                    break
                # Event.wait (not time.sleep) so SIGTERM/SIGINT interrupts
                # the sleep immediately instead of after up to `interval`s.
                self.stop_event.wait(interval)
        finally:
            self._restore_signal_handlers(previous_handlers)
        logger.info("Notification dispatcher worker stopped after %s cycle(s)", cycles)

    def _install_signal_handlers(self) -> dict:
        """Route SIGTERM/SIGINT to a graceful stop; return previous handlers.

        Containers receive SIGTERM on deploys/scale-down: we finish the
        in-flight batch, then exit 0.
        """

        def _request_stop(signum, frame):
            logger.info(
                "Received %s; finishing current batch, then exiting",
                signal.Signals(signum).name,
            )
            self.stop_event.set()

        previous = {}
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                previous[sig] = signal.signal(sig, _request_stop)
            except ValueError:  # pragma: no cover - not in the main thread
                pass
        return previous

    def _restore_signal_handlers(self, previous: dict) -> None:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
