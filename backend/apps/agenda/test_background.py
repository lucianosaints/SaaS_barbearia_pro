from threading import Event
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from apps.agenda.background import enqueue_notification
from apps.agenda.signals import _dispatch_notification


class BackgroundNotificationTests(SimpleTestCase):
    @override_settings(AGENDA_NOTIFICATIONS_ASYNC=True)
    @patch('apps.agenda.signals.enqueue_notification')
    def test_production_dispatch_enqueues_callback(self, mocked_enqueue):
        callback = Mock()

        _dispatch_notification(callback)

        mocked_enqueue.assert_called_once_with(callback)
        callback.assert_not_called()

    def test_enqueue_does_not_wait_for_notification_to_finish(self):
        started = Event()
        release = Event()
        finished = Event()

        def slow_notification():
            started.set()
            release.wait(timeout=2)
            finished.set()

        enqueue_notification(slow_notification)

        self.assertTrue(started.wait(timeout=1))
        self.assertFalse(finished.is_set())
        release.set()
        self.assertTrue(finished.wait(timeout=1))
