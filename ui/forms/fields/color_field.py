import ctypes
import sys

from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QColorDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget

from core.rendering.material_icons import MaterialIcons

from ..base_field import BaseFormField


def color_to_ui(value):
    value = str(value or "").strip()
    if not value.startswith("#"):
        return value

    hex_value = value[1:]

    if len(hex_value) == 8:
        r = hex_value[0:2]
        g = hex_value[2:4]
        b = hex_value[4:6]
        a = hex_value[6:8]
        return f"#{a}{r}{g}{b}"

    return value


def color_from_ui(value):
    value = str(value or "").strip()
    if not value.startswith("#"):
        return value

    hex_value = value[1:]

    if len(hex_value) == 8:
        a = hex_value[0:2]
        r = hex_value[2:4]
        g = hex_value[4:6]
        b = hex_value[6:8]
        return f"#{r}{g}{b}{a}"

    return value


def qcolor_to_value(color):
    if not color.isValid():
        return "#000000"

    if color.alpha() < 255:
        return "#{:02x}{:02x}{:02x}{:02x}".format(
            color.red(),
            color.green(),
            color.blue(),
            color.alpha(),
        )

    return "#{:02x}{:02x}{:02x}".format(
        color.red(),
        color.green(),
        color.blue(),
    )


def value_to_qcolor(value):
    color = QColor(color_to_ui(value))
    if color.isValid():
        return color
    return QColor("#000000")


class WindowsEyedropperApi:
    GWL_EXSTYLE = -20
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_LAYERED = 0x00080000
    HWND_TOPMOST = -1
    SWP_NOSIZE = 0x0001
    SWP_NOMOVE = 0x0002
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040
    SWP_NOOWNERZORDER = 0x0200
    SW_SHOWNOACTIVATE = 4
    VK_LBUTTON = 0x01
    VK_RBUTTON = 0x02
    VK_ESCAPE = 0x1B

    def __init__(self):
        self.enabled = sys.platform.startswith("win")
        self.user32 = None
        self.gdi32 = None

        if self.enabled:
            self.user32 = ctypes.windll.user32
            self.gdi32 = ctypes.windll.gdi32

    def force_topmost(self, hwnd, force_show=False):
        if not self.enabled or not self.user32:
            return

        style = self.user32.GetWindowLongW(hwnd, self.GWL_EXSTYLE)
        self.user32.SetWindowLongW(
            hwnd,
            self.GWL_EXSTYLE,
            style | self.WS_EX_TOPMOST | self.WS_EX_TOOLWINDOW | self.WS_EX_LAYERED,
        )

        if force_show:
            self.user32.ShowWindow(hwnd, self.SW_SHOWNOACTIVATE)

        self.user32.SetWindowPos(
            hwnd,
            self.HWND_TOPMOST,
            0,
            0,
            0,
            0,
            self.SWP_NOMOVE
            | self.SWP_NOSIZE
            | self.SWP_NOACTIVATE
            | self.SWP_SHOWWINDOW
            | self.SWP_NOOWNERZORDER,
        )
        self.user32.BringWindowToTop(hwnd)

    def color_at(self, global_pos):
        if not self.enabled or not self.user32 or not self.gdi32:
            return QColor()

        hdc = self.user32.GetDC(0)
        if not hdc:
            return QColor()

        pixel = self.gdi32.GetPixel(hdc, int(global_pos.x()), int(global_pos.y()))
        self.user32.ReleaseDC(0, hdc)

        if pixel == -1:
            return QColor()

        red = pixel & 0x0000FF
        green = (pixel & 0x00FF00) >> 8
        blue = (pixel & 0xFF0000) >> 16

        return QColor(red, green, blue)

    def is_key_down(self, key_code):
        if not self.enabled or not self.user32:
            return False

        return bool(self.user32.GetAsyncKeyState(key_code) & 0x8000)


class ColorEyedropperOverlay(QWidget):
    colorHovered = Signal(str)
    colorPicked = Signal(str)
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(None)
        self.parent_dialog = parent
        self.current_color = QColor("#000000")
        self.current_pos = QPoint(0, 0)
        self.last_pos = QPoint(-1, -1)
        self.last_color_value = ""
        self.left_was_down = False
        self.right_was_down = False
        self.escape_was_down = False
        self.windows_api = WindowsEyedropperApi()

        self.live_timer = QTimer(self)
        self.live_timer.setInterval(16)
        self.live_timer.timeout.connect(self.refresh_color)

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
        self.refresh_color(force=True)
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

    def qt_color_at(self, global_pos):
        screen = QGuiApplication.screenAt(global_pos)
        if not screen:
            return QColor()

        geometry = screen.geometry()
        local = global_pos - geometry.topLeft()
        pixmap = screen.grabWindow(0, local.x(), local.y(), 1, 1)
        image = pixmap.toImage()

        if image.width() <= 0 or image.height() <= 0:
            return QColor()

        return image.pixelColor(0, 0)

    def color_at(self, global_pos):
        if self.windows_api.enabled:
            return self.windows_api.color_at(global_pos)

        return self.qt_color_at(global_pos)

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

    def update_current_color(self, global_pos, force=False):
        if not force and global_pos == self.last_pos:
            return False

        self.current_pos = QPoint(global_pos)
        self.last_pos = QPoint(global_pos)

        color = self.color_at(global_pos)
        if not color.isValid():
            return False

        color_value = qcolor_to_value(color)
        self.current_color = color

        if color_value != self.last_color_value:
            self.last_color_value = color_value
            self.colorHovered.emit(color_value)

        return True

    def refresh_color(self, force=False):
        self.apply_native_topmost(force_show=True)
        self.handle_global_buttons()

        if not self.live_timer.isActive():
            return

        if self.update_current_color(QCursor.pos(), force):
            self.update()

    def pick_at(self, global_pos):
        color = self.color_at(global_pos)
        if color.isValid():
            self.finish(qcolor_to_value(color))

    def mouseMoveEvent(self, event):
        self.apply_native_topmost(force_show=True)

        if self.update_current_color(event.globalPosition().toPoint(), force=True):
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
        preview_size = 78
        preview_x = local_pos.x() + 18
        preview_y = local_pos.y() + 18

        if preview_x + preview_size > self.width():
            preview_x = local_pos.x() - preview_size - 18
        if preview_y + preview_size > self.height():
            preview_y = local_pos.y() - preview_size - 18

        color_name = qcolor_to_value(self.current_color)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawLine(local_pos.x() - 12, local_pos.y(), local_pos.x() - 4, local_pos.y())
        painter.drawLine(local_pos.x() + 4, local_pos.y(), local_pos.x() + 12, local_pos.y())
        painter.drawLine(local_pos.x(), local_pos.y() - 12, local_pos.x(), local_pos.y() - 4)
        painter.drawLine(local_pos.x(), local_pos.y() + 4, local_pos.x(), local_pos.y() + 12)

        painter.setBrush(QColor("#101114"))
        painter.setPen(QPen(QColor("#343849"), 1))
        painter.drawRoundedRect(preview_x, preview_y, preview_size, preview_size, 10, 10)

        painter.setBrush(self.current_color)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawRoundedRect(preview_x + 10, preview_y + 10, preview_size - 20, 34, 7, 7)

        painter.setPen(QColor("#f4f4f5"))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(preview_x + 10, preview_y + 58, color_name)

        painter.end()

    def stop(self):
        self.live_timer.stop()
        self.releaseMouse()
        self.releaseKeyboard()
        self.hide()
        self.deleteLater()

    def finish(self, color):
        self.stop()
        self.colorPicked.emit(color)

    def cancel(self):
        self.stop()
        self.cancelled.emit()


class ColorPickerInput(QWidget):
    colorChanged = Signal(str)

    def __init__(self, initial_color=None, parent=None):
        super().__init__(parent)
        self._current_color = QColor("#000000")
        self._current_value = "#000000"
        self._previous_value = "#000000"
        self._eyedropper = None
        self.setObjectName("ColorPickerInput")
        
        self.material_font = MaterialIcons.ensure_font()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.input = QLineEdit(self)
        self.input.setPlaceholderText("#000000 or #RRGGBBAA")
        self.input.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.input, 1)

        self.pick_button = QPushButton("palette", self)
        self.pick_button.setFont(QFont(self.material_font))
        self.pick_button.setToolTip("Open color picker")
        self.pick_button.clicked.connect(self.open_color_dialog)
        layout.addWidget(self.pick_button)

        self.eyedropper_button = QPushButton("colorize", self)
        self.eyedropper_button.setFont(QFont(self.material_font))
        self.eyedropper_button.setToolTip("Pick color from screen")
        self.eyedropper_button.clicked.connect(self.start_eyedropper)
        layout.addWidget(self.eyedropper_button)

        self.set_color(initial_color or "#000000", emit_signal=False)

    def open_color_dialog(self):
        color = QColorDialog.getColor(
            self._current_color,
            self,
            "Select Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if color.isValid():
            self.set_color(qcolor_to_value(color))

    def start_eyedropper(self):
        self._previous_value = self._current_value
        dialog = self.window()

        QTimer.singleShot(180, lambda: self.open_eyedropper(dialog))

    def open_eyedropper(self, dialog):
        self._eyedropper = ColorEyedropperOverlay(dialog)
        self._eyedropper.colorHovered.connect(self.preview_color)
        self._eyedropper.colorPicked.connect(self.finish_eyedropper)
        self._eyedropper.cancelled.connect(self.cancel_eyedropper)
        self._eyedropper.start()

    def preview_color(self, color):
        self.set_color(color)

    def finish_eyedropper(self, color):
        self.set_color(color)

    def cancel_eyedropper(self):
        self.set_color(self._previous_value)

    def on_text_changed(self, value):
        color = value_to_qcolor(value)
        if not color.isValid():
            return

        self._current_color = color
        self._current_value = str(value or "").strip()
        self.update_preview()
        self.colorChanged.emit(self._current_value)

    def set_color(self, value, emit_signal=True):
        value_text = str(value or "").strip()
        color = value_to_qcolor(value_text)
        color_value = qcolor_to_value(color)

        if value_text.startswith("#") and len(value_text[1:]) in (6, 8):
            color_value = value_text.lower()

        self._current_color = color
        self._current_value = color_value

        if self.input.text() != color_value:
            self.input.blockSignals(True)
            self.input.setText(color_value)
            self.input.blockSignals(False)

        self.update_preview()

        if emit_signal:
            self.colorChanged.emit(color_value)

    def update_preview(self):
        color_name = color_to_ui(self._current_value)
        text_color = "#ffffff" if self._current_color.lightnessF() < 0.5 else "#111827"

        self.pick_button.setStyleSheet(
            f"background: {color_name}; color: {text_color}; border: 1px solid #343849;"
        )

    def get_color(self):
        color = value_to_qcolor(self.input.text())
        if color.isValid():
            return str(self.input.text() or "").strip().lower()
        return self._current_value


class ColorFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = ColorPickerInput(value, parent)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.colorChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.get_color()

    def set_value(self, field, widget, value):
        widget.set_color(value)
