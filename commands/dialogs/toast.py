from PySide6.QtCore import QTimer, Qt, QPoint, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PySide6.QtGui import QFont

from core.rendering.material_icons import MaterialIcons

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand


DialogsCategory = MacroCommandCategory("dialogs", "Dialogs", "m:chat")

_open_toasts = []
_toast_queue = []
_toast_active = None

TOAST_STYLE = """
QDialog {
    background: transparent;
}
QFrame#ToastFrame {
    border-radius: 22px;
}
QFrame#ToastFrame[toastTheme="green"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(32, 181, 33, 248), stop: 1 rgba(26, 150, 22, 248));
    border: 1px solid rgba(43, 118, 46, 170);
}
QFrame#ToastFrame[toastTheme="red"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(201, 70, 67, 248), stop: 1 rgba(180, 61, 58, 248));
    border: 1px solid rgba(134, 48, 46, 170);
}
QFrame#ToastFrame[toastTheme="orange"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(238, 152, 0, 248), stop: 1 rgba(226, 142, 0, 248));
    border: 1px solid rgba(152, 101, 12, 170);
}
QFrame#ToastFrame[toastTheme="blue"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(59, 130, 246, 248), stop: 1 rgba(37, 99, 235, 248));
    border: 1px solid rgba(30, 64, 175, 170);
}
QFrame#ToastFrame[toastTheme="light"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(255, 255, 255, 252), stop: 1 rgba(241, 245, 249, 252));
    border: 1px solid rgba(148, 163, 184, 150);
}
QFrame#ToastFrame[toastTheme="dark"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 rgba(63, 71, 86, 252), stop: 1 rgba(46, 54, 68, 252));
    border: 1px solid rgba(148, 163, 184, 90);
}
QLabel#ToastIcon {
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    border-radius: 16px;
    font-size: 16px;
    font-weight: 400;
    padding: 0px;
    border: none;
}
QLabel#ToastIcon[toastTheme="green"] {
    background-color: rgba(137, 219, 101, 255);
    color: rgba(34, 94, 20, 255);
    border: none;
}
QLabel#ToastIcon[toastTheme="red"] {
    background-color: rgba(239, 109, 101, 255);
    color: rgba(120, 30, 28, 255);
    border: none;
}
QLabel#ToastIcon[toastTheme="orange"] {
    background-color: rgba(255, 211, 122, 255);
    color: rgba(133, 77, 6, 255);
    border: none;
}
QLabel#ToastIcon[toastTheme="blue"] {
    background-color: rgba(147, 197, 253, 255);
    color: rgba(30, 64, 175, 255);
    border: none;
}
QLabel#ToastIcon[toastTheme="light"] {
    background-color: rgba(226, 232, 240, 255);
    color: rgba(15, 23, 42, 255);
    border: none;
}
QLabel#ToastIcon[toastTheme="dark"] {
    background-color: rgba(226, 232, 240, 255);
    color: rgba(51, 65, 85, 255);
    border: none;
}
QLabel#ToastLabel {
    font-size: 14px;
    font-weight: 800;
    background: transparent;
    border: none;
}
QLabel#ToastLabel[toastTheme="green"],
QLabel#ToastLabel[toastTheme="red"],
QLabel#ToastLabel[toastTheme="orange"],
QLabel#ToastLabel[toastTheme="blue"],
QLabel#ToastLabel[toastTheme="dark"] {
    color: #ffffff;
}
QLabel#ToastLabel[toastTheme="light"] {
    color: #0f172a;
}
"""


def remove_open_widget(widget, collection):
    if widget in collection:
        collection.remove(widget)


def get_text_from_source(values, runtime, source_field, text_field, variable_field):
    source = str(values.get(source_field, "string") or "string").strip().lower()
    if source == "variable":
        variable_name = str(values.get(variable_field, "") or "").strip()
        value = runtime.vars.get(variable_name, "")
        if value is None:
            return ""
        return str(value)
    value = values.get(text_field, "")
    if value is None:
        return ""
    return str(value)


def run_on_ui(runtime, callback, *args):
    if runtime is not None and hasattr(runtime, "ui") and runtime.ui is not None:
        return runtime.ui.run(callback, *args)
    return callback(*args)


def show_next_toast():
    global _toast_active

    if _toast_active is not None:
        return

    if not _toast_queue:
        return

    message, duration_ms, theme, click_to_close, icon = _toast_queue.pop(0)
    toast = ToastDialog(message, duration_ms, None, "top", theme, click_to_close, icon)
    _toast_active = toast
    _open_toasts.append(toast)
    toast.show()


def show_toast_dialog(message, duration_ms=2500, theme="dark", click_to_close=True, icon=""):
    _toast_queue.append((message, duration_ms, theme, click_to_close, icon))
    show_next_toast()
    return {"accepted": True}


class ToastDialog(QDialog):
    def __init__(self, message, duration_ms=2500, parent=None, side="top", theme="dark", click_to_close=True, icon=""):
        super().__init__(parent)
        self.duration_ms = max(500, int(duration_ms or 2500))
        self.side = str(side or "top").strip().lower()
        if self.side not in ("top", "bottom"):
            self.side = "top"

        self.theme = str(theme or "dark").strip().lower()
        if self.theme not in ("green", "red", "orange", "blue", "light", "dark"):
            self.theme = "dark"

        self.click_to_close = bool(click_to_close)
        self.icon_value = str(icon or "").strip()
        self._closing = False
        self._animation_group = None
        self._close_timer = None

        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(TOAST_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.frame = QFrame(self)
        self.frame.setObjectName("ToastFrame")
        self.frame.setProperty("toastTheme", self.theme)

        self.opacity_effect = QGraphicsOpacityEffect(self.frame)
        self.opacity_effect.setOpacity(0)
        self.frame.setGraphicsEffect(self.opacity_effect)

        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(8, 7, 18, 7)
        frame_layout.setSpacing(10)

        self.icon = QLabel(self.resolve_icon_text(), self.frame)
        self.icon.setObjectName("ToastIcon")
        self.icon.setProperty("toastTheme", self.theme)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setFixedSize(32, 32)

        icon_font = QFont(MaterialIcons.font_family())
        icon_font.setPixelSize(16)
        icon_font.setWeight(QFont.Weight.Normal)
        self.icon.setFont(icon_font)

        self.label = QLabel(str(message or ""), self.frame)
        self.label.setObjectName("ToastLabel")
        self.label.setProperty("toastTheme", self.theme)
        self.label.setWordWrap(True)
        self.label.setMinimumWidth(220)
        self.label.setMaximumWidth(420)

        frame_layout.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignVCenter)
        frame_layout.addWidget(self.label, 1)
        root.addWidget(self.frame)

    def resolve_icon_text(self):
        if self.icon_value:
            icon = MaterialIcons.get(self.icon_value, "")
            if icon:
                return icon

        defaults = {
            "green": "m:check",
            "red": "m:bolt",
            "orange": "m:warning",
            "blue": "m:info",
            "light": "m:info",
            "dark": "m:notifications",
        }
        return MaterialIcons.get(defaults.get(self.theme, "m:notifications"), "")

    def mousePressEvent(self, event):
        if self.click_to_close:
            self.close_toast()
        super().mousePressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
        self.animate_in()

        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self.close_toast)
        self._close_timer.start(self.duration_ms)

    def closeEvent(self, event):
        global _toast_active

        if not self._closing:
            event.ignore()
            self.close_toast()
            return

        remove_open_widget(self, _open_toasts)

        if _toast_active is self:
            _toast_active = None
            QTimer.singleShot(120, show_next_toast)

        super().closeEvent(event)

    def target_position(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return QPoint(0, 0)

        geometry = screen.availableGeometry()
        x = geometry.x() + int((geometry.width() - self.width()) / 2)

        if self.side == "bottom":
            y = geometry.y() + geometry.height() - self.height() - 28
        else:
            y = geometry.y() + 28

        return QPoint(x, y)

    def hidden_position(self):
        target = self.target_position()

        if self.side == "bottom":
            return QPoint(target.x(), target.y() + 18)

        return QPoint(target.x(), max(0, target.y() - 18))

    def animate_in(self):
        start_pos = self.hidden_position()
        end_pos = self.target_position()

        self.move(start_pos)
        self.opacity_effect.setOpacity(0)

        pos_animation = QPropertyAnimation(self, b"pos", self)
        pos_animation.setDuration(360)
        pos_animation.setStartValue(start_pos)
        pos_animation.setEndValue(end_pos)
        pos_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        opacity_animation.setDuration(260)
        opacity_animation.setStartValue(0)
        opacity_animation.setEndValue(1)
        opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._animation_group = QParallelAnimationGroup(self)
        self._animation_group.addAnimation(pos_animation)
        self._animation_group.addAnimation(opacity_animation)
        self._animation_group.start()

    def close_toast(self):
        if self._closing:
            return

        self._closing = True

        if self._close_timer is not None:
            self._close_timer.stop()

        start_pos = self.pos()
        end_pos = self.hidden_position()

        pos_animation = QPropertyAnimation(self, b"pos", self)
        pos_animation.setDuration(320)
        pos_animation.setStartValue(start_pos)
        pos_animation.setEndValue(end_pos)
        pos_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        opacity_animation = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        opacity_animation.setDuration(240)
        opacity_animation.setStartValue(self.opacity_effect.opacity())
        opacity_animation.setEndValue(0)
        opacity_animation.setEasingCurve(QEasingCurve.Type.InCubic)

        self._animation_group = QParallelAnimationGroup(self)
        self._animation_group.addAnimation(pos_animation)
        self._animation_group.addAnimation(opacity_animation)
        self._animation_group.finished.connect(self.close)
        self._animation_group.start()


class ToastCommand(MacroCommand):
    id = "dialogs.toast"
    title = "Show Toast"
    category = DialogsCategory
    icon = "mc:e578"
    description = "Show a temporary toast message."
    fields = [
        {
            "name": "message_source",
            "title": "Message Source",
            "value_type": "choice",
            "default_value": "string",
            "options": [
                {"title": "String", "value": "string"},
                {"title": "Variable", "value": "variable"},
            ],
        },
        {
            "name": "message",
            "title": "Message",
            "value_type": "string",
            "default_value": "Done",
            "visible_if": {"field": "message_source", "operator": "==", "value": "string"},
        },
        {
            "name": "message_variable",
            "title": "Message Variable",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {"field": "message_source", "operator": "==", "value": "variable"},
        },
        {
            "name": "duration_ms",
            "title": "Duration (ms)",
            "value_type": "int",
            "default_value": 2500,
        },
        {
            "name": "theme",
            "title": "Theme",
            "value_type": "choice",
            "default_value": "dark",
            "options": [
                {"title": "Green", "value": "green"},
                {"title": "Red", "value": "red"},
                {"title": "Orange", "value": "orange"},
                {"title": "Blue", "value": "blue"},
                {"title": "Light", "value": "light"},
                {"title": "Dark", "value": "dark"},
            ],
        },
        {
            "name": "icon",
            "title": "Icon",
            "value_type": "string",
            "default_value": "m:info",
            "place_holder": "m:info or mc:e88e",
        },
        {
            "name": "click_to_close",
            "title": "Click To Close",
            "value_type": "bool",
            "default_value": True,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        message_source = str(
            values.get("message_source", "string") or "string"
        ).strip().lower()

        if message_source == "variable":
            variable_name = str(
                values.get("message_variable", "") or ""
            ).strip()
            return f"show toast from variable: ({variable_name})"

        message_value = values.get("message", "")
        message = "" if message_value is None else str(message_value)
        return f"show toast: {message}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        message = get_text_from_source(values, runtime, "message_source", "message", "message_variable")
        return run_on_ui(
            runtime,
            show_toast_dialog,
            message,
            int(values.get("duration_ms", 2500) or 2500),
            str(values.get("theme", "dark") or "dark"),
            runtime.helper.parse_bool(values.get("click_to_close", True)),
            str(values.get("icon", "") or ""),
        )


def register_macro(registry):
    registry.register(ToastCommand)
