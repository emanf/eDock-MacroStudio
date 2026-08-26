from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import  QHBoxLayout, QLabel, QPushButton, QSpinBox, QWidget

from core.rendering.material_icons import MaterialIcons

from ..base_field import BaseFormField
from .color_field import WindowsEyedropperApi


def normalize_mouse_position(value):
    if isinstance(value, dict):
        return {
            "x": int(value.get("x", 0) or 0),
            "y": int(value.get("y", 0) or 0),
        }

    if isinstance(value, (list, tuple)) and len(value) >= 2:
        return {
            "x": int(value[0] or 0),
            "y": int(value[1] or 0),
        }

    if isinstance(value, str):
        parts = value.replace(";", ",").replace("x", ",").replace("X", ",").split(",")
        parts = [part.strip() for part in parts if part.strip()]
        if len(parts) >= 2:
            try:
                return {
                    "x": int(float(parts[0])),
                    "y": int(float(parts[1])),
                }
            except ValueError:
                pass

    return {
        "x": 0,
        "y": 0,
    }


class MousePositionOverlay(QWidget):
    positionHovered = Signal(object)
    positionPicked = Signal(object)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(None)
        self.parent_dialog = parent
        self.current_pos = QPoint(0, 0)
        self.last_pos = QPoint(-1, -1)
        self.left_was_down = False
        self.right_was_down = False
        self.escape_was_down = False
        self.windows_api = WindowsEyedropperApi()

        self.live_timer = QTimer(self)
        self.live_timer.setInterval(16)
        self.live_timer.timeout.connect(self.refresh_position)

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def start(self):
        virtual_geometry = self.get_virtual_geometry()
        if not virtual_geometry:
            self.cancelled.emit()
            return

        self.current_pos = QCursor.pos()
        self.setGeometry(virtual_geometry)
        self.show()
        self.raise_()
        self.activateWindow()
        self.apply_native_topmost(force_show=True)
        self.grabMouse()
        self.grabKeyboard()
        self.refresh_position(force=True)
        self.live_timer.start()

    def get_virtual_geometry(self):
        screens = QGuiApplication.screens()
        if not screens:
            return None

        virtual_geometry = screens[0].virtualGeometry()
        for screen in screens:
            virtual_geometry = virtual_geometry.united(screen.geometry())

        return virtual_geometry

    def apply_native_topmost(self, force_show=False):
        self.windows_api.force_topmost(int(self.winId()), force_show)

    def handle_global_buttons(self):
        if not self.windows_api.enabled:
            return

        left_down = self.windows_api.is_key_down(WindowsEyedropperApi.VK_LBUTTON)
        right_down = self.windows_api.is_key_down(WindowsEyedropperApi.VK_RBUTTON)
        escape_down = self.windows_api.is_key_down(WindowsEyedropperApi.VK_ESCAPE)

        if left_down and not self.left_was_down:
            self.pick_at(QCursor.pos())
            return

        if right_down and not self.right_was_down:
            self.cancel()
            return

        if escape_down and not self.escape_was_down:
            self.cancel()
            return

        self.left_was_down = left_down
        self.right_was_down = right_down
        self.escape_was_down = escape_down

    def update_current_position(self, global_pos, force=False):
        if not force and global_pos == self.last_pos:
            return False

        self.current_pos = QPoint(global_pos)
        self.last_pos = QPoint(global_pos)

        self.positionHovered.emit({
            "x": int(self.current_pos.x()),
            "y": int(self.current_pos.y()),
        })

        return True

    def refresh_position(self, force=False):
        self.apply_native_topmost(force_show=True)
        self.handle_global_buttons()

        if not self.live_timer.isActive():
            return

        if self.update_current_position(QCursor.pos(), force):
            self.update()

    def pick_at(self, global_pos):
        self.finish({
            "x": int(global_pos.x()),
            "y": int(global_pos.y()),
        })

    def mouseMoveEvent(self, event):
        self.apply_native_topmost(force_show=True)

        if self.update_current_position(event.globalPosition().toPoint(), force=True):
            self.update()

    def mousePressEvent(self, event):
        self.apply_native_topmost(force_show=True)

        if event.button() == Qt.MouseButton.LeftButton:
            self.pick_at(event.globalPosition().toPoint())
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.cancel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()

    def paintEvent(self, event):
        painter = QPainter(self)
        local_pos = self.mapFromGlobal(self.current_pos)
        preview_width = 112
        preview_height = 54
        preview_x = local_pos.x() + 18
        preview_y = local_pos.y() + 18

        if preview_x + preview_width > self.width():
            preview_x = local_pos.x() - preview_width - 18
        if preview_y + preview_height > self.height():
            preview_y = local_pos.y() - preview_height - 18

        position_text = f"X: {self.current_pos.x()}  Y: {self.current_pos.y()}"

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawLine(local_pos.x() - 12, local_pos.y(), local_pos.x() - 4, local_pos.y())
        painter.drawLine(local_pos.x() + 4, local_pos.y(), local_pos.x() + 12, local_pos.y())
        painter.drawLine(local_pos.x(), local_pos.y() - 12, local_pos.x(), local_pos.y() - 4)
        painter.drawLine(local_pos.x(), local_pos.y() + 4, local_pos.x(), local_pos.y() + 12)

        painter.setBrush(QColor("#101114"))
        painter.setPen(QPen(QColor("#343849"), 1))
        painter.drawRoundedRect(preview_x, preview_y, preview_width, preview_height, 10, 10)

        painter.setPen(QColor("#f4f4f5"))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(preview_x + 10, preview_y + 32, position_text)

        painter.end()

    def stop(self):
        self.live_timer.stop()
        self.releaseMouse()
        self.releaseKeyboard()
        self.hide()
        self.deleteLater()

    def finish(self, position):
        self.stop()
        self.positionPicked.emit(position)

    def cancel(self):
        self.stop()
        self.cancelled.emit()


class MousePositionPickerInput(QWidget):
    positionChanged = Signal(object)

    def __init__(self, initial_position=None, parent=None):
        super().__init__(parent)
        self._current_position = normalize_mouse_position(initial_position)
        self._previous_position = dict(self._current_position)
        self._capture = None
        self.setObjectName("MousePositionPickerInput")

        self.material_font = MaterialIcons.ensure_font()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.x_label = QLabel("X", self)
        layout.addWidget(self.x_label)

        self.x_input = QSpinBox(self)
        self.x_input.setRange(-100000, 100000)
        self.x_input.setValue(self._current_position["x"])
        self.x_input.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.x_input, 1)

        self.y_label = QLabel("Y", self)
        layout.addWidget(self.y_label)

        self.y_input = QSpinBox(self)
        self.y_input.setRange(-100000, 100000)
        self.y_input.setValue(self._current_position["y"])
        self.y_input.valueChanged.connect(self.on_value_changed)
        layout.addWidget(self.y_input, 1)

        self.capture_button = QPushButton("my_location", self)
        self.capture_button.setFont(QFont(self.material_font))
        self.capture_button.setToolTip("Capture mouse position")
        self.capture_button.clicked.connect(self.start_capture)
        layout.addWidget(self.capture_button)

    def start_capture(self):
        self._previous_position = self.get_position()
        dialog = self.window()

        QTimer.singleShot(180, lambda: self.open_capture(dialog))

    def open_capture(self, dialog):
        self._capture = MousePositionOverlay(dialog)
        self._capture.positionHovered.connect(self.preview_position)
        self._capture.positionPicked.connect(self.finish_capture)
        self._capture.cancelled.connect(self.cancel_capture)
        self._capture.start()

    def preview_position(self, position):
        self.set_position(position)

    def finish_capture(self, position):
        self.set_position(position)

    def cancel_capture(self):
        self.set_position(self._previous_position)

    def on_value_changed(self):
        self._current_position = {
            "x": int(self.x_input.value()),
            "y": int(self.y_input.value()),
        }
        self.positionChanged.emit(dict(self._current_position))

    def set_position(self, value, emit_signal=True):
        position = normalize_mouse_position(value)
        self._current_position = position

        self.x_input.blockSignals(True)
        self.y_input.blockSignals(True)
        self.x_input.setValue(position["x"])
        self.y_input.setValue(position["y"])
        self.x_input.blockSignals(False)
        self.y_input.blockSignals(False)

        if emit_signal:
            self.positionChanged.emit(dict(self._current_position))

    def get_position(self):
        return {
            "x": int(self.x_input.value()),
            "y": int(self.y_input.value()),
        }


class MousePositionFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = MousePositionPickerInput(value, parent)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.positionChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.get_position()

    def set_value(self, field, widget, value):
        widget.set_position(value)
