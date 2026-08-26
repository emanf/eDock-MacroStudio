from PySide6 import QtCore
from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpinBox, QVBoxLayout, QWidget

from core.rendering.material_icons import MaterialIcons

from ..base_field import BaseFormField
from .color_field import WindowsEyedropperApi


def empty_screen_region():
    return {
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0,
    }


def normalize_screen_region(value):
    if isinstance(value, dict):
        x = int(value.get("x", 0) or 0)
        y = int(value.get("y", 0) or 0)
        width = int(value.get("width", 0) or 0)
        height = int(value.get("height", 0) or 0)

        return {
            "x": x,
            "y": y,
            "width": max(0, width),
            "height": max(0, height),
        }

    return empty_screen_region()


class ScreenRegionPickerOverlay(QWidget):
    regionHovered = Signal(object)
    regionPicked = Signal(object)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(None)
        self.parent_dialog = parent
        self.current_pos = QCursor.pos()
        self.start_pos = None
        self.end_pos = None
        self.dragging = False
        self.left_was_down = False
        self.right_was_down = False
        self.windows_api = WindowsEyedropperApi()

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.handle_global_input)

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

    def start(self):
        virtual_geometry = self.get_virtual_geometry()
        if not virtual_geometry:
            self.cancelled.emit()
            return

        self.current_pos = QCursor.pos()
        self.start_pos = None
        self.end_pos = None
        self.dragging = False
        self.left_was_down = False
        self.right_was_down = False
        self.setGeometry(virtual_geometry)

        self.show()
        self.setWindowState(QtCore.Qt.WindowFullScreen)
        self.activateWindow()
        self.raise_()
        self.setFocus(QtCore.Qt.ActiveWindowFocusReason)
        self.grabKeyboard()
        self.grabMouse()
        self.apply_native_topmost(force_show=True)
        self.update()
        self.timer.start()

    def get_virtual_geometry(self):
        screens = QGuiApplication.screens()
        if not screens:
            return None

        geometry = screens[0].virtualGeometry()
        for screen in screens[1:]:
            geometry = geometry.united(screen.geometry())

        return geometry

    def apply_native_topmost(self, force_show=False):
        self.windows_api.force_topmost(int(self.winId()), force_show)

    def normalized_rect(self):
        if self.start_pos is None or self.end_pos is None:
            return QRect()

        return QRect(self.start_pos, self.end_pos).normalized()

    def current_region(self):
        rect = self.normalized_rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return empty_screen_region()

        return normalize_screen_region({
            "x": int(rect.left()),
            "y": int(rect.top()),
            "width": int(rect.width()),
            "height": int(rect.height()),
        })

    def handle_global_input(self):
        self.apply_native_topmost(force_show=True)
        self.current_pos = QCursor.pos()

        if self.dragging:
            self.end_pos = QPoint(self.current_pos)
            self.regionHovered.emit(self.current_region())

        left_down = self.windows_api.is_key_down(0x01)
        right_down = self.windows_api.is_key_down(0x02)

        if right_down and not self.right_was_down:
            self.right_was_down = True
            self.cancel()
            return

        if not right_down:
            self.right_was_down = False

        if left_down and not self.left_was_down:
            self.left_was_down = True
            self.dragging = True
            self.start_pos = QPoint(self.current_pos)
            self.end_pos = QPoint(self.current_pos)
            self.regionHovered.emit(self.current_region())
            self.update()
            return

        if not left_down and self.left_was_down:
            self.left_was_down = False
            if self.dragging:
                self.dragging = False
                self.end_pos = QPoint(self.current_pos)
                region = self.current_region()
                if region.get("width", 0) > 0 and region.get("height", 0) > 0:
                    self.finish(region)
                    return
                self.cancel()
                return

        self.update()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.cancel()
            return

        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 90))

        local_pos = self.mapFromGlobal(self.current_pos)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawLine(local_pos.x() - 12, local_pos.y(), local_pos.x() - 4, local_pos.y())
        painter.drawLine(local_pos.x() + 4, local_pos.y(), local_pos.x() + 12, local_pos.y())
        painter.drawLine(local_pos.x(), local_pos.y() - 12, local_pos.x(), local_pos.y() - 4)
        painter.drawLine(local_pos.x(), local_pos.y() + 4, local_pos.x(), local_pos.y() + 12)

        rect = self.normalized_rect()
        if rect.width() > 0 and rect.height() > 0:
            local_rect = QRect(
                rect.left() - self.geometry().left(),
                rect.top() - self.geometry().top(),
                rect.width(),
                rect.height(),
            )

            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(local_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#4da3ff"), 2))
            painter.drawRect(local_rect)

            preview_width = 220
            preview_height = 96
            preview_x = local_rect.right() + 18
            preview_y = local_rect.bottom() + 18

            if preview_x + preview_width > self.width():
                preview_x = local_rect.left() - preview_width - 18

            if preview_y + preview_height > self.height():
                preview_y = local_rect.top() - preview_height - 18

            painter.setBrush(QColor("#101114"))
            painter.setPen(QPen(QColor("#343849"), 1))
            painter.drawRoundedRect(preview_x, preview_y, preview_width, preview_height, 10, 10)

            painter.setPen(QColor("#f4f4f5"))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(preview_x + 10, preview_y + 22, f"X: {rect.left()}  Y: {rect.top()}")
            painter.drawText(preview_x + 10, preview_y + 44, f"W: {rect.width()}  H: {rect.height()}")
            painter.drawText(preview_x + 10, preview_y + 68, "Release to capture")

        painter.end()

    def stop(self):
        self.timer.stop()
        self.releaseKeyboard()
        self.releaseMouse()
        self.hide()
        self.deleteLater()

    def finish(self, region):
        self.stop()
        self.regionPicked.emit(normalize_screen_region(region))

    def cancel(self):
        self.stop()
        self.cancelled.emit()


class ScreenRegionPickerInput(QWidget):
    regionChanged = Signal(object)

    def __init__(self, initial_value=None, parent=None):
        super().__init__(parent)
        self._current_value = normalize_screen_region(initial_value)
        self._previous_value = normalize_screen_region(initial_value)
        self._capture = None
        self.setObjectName("ScreenRegionPickerInput")

        self.material_font = MaterialIcons.ensure_font()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)

        self.x_input = self.create_spinbox()
        self.y_input = self.create_spinbox()
        self.width_input = self.create_spinbox(minimum=0)
        self.height_input = self.create_spinbox(minimum=0)

        self.capture_button = QPushButton("crop_free", self)
        self.capture_button.setFont(QFont(self.material_font))
        self.capture_button.setToolTip("Pick screen region")
        self.capture_button.setFixedWidth(42)
        self.capture_button.clicked.connect(self.start_capture)

        top_row.addWidget(self.create_field_box("X:", self.x_input), 1)
        top_row.addWidget(self.create_field_box("Y:", self.y_input), 1)
        top_row.addWidget(self.capture_button)

        bottom_row.addWidget(self.create_field_box("W:", self.width_input), 1)
        bottom_row.addWidget(self.create_field_box("H:", self.height_input), 1)
        bottom_row.addSpacing(50)

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)

        self.x_input.valueChanged.connect(self.emit_current_value)
        self.y_input.valueChanged.connect(self.emit_current_value)
        self.width_input.valueChanged.connect(self.emit_current_value)
        self.height_input.valueChanged.connect(self.emit_current_value)

        self.set_value(self._current_value, emit_signal=False)

    def create_field_box(self, label_text, input_widget):
        widget = QWidget(self)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(label_text, widget)
        label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        input_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout.addWidget(label)
        layout.addWidget(input_widget, 1)

        return widget

    def create_spinbox(self, minimum=-100000, maximum=100000):
        spinbox = QSpinBox(self)
        spinbox.setRange(minimum, maximum)
        spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        spinbox.setMinimumWidth(100)
        return spinbox

    def start_capture(self):
        self._previous_value = self.get_value()
        dialog = self.window()
        QtCore.QTimer.singleShot(180, lambda: self.open_capture(dialog))

    def open_capture(self, dialog):
        self._capture = ScreenRegionPickerOverlay(dialog)
        self._capture.regionHovered.connect(self.preview_region)
        self._capture.regionPicked.connect(self.finish_capture)
        self._capture.cancelled.connect(self.cancel_capture)
        self._capture.start()

    def preview_region(self, value):
        self.set_value(value)

    def finish_capture(self, value):
        self._capture = None
        self.set_value(value)

    def cancel_capture(self):
        self._capture = None
        self.set_value(self._previous_value)

    def set_value(self, value, emit_signal=True):
        normalized = normalize_screen_region(value)
        self._current_value = normalized

        widgets = [
            self.x_input,
            self.y_input,
            self.width_input,
            self.height_input,
        ]

        for widget in widgets:
            widget.blockSignals(True)

        self.x_input.setValue(normalized.get("x", 0))
        self.y_input.setValue(normalized.get("y", 0))
        self.width_input.setValue(normalized.get("width", 0))
        self.height_input.setValue(normalized.get("height", 0))

        for widget in widgets:
            widget.blockSignals(False)

        if emit_signal:
            self.regionChanged.emit(self.get_value())

    def emit_current_value(self):
        self._current_value = normalize_screen_region({
            "x": self.x_input.value(),
            "y": self.y_input.value(),
            "width": self.width_input.value(),
            "height": self.height_input.value(),
        })
        self.regionChanged.emit(self.get_value())

    def get_value(self):
        return normalize_screen_region({
            "x": self.x_input.value(),
            "y": self.y_input.value(),
            "width": self.width_input.value(),
            "height": self.height_input.value(),
        })


class ScreenRegionFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = ScreenRegionPickerInput(value, parent)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.regionChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.get_value()

    def set_value(self, field, widget, value):
        widget.set_value(value)
