import logging
from queue import Queue
from threading import Lock, Thread

from django.db import close_old_connections


logger = logging.getLogger(__name__)

_notification_queue = Queue()
_worker_lock = Lock()
_worker = None


def _process_notifications() -> None:
    while True:
        callback = _notification_queue.get()
        try:
            close_old_connections()
            callback()
        except Exception:
            logger.exception('Falha inesperada ao processar uma notificação de agenda.')
        finally:
            close_old_connections()
            _notification_queue.task_done()


def _ensure_worker() -> None:
    global _worker
    with _worker_lock:
        if _worker is None or not _worker.is_alive():
            _worker = Thread(
                target=_process_notifications,
                name='agenda-notifications',
                daemon=True,
            )
            _worker.start()


def enqueue_notification(callback) -> None:
    """Agenda uma notificação sem bloquear a resposta HTTP do agendamento."""
    _ensure_worker()
    _notification_queue.put(callback)
