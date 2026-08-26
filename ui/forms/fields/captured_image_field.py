import base64
import json

from PySide6 import QtCore
from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QWidget

from core.rendering.material_icons import MaterialIcons

from ..base_field import BaseFormField
from .color_field import WindowsEyedropperApi


def empty_captured_image():
    return {
        "image_base64": "",
        "start_x": 0,
        "start_y": 0,
        "end_x": 0,
        "end_y": 0,
        "width": 0,
        "height": 0,
    }


def normalize_captured_image(value):
    if isinstance(value, dict):
        image_base64 = str(value.get("image_base64", "") or "")
        start_x = int(value.get("start_x", 0) or 0)
        start_y = int(value.get("start_y", 0) or 0)
        end_x = int(value.get("end_x", 0) or 0)
        end_y = int(value.get("end_y", 0) or 0)
        width = int(value.get("width", 0) or 0)
        height = int(value.get("height", 0) or 0)

        return {
            "image_base64": image_base64,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "width": width,
            "height": height,
        }

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return empty_captured_image()

        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return normalize_captured_image(parsed)
        except Exception:
            pass

        return {
            "image_base64": value,
            "start_x": 0,
            "start_y": 0,
            "end_x": 0,
            "end_y": 0,
            "width": 0,
            "height": 0,
        }

    return empty_captured_image()


def pixmap_to_base64(pixmap):
    if pixmap.isNull():
        return ""

    from PySide6.QtCore import QByteArray, QBuffer, QIODevice

    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(byte_array.toBase64()).decode("utf-8")


def base64_to_pixmap(value):
    value = str(value or "").strip()
    pixmap = QPixmap()

    if not value:
        return pixmap

    try:
        raw = base64.b64decode(value)
    except Exception:
        return QPixmap()

    pixmap.loadFromData(raw, "PNG")
    return pixmap


class ScreenRegionOverlay(QWidget):
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
        self.full_screenshot = QPixmap()

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
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

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
        self.full_screenshot = self.capture_virtual_geometry(virtual_geometry)

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

    def capture_virtual_geometry(self, geometry):
        screens = QGuiApplication.screens()
        result = QPixmap(geometry.size())
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        for screen in screens:
            screen_geometry = screen.geometry()
            part = screen.grabWindow(0)
            target_top_left = screen_geometry.topLeft() - geometry.topLeft()
            painter.drawPixmap(target_top_left, part)
        painter.end()

        return result

    def apply_native_topmost(self, force_show=False):
        self.windows_api.force_topmost(int(self.winId()), force_show)

    def normalized_rect(self):
        if self.start_pos is None or self.end_pos is None:
            return QRect()

        return QRect(self.start_pos, self.end_pos).normalized()

    def current_capture(self):
        rect = self.normalized_rect()
        if rect.width() <= 0 or rect.height() <= 0 or self.full_screenshot.isNull():
            return empty_captured_image()

        start_x = int(rect.left())
        start_y = int(rect.top())
        end_x = int(rect.right())
        end_y = int(rect.bottom())

        local_rect = QRect(
            rect.left() - self.geometry().left(),
            rect.top() - self.geometry().top(),
            rect.width(),
            rect.height(),
        )
        pixmap = self.full_screenshot.copy(local_rect)

        return normalize_captured_image({
            "image_base64": pixmap_to_base64(pixmap),
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "width": int(pixmap.width()),
            "height": int(pixmap.height()),
        })

    def handle_global_input(self):
        self.apply_native_topmost(force_show=True)
        self.current_pos = QCursor.pos()

        if self.dragging:
            self.end_pos = QPoint(self.current_pos)
            self.regionHovered.emit(self.current_capture())

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
            self.regionHovered.emit(self.current_capture())
            self.update()
            return

        if not left_down and self.left_was_down:
            self.left_was_down = False
            if self.dragging:
                self.dragging = False
                self.end_pos = QPoint(self.current_pos)
                capture = self.current_capture()
                if capture.get("image_base64"):
                    self.finish(capture)
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

        if not self.full_screenshot.isNull():
            painter.drawPixmap(self.rect(), self.full_screenshot)

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

            if not self.full_screenshot.isNull():
                selected = self.full_screenshot.copy(local_rect)
                painter.drawPixmap(local_rect, selected)

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
            painter.drawText(preview_x + 10, preview_y + 22, f"Size: {rect.width()} x {rect.height()}")
            painter.drawText(preview_x + 10, preview_y + 42, f"Start: {rect.left()}, {rect.top()}")
            painter.drawText(preview_x + 10, preview_y + 62, f"End: {rect.right()}, {rect.bottom()}")
            painter.drawText(preview_x + 10, preview_y + 82, "Release to capture")

        painter.end()

    def stop(self):
        self.timer.stop()
        self.releaseKeyboard()
        self.releaseMouse()
        self.hide()
        self.deleteLater()

    def finish(self, capture):
        self.stop()
        self.regionPicked.emit(normalize_captured_image(capture))

    def cancel(self):
        self.stop()
        self.cancelled.emit()


class CapturedImagePickerInput(QWidget):
    imageChanged = Signal(object)

    def __init__(self, initial_value=None, parent=None):
        super().__init__(parent)
        self._current_value = normalize_captured_image(initial_value)
        self._previous_value = normalize_captured_image(initial_value)
        self._capture = None
        self.setObjectName("CapturedImagePickerInput")

        self.material_font = MaterialIcons.ensure_font()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.preview = QLabel(self)
        self.preview.setMinimumSize(72, 48)
        self.preview.setMaximumHeight(48)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview, 1)

        self.capture_button = QPushButton("crop_free", self)
        self.capture_button.setFont(QFont(self.material_font))
        self.capture_button.setToolTip("Capture screen region")
        self.capture_button.clicked.connect(self.start_capture)
        layout.addWidget(self.capture_button)

        self.load_button = QPushButton("image", self)
        self.load_button.setFont(QFont(self.material_font))
        self.load_button.setToolTip("Load image from file")
        self.load_button.clicked.connect(self.load_from_file)
        layout.addWidget(self.load_button)

        self.clear_button = QPushButton("close", self)
        self.clear_button.setFont(QFont(self.material_font))
        self.clear_button.setToolTip("Clear captured image")
        self.clear_button.clicked.connect(self.clear_value)
        layout.addWidget(self.clear_button)

        self.set_value(self._current_value, emit_signal=False)

    def start_capture(self):
        self._previous_value = self.get_value()
        dialog = self.window()
        QTimer.singleShot(180, lambda: self.open_capture(dialog))

    def open_capture(self, dialog):
        self._capture = ScreenRegionOverlay(dialog)
        self._capture.regionHovered.connect(self.preview_capture)
        self._capture.regionPicked.connect(self.finish_capture)
        self._capture.cancelled.connect(self.cancel_capture)
        self._capture.start()

    def preview_capture(self, value):
        self.set_value(value)

    def finish_capture(self, value):
        self._capture = None
        self.set_value(value)
        self.update_position_field()

    def cancel_capture(self):
        self._capture = None
        self.set_value(self._previous_value)

    def load_from_file(self):
        self._previous_value = self.get_value()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*.*)",
        )
        if not file_path:
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return

        self.set_value({
            "image_base64": pixmap_to_base64(pixmap),
            "start_x": 0,
            "start_y": 0,
            "end_x": 0,
            "end_y": 0,
            "width": int(pixmap.width()),
            "height": int(pixmap.height()),
        })

    def clear_value(self):
        self.set_value(empty_captured_image())
        self.update_position_field()

    def set_value(self, value, emit_signal=True):
        normalized = normalize_captured_image(value)
        self._current_value = normalized
        self.update_preview()

        if emit_signal:
            self.imageChanged.emit(self.get_value())

    def update_preview(self):
        image_base64 = self._current_value.get("image_base64", "")
        width = int(self._current_value.get("width", 0) or 0)
        height = int(self._current_value.get("height", 0) or 0)
        start_x = int(self._current_value.get("start_x", 0) or 0)
        start_y = int(self._current_value.get("start_y", 0) or 0)
        end_x = int(self._current_value.get("end_x", 0) or 0)
        end_y = int(self._current_value.get("end_y", 0) or 0)

        pixmap = base64_to_pixmap(image_base64)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                96,
                48,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.preview.setPixmap(scaled)
            self.preview.setText("")
            self.preview.setToolTip(f"{width} x {height} | {start_x}, {start_y} -> {end_x}, {end_y}")
            return

        self.preview.setPixmap(QPixmap())
        self.preview.setToolTip("")

        if width > 0 and height > 0:
            self.preview.setText(f"{width} x {height}")
        else:
            self.preview.setText("No image")

    def get_value(self):
        return normalize_captured_image(self._current_value)

    def update_position_field(self):
        if not isinstance(self._current_value, dict):
            return

        dialog = self.window()

        if hasattr(dialog, "set_field_value"):
            dialog.set_field_value("position", {
                "x": int(self._current_value.get("start_x", 0) or 0),
                "y": int(self._current_value.get("start_y", 0) or 0),
            })


class CapturedImageFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = CapturedImagePickerInput(value, parent)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.imageChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.get_value()

    def set_value(self, field, widget, value):
        widget.set_value(value)
