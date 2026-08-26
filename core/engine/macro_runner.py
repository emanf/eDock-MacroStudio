from PySide6.QtCore import QObject, QThread, Signal, Qt, Slot

from .automation import pyautogui_call
from .macro_executor import MacroExecutor
from .runtime_helpers import RuntimeHelpers
from .runtime_ui import MacroRunnerUiBridge
from .runtime_variables import RuntimeVariables
from .runtime_os_helpers import get_os_helper


class MacroRunnerWorker(QObject):
    finished = Signal()
    failed = Signal(str)
    step_changed = Signal(int)
    message = Signal(str, str, bool)
    macro_group_started = Signal(str)
    macro_group_finished = Signal(str)

    def __init__(
        self,
        items,
        registry,
        group_library=None,
        group_titles=None,
        loop_count=1,
        speed=1.0,
        delay_ms=0,
        max_depth=10,
        context=None,
        initial_variables=None,
        background_macro_starter=None,
    ):
        super().__init__()
        self.registry = registry
        self.speed = max(0.05, float(speed or 1.0))
        self.context = context
        self.variables = {}
        self.initial_variables = list(initial_variables or [])
        self.background_macro_starter = (
            background_macro_starter
            if callable(background_macro_starter)
            else None
        )
        self.vars = RuntimeVariables(self)
        self.ui = MacroRunnerUiBridge(self)
        self.helper = RuntimeHelpers(self)
        self.os_helpers = get_os_helper(self)
        self.global_hotkey_listeners = {}
        self.global_timers = {}
        self.ui.message_requested.connect(
            self.emit_message,
            Qt.ConnectionType.DirectConnection,
        )

        self.executor = MacroExecutor(
            items=items,
            registry=registry,
            runtime=self,
            group_library=group_library,
            group_titles=group_titles,
            loop_count=loop_count,
            delay_ms=delay_ms,
            max_depth=max_depth,
            on_step=self.step_changed.emit,
            on_group_started=self.macro_group_started.emit,
            on_group_finished=self.macro_group_finished.emit,
        )

        self.initialize_variables()

    @property
    def stopped(self):
        return self.executor.stopped

    @property
    def paused(self):
        return self.executor.paused

    @property
    def items(self):
        return self.executor.items

    @Slot(str, str, bool)
    def emit_message(self, title, message, wait):
        self.message.emit(title, message, wait)

    def initialize_variables(self):
        self.variables = {}

        for variable in self.initial_variables:
            if not isinstance(variable, dict):
                continue

            variable_name = str(variable.get("name", "") or "").strip()

            if not variable_name:
                continue

            variable_type = str(
                variable.get("type", "auto") or "auto"
            ).strip() or "auto"
            variable_value = variable.get("value", "")
            self.variables[variable_name] = (
                self.helper.convert_variable_value(
                    variable_value,
                    variable_type,
                )
            )

    def stop(self):
        self.executor.stop()
        self.unregister_all_global_hotkeys()
        self.unregister_all_global_timers()

        if self.ui is not None:
            self.ui.cancel_pending()
            self.ui.notify_message_closed()

    def pause(self):
        self.executor.pause()

    def resume(self):
        self.executor.resume()

    def is_paused(self):
        return self.executor.is_paused()

    def exit_current_macro(self):
        if not self.executor.stopped:
            self.executor.exit_current_macro()

            if self.ui is not None:
                self.ui.notify_message_closed()

    def wait_if_paused(self):
        self.executor.wait_if_paused()

    def sleep(self, seconds):
        self.executor.sleep(seconds)

    def start_background_macro_group(self, target):
        if self.background_macro_starter is None:
            return False

        return bool(
            self.background_macro_starter(
                target,
                dict(self.variables),
            )
        )

    def normalize_global_hotkey(self, keys):
        parts = [
            part.strip().lower()
            for part in str(keys or "").replace(",", "+").split("+")
            if part.strip()
        ]
        normalized = []

        special_keys = {
            "ctrl": "<ctrl>",
            "control": "<ctrl>",
            "shift": "<shift>",
            "alt": "<alt>",
            "option": "<alt>",
            "cmd": "<cmd>",
            "command": "<cmd>",
            "win": "<cmd>",
            "super": "<cmd>",
            "meta": "<cmd>",
            "enter": "<enter>",
            "return": "<enter>",
            "space": "<space>",
            "tab": "<tab>",
            "esc": "<esc>",
            "escape": "<esc>",
            "backspace": "<backspace>",
            "delete": "<delete>",
            "del": "<delete>",
            "insert": "<insert>",
            "home": "<home>",
            "end": "<end>",
            "pageup": "<page_up>",
            "page_up": "<page_up>",
            "pagedown": "<page_down>",
            "page_down": "<page_down>",
            "up": "<up>",
            "down": "<down>",
            "left": "<left>",
            "right": "<right>",
        }

        for part in parts:
            if part in special_keys:
                normalized.append(special_keys[part])
                continue

            if part.startswith("f") and part[1:].isdigit():
                number = int(part[1:])

                if 1 <= number <= 24:
                    normalized.append(f"<f{number}>")
                    continue

            if len(part) == 1:
                normalized.append(part)
                continue

            normalized.append(f"<{part}>")

        return "+".join(normalized)

    def register_global_hotkey(self, registration):
        try:
            from pynput import keyboard
        except Exception as error:
            raise RuntimeError(
                f"pynput is required for global hotkeys: {error}"
            )

        if not isinstance(registration, dict):
            return

        hotkey_id = str(registration.get("id", "") or "").strip()
        keys = str(registration.get("keys", "") or "").strip()

        if not hotkey_id or not keys:
            return

        if hotkey_id in self.global_hotkey_listeners:
            return

        normalized_keys = self.normalize_global_hotkey(keys)

        if not normalized_keys:
            return

        event = {
            "id": hotkey_id,
            "keys": keys,
            "action_type": str(
                registration.get("action_type", "") or ""
            ).strip(),
            "target": registration.get("target", ""),
            "comment": registration.get("comment", ""),
            "python_code": registration.get("python_code", ""),
            "target_variable": registration.get("target_variable", ""),
            "run_in_background": self.helper.parse_bool(
                registration.get("run_in_background", False)
            ),
        }

        def on_activate():
            self.executor.queue_hotkey_event(event)

        listener = keyboard.GlobalHotKeys(
            {
                normalized_keys: on_activate,
            }
        )
        listener.start()
        self.global_hotkey_listeners[hotkey_id] = listener

    def register_global_timer(self, registration):
        if not isinstance(registration, dict):
            return

        timer_id = str(registration.get("id", "") or "").strip()

        if not timer_id or timer_id in self.global_timers:
            return

        try:
            seconds = float(registration.get("seconds", 0) or 0)
        except Exception:
            raise ValueError("Timer seconds must be a valid number.")

        if seconds <= 0:
            raise ValueError("Timer seconds must be greater than zero.")

        now = __import__("time").monotonic()
        run_immediately = self.helper.parse_bool(
            registration.get("run_immediately", False)
        )

        self.global_timers[timer_id] = {
            "id": timer_id,
            "seconds": seconds,
            "timer_mode": str(
                registration.get("timer_mode", "repeating") or "repeating"
            ),
            "next_run": now if run_immediately else now + seconds,
            "run_immediately": run_immediately,
            "action_type": str(
                registration.get("action_type", "") or ""
            ).strip(),
            "target": registration.get("target", ""),
            "comment": registration.get("comment", ""),
            "python_code": registration.get("python_code", ""),
            "target_variable": registration.get("target_variable", ""),
            "run_in_background": self.helper.parse_bool(
                registration.get("run_in_background", False)
            ),
        }

    def poll_global_timers(self):
        import time

        now = time.monotonic()
        events = []

        for timer_id, timer in list(self.global_timers.items()):
            if now < timer["next_run"]:
                continue

            events.append(dict(timer))

            if timer["timer_mode"] == "one_shot":
                self.global_timers.pop(timer_id, None)
            else:
                timer["next_run"] = now + timer["seconds"]

        for event in events:
            self.executor.queue_timer_event(event)

    def unregister_all_global_hotkeys(self):
        listeners = list(self.global_hotkey_listeners.values())
        self.global_hotkey_listeners = {}

        for listener in listeners:
            try:
                listener.stop()
            except Exception:
                pass

    def unregister_all_global_timers(self):
        self.global_timers = {}

    def run(self):
        try:
            self.executor.run()
            self.finished.emit()
        except Exception as error:
            self.failed.emit(str(error))
            self.finished.emit()
        finally:
            self.unregister_all_global_hotkeys()
            self.unregister_all_global_timers()

    def pyautogui_call(self, method, *args, **kwargs):
        return pyautogui_call(method, *args, **kwargs)


class MacroRunner(QObject):
    finished = Signal()
    failed = Signal(str)
    step_changed = Signal(int)
    message = Signal(str, str, bool)
    macro_group_started = Signal(str)
    macro_group_finished = Signal(str)

    def __init__(self, registry, context=None, parent=None):
        super().__init__(parent)
        self.registry = registry
        self.context = context
        self.thread = None
        self.worker = None
        self.last_run_result = {}
        self.last_run_variables = {}
        self.variables_provider = None
        self.macros_provider = None
        self.group_titles = {}
        self.background_threads = []
        self.background_workers = []

    def is_running(self):
        return self.thread is not None and self.thread.isRunning()

    def is_paused(self):
        return self.worker is not None and self.worker.is_paused()

    def set_variables_provider(self, callback):
        self.variables_provider = callback if callable(callback) else None

    def set_macros_provider(self, callback):
        self.macros_provider = callback if callable(callback) else None

    def get_project_macros(self):
        if self.context is not None:
            getter = getattr(self.context, "get_project_macros", None)

            if callable(getter):
                macros = getter() or []

                if macros:
                    return macros

        if callable(self.macros_provider):
            macros = self.macros_provider() or []

            if macros:
                return macros

        return []

    def build_group_library(self):
        group_library = {}
        self.group_titles = {}

        for macro_group in self.get_project_macros():
            group_name = str(
                getattr(macro_group, "name", "") or ""
            ).strip()
            group_title = str(
                getattr(macro_group, "title", "") or ""
            ).strip()

            if not group_name and group_title:
                group_name = group_title

            if not group_name:
                continue

            group_items = list(
                getattr(macro_group, "items", []) or []
            )
            group_library[group_name] = group_items
            self.group_titles[group_name] = group_title or group_name

            if group_title:
                group_library[group_title] = group_items

        return group_library

    def build_initial_variables(self, variables):
        initial_variables = []

        if isinstance(variables, dict):
            for name, value in variables.items():
                initial_variables.append(
                    {
                        "name": name,
                        "type": "auto",
                        "value": value,
                    }
                )
            return initial_variables

        if isinstance(variables, list):
            return list(variables)

        if variables is None and callable(self.variables_provider):
            return self.variables_provider() or []

        return []

    def cleanup_background_worker(self, thread, worker):
        if worker in self.background_workers:
            self.background_workers.remove(worker)

        if thread in self.background_threads:
            self.background_threads.remove(thread)

        thread.deleteLater()

    def start_background_macro_group(
        self,
        target,
        variables=None,
        loop_count=1,
        speed=1.0,
        delay_ms=0,
        max_depth=10,
    ):
        group_library = self.build_group_library()
        resolved_target = str(target or "").strip()

        if not resolved_target:
            return False

        if resolved_target not in group_library:
            for key, title in self.group_titles.items():
                if str(title or "").strip() == resolved_target:
                    resolved_target = key
                    break

        target_items = group_library.get(resolved_target, [])

        if not target_items:
            return False

        initial_variables = self.build_initial_variables(variables)
        thread = QThread()
        worker = MacroRunnerWorker(
            items=target_items,
            registry=self.registry,
            group_library=group_library,
            group_titles=self.group_titles,
            loop_count=loop_count,
            speed=speed,
            delay_ms=delay_ms,
            max_depth=max_depth,
            context=self.context,
            initial_variables=initial_variables,
            background_macro_starter=lambda child_target, child_variables: (
                self.start_background_macro_group(
                    child_target,
                    child_variables,
                    loop_count=loop_count,
                    speed=speed,
                    delay_ms=delay_ms,
                    max_depth=max_depth,
                )
            ),
        )

        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(
            lambda: self.cleanup_background_worker(thread, worker)
        )
        worker.failed.connect(
            self.failed.emit,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.message.connect(
            self.on_worker_message,
            Qt.ConnectionType.QueuedConnection,
        )

        self.background_threads.append(thread)
        self.background_workers.append(worker)
        thread.start()
        return True

    def start(
        self,
        items,
        group_library=None,
        loop_count=1,
        speed=1.0,
        delay_ms=0,
        max_depth=10,
        initial_variables=None,
    ):
        if self.is_running():
            return False

        if initial_variables is None and callable(self.variables_provider):
            initial_variables = self.variables_provider()

        if group_library is None:
            group_library = self.build_group_library()

        run_items = items

        if hasattr(items, "items"):
            run_items = getattr(items, "items", []) or []

        self.thread = QThread()
        self.worker = MacroRunnerWorker(
            items=run_items,
            registry=self.registry,
            group_library=group_library,
            group_titles=self.group_titles,
            loop_count=loop_count,
            speed=speed,
            delay_ms=delay_ms,
            max_depth=max_depth,
            context=self.context,
            initial_variables=initial_variables,
            background_macro_starter=lambda target, variables: (
                self.start_background_macro_group(
                    target,
                    variables,
                    loop_count=loop_count,
                    speed=speed,
                    delay_ms=delay_ms,
                    max_depth=max_depth,
                )
            ),
        )

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.on_thread_finished)
        self.worker.failed.connect(self.failed.emit)
        self.worker.step_changed.connect(self.step_changed.emit)
        self.worker.message.connect(
            self.on_worker_message,
            Qt.ConnectionType.QueuedConnection,
        )
        self.worker.macro_group_started.connect(
            self.macro_group_started.emit
        )
        self.worker.macro_group_finished.connect(
            self.macro_group_finished.emit
        )

        self.thread.start()
        return True

    def pause(self):
        if self.worker is not None:
            self.worker.pause()

    def resume(self):
        if self.worker is not None:
            self.worker.resume()

    def exit_current_macro(self):
        if self.worker is not None:
            self.worker.exit_current_macro()

    def stop(self):
        if self.worker is not None:
            self.worker.stop()

        for worker in list(self.background_workers):
            worker.stop()

        workers = []

        if self.worker is not None:
            workers.append(self.worker)

        workers.extend(self.background_workers)

        for worker in workers:
            ui = getattr(worker, "ui", None)

            if ui is not None:
                ui.cancel_pending()

    def notify_message_closed(self):
        workers = []

        if self.worker is not None:
            workers.append(self.worker)

        workers.extend(self.background_workers)

        for worker in workers:
            ui = getattr(worker, "ui", None)

            if ui is not None:
                ui.notify_message_closed()

    def on_worker_message(self, title, message, wait):
        self.message.emit(title, message, wait)

    def on_thread_finished(self):
        if self.worker is not None:
            self.last_run_variables = dict(
                getattr(self.worker, "variables", {}) or {}
            )

        self.thread.deleteLater()
        self.thread = None
        self.worker = None
        self.finished.emit()
