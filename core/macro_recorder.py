import time
from PySide6.QtCore import QObject, Signal

from .model.macro_item import MacroItem


class MacroRecorder(QObject):
    recorded = Signal(object)
    started = Signal()
    stopped = Signal()
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mouse_listener = None
        self.keyboard_listener = None
        self.is_recording = False
        self.last_time = None
        self.last_move_time = 0

    def start(self):
        if self.is_recording:
            return False

        try:
            from pynput import mouse, keyboard
        except Exception:
            self.failed.emit("pynput is required for recording macros. Install it with: pip install pynput")
            return False

        self.is_recording = True
        self.last_time = time.time()
        self.last_move_time = 0

        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll,
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()
        self.started.emit()
        return True

    def stop(self):
        if not self.is_recording:
            return False

        self.is_recording = False

        try:
            if self.mouse_listener is not None:
                self.mouse_listener.stop()
        except Exception:
            pass

        try:
            if self.keyboard_listener is not None:
                self.keyboard_listener.stop()
        except Exception:
            pass

        self.mouse_listener = None
        self.keyboard_listener = None
        self.stopped.emit()
        return True

    def add_wait_if_needed(self):
        now = time.time()
        if self.last_time is None:
            self.last_time = now
            return

        diff = now - self.last_time
        self.last_time = now

        if diff >= 0.08:
            self.recorded.emit(
                MacroItem(
                    command_id="timing.wait",
                    values={
                        "wait_type": "value",
                        "seconds": round(diff, 2),
                    },
                )
            )

    def on_mouse_move(self, x, y):
        if not self.is_recording:
            return

        now = time.time()
        if now - self.last_move_time < 0.25:
            return

        self.last_move_time = now
        self.add_wait_if_needed()
        self.recorded.emit(
            MacroItem(
                command_id="mouse.move",
                values={
                    "position_type": "value",
                    "position": {"x": int(x), "y": int(y)},
                    "random_offset_min": 0,
                    "random_offset_max": 0,
                    "duration": 0.1,
                },
            )
        )

    def on_mouse_click(self, x, y, button, pressed):
        if not self.is_recording or not pressed:
            return

        self.add_wait_if_needed()

        button_name = str(button).split(".")[-1]
        if button_name not in ["left", "right", "middle"]:
            button_name = "left"

        self.recorded.emit(
            MacroItem(
                command_id="mouse.click",
                values={
                    "click_mode": "position",
                    "position_type": "value",
                    "position": {"x": int(x), "y": int(y)},
                    "random_offset": {"min_value": 0, "max_value": 0},
                    "button": button_name,
                    "clicks": 1,
                },
            )
        )

    def on_mouse_scroll(self, x, y, dx, dy):
        if not self.is_recording:
            return

        self.add_wait_if_needed()
        self.recorded.emit(
            MacroItem(
                command_id="mouse.scroll",
                values={
                    "amount": int(dy),
                },
            )
        )

    def on_key_press(self, key):
        if not self.is_recording:
            return

        self.add_wait_if_needed()

        key_text = self.key_to_text(key)

        if key_text:
            self.recorded.emit(
                MacroItem(
                    command_id="keyboard.key_press",
                    values={
                        "key": key_text,
                    },
                )
            )

    def key_to_text(self, key):
        try:
            char = getattr(key, "char", None)
            if char:
                return char
        except Exception:
            pass

        text = str(key or "")
        if text.startswith("Key."):
            text = text[4:]

        replacements = {
            "space": "space",
            "enter": "enter",
            "tab": "tab",
            "esc": "esc",
            "backspace": "backspace",
            "delete": "delete",
            "ctrl_l": "ctrl",
            "ctrl_r": "ctrl",
            "shift": "shift",
            "shift_l": "shift",
            "shift_r": "shift",
            "alt_l": "alt",
            "alt_r": "alt",
            "cmd": "win",
            "cmd_l": "win",
            "cmd_r": "win",
        }

        return replacements.get(text, text)
