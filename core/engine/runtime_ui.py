import threading

from PySide6.QtCore import QObject, Signal, Qt, QCoreApplication


class MacroRunnerUiBridge(QObject):
    message_requested = Signal(str, str, bool)
    invoke_requested = Signal(object, object, object)

    def __init__(self, runtime, parent=None):
        super().__init__(parent)
        self.runtime = runtime
        self._message_events = set()
        self._invoke_events = set()
        self._lock = threading.Lock()
        self.invoke_requested.connect(
            self._invoke_on_ui_thread,
            Qt.ConnectionType.QueuedConnection,
        )

        application = QCoreApplication.instance()
        if application is not None and self.parent() is None:
            self.moveToThread(application.thread())

    def show_message(self, title, message, wait=False):
        title = str(title or "Message")
        message = str(message or "")

        if not wait:
            self.message_requested.emit(title, message, False)
            return

        event = threading.Event()

        with self._lock:
            self._message_events.add(event)

        self.message_requested.emit(title, message, True)
        event.wait()

        with self._lock:
            self._message_events.discard(event)

    def run(self, callback, *args, **kwargs):
        if not callable(callback):
            raise RuntimeError("UI callback is not callable")

        event = threading.Event()
        state = {
            "result": None,
            "error": None,
        }

        with self._lock:
            self._invoke_events.add(event)

        self.invoke_requested.emit(callback, (args, kwargs), (event, state))
        event.wait()

        with self._lock:
            self._invoke_events.discard(event)

        if state["error"] is not None:
            raise state["error"]

        return state["result"]

    def run_safe(self, callback, *args, **kwargs):
        try:
            return self.run(callback, *args, **kwargs)
        except Exception:
            return None

    def notify_message_closed(self):
        with self._lock:
            events = tuple(self._message_events)
            self._message_events.clear()

        for event in events:
            event.set()

    def cancel_pending(self):
        with self._lock:
            events = tuple(self._message_events) + tuple(self._invoke_events)
            self._message_events.clear()
            self._invoke_events.clear()

        for event in events:
            event.set()

    def _invoke_on_ui_thread(self, callback, payload, state_payload):
        args, kwargs = payload
        event, state = state_payload

        try:
            state["result"] = callback(*args, **kwargs)
        except Exception as error:
            state["error"] = error
        finally:
            event.set()
