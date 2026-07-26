"""Tests for the dispatch_notifications management command (one-shot + loop)."""

import signal
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from notifications.management.commands.dispatch_notifications import Command
from notifications.models import NotificationEvent, NotificationRecord
from tests.factories import create_facility, create_user


class OneShotModeTests(TestCase):
    """The default (no --loop) mode stays cron-friendly: one batch, then exit."""

    def setUp(self):
        self.facility = create_facility(name="OneShot", region="R", zone="Z", woreda=1)
        self.user = create_user(username="oneshot", facility=self.facility)

    def test_no_pending_events_prints_message(self):
        out = StringIO()
        call_command("dispatch_notifications", stdout=out)
        self.assertIn("No pending notification events found.", out.getvalue())

    def test_dispatches_pending_events_and_marks_them(self):
        ev = NotificationEvent.objects.create(
            event_type="OneShotTest",
            facility=self.facility,
            payload={"message": "Hello there"},
        )
        out = StringIO()
        call_command("dispatch_notifications", stdout=out)

        ev.refresh_from_db()
        self.assertTrue(ev.dispatched)
        self.assertTrue(
            NotificationRecord.objects.filter(event=ev, user=self.user).exists()
        )
        out_value = out.getvalue()
        self.assertIn(f"Dispatched 1 records for event {ev.id}", out_value)
        self.assertIn("Dispatched 1 notification records from 1 events.", out_value)

    def test_already_dispatched_events_are_skipped(self):
        NotificationEvent.objects.create(
            event_type="Done",
            facility=self.facility,
            payload={"message": "Already sent"},
            dispatched=True,
        )
        out = StringIO()
        call_command("dispatch_notifications", stdout=out)
        self.assertIn("No pending notification events found.", out.getvalue())
        self.assertEqual(NotificationRecord.objects.count(), 0)


class LoopModeTests(SimpleTestCase):
    """The --loop worker machinery, with the batch dispatch mocked out."""

    def test_loop_runs_max_cycles_then_exits(self):
        with mock.patch.object(
            Command, "_dispatch_batch", return_value=(0, 0)
        ) as batch:
            call_command("dispatch_notifications", "--loop", interval=0, max_cycles=3)
        self.assertEqual(batch.call_count, 3)

    def test_loop_stops_when_stop_event_is_set(self):
        cmd = Command()

        def fake_batch():
            if fake_batch.calls >= 1:  # stop after the second cycle starts
                cmd.stop_event.set()
            fake_batch.calls += 1
            return (0, 0)

        fake_batch.calls = 0
        with mock.patch.object(cmd, "_dispatch_batch", side_effect=fake_batch):
            cmd._run_loop(interval=0, max_cycles=None)
        self.assertEqual(fake_batch.calls, 2)

    def test_cycle_exception_does_not_kill_the_loop(self):
        with mock.patch.object(
            Command,
            "_dispatch_batch",
            side_effect=[RuntimeError("transient DB error"), (2, 5), (0, 0)],
        ) as batch:
            with self.assertLogs(
                "notifications.management.commands.dispatch_notifications",
                level="ERROR",
            ) as logs:
                call_command(
                    "dispatch_notifications", "--loop", interval=0, max_cycles=3
                )
        self.assertEqual(batch.call_count, 3)
        self.assertTrue(any("Dispatch cycle 1 failed" in line for line in logs.output))

    def test_loop_logs_cycle_summary_at_info(self):
        with mock.patch.object(Command, "_dispatch_batch", return_value=(2, 5)):
            with self.assertLogs(
                "notifications.management.commands.dispatch_notifications",
                level="INFO",
            ) as logs:
                call_command(
                    "dispatch_notifications", "--loop", interval=0, max_cycles=1
                )
        self.assertTrue(any("2 event(s), 5 record(s)" in line for line in logs.output))

    def test_sigterm_sets_stop_event_and_handlers_are_restored(self):
        cmd = Command()
        original_sigterm = signal.getsignal(signal.SIGTERM)
        previous = cmd._install_signal_handlers()
        try:
            handler = signal.getsignal(signal.SIGTERM)
            handler(signal.SIGTERM, None)  # simulate delivery of SIGTERM
            self.assertTrue(cmd.stop_event.is_set())
        finally:
            cmd._restore_signal_handlers(previous)
        self.assertIs(signal.getsignal(signal.SIGTERM), original_sigterm)
