from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand


DialogsCategory = MacroCommandCategory("dialogs", "Dialogs", "m:chat")

_open_message_boxes = []

MESSAGE_BOX_STYLE = """
QMessageBox {
    background: #17191f;
}
QMessageBox QLabel {
    color: #f4f4f5;
    font-size: 13px;
}
QMessageBox QPushButton {
    background: #2563eb;
    border: 1px solid #2563eb;
    border-radius: 10px;
    padding: 9px 18px;
    color: white;
    min-width: 72px;
}
QMessageBox QPushButton:hover {
    background: #1d4ed8;
    border-color: #1d4ed8;
}
QMessageBox QPushButton:pressed {
    background: #1e40af;
    border-color: #1e40af;
}
"""


def active_parent():
    return QApplication.activeWindow()


def remove_open_widget(widget, collection):
    if widget in collection:
        collection.remove(widget)


def parse_bool_value(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    if value is None:
        return False

    text = str(value).strip().lower()
    return text in ["true", "1", "yes", "on", "checked", "enabled"]


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


def remove_message_box(box):
    remove_open_widget(box, _open_message_boxes)


def create_message_box(message, title="Macro Message", icon=QMessageBox.Icon.Information, rich=False):
    parent = active_parent()
    box = QMessageBox(parent)
    box.setWindowModality(Qt.WindowModality.WindowModal)
    title_value = "Message" if title is None else str(title)
    message_value = "" if message is None else str(message)
    box.setWindowTitle(title_value)
    box.setTextFormat(Qt.TextFormat.RichText if rich else Qt.TextFormat.PlainText)
    box.setText(message_value)
    box.setIcon(icon)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.setStyleSheet(MESSAGE_BOX_STYLE)
    box.setMinimumWidth(360)
    ok_button = box.button(QMessageBox.StandardButton.Ok)
    if ok_button is not None:
        ok_button.setObjectName("Primary")
        ok_button.setText("OK")
    return box


def show_message_box(message, wait=False, title="Macro Message", icon=QMessageBox.Icon.Information, rich=False):
    app = QApplication.instance()
    if app is None:
        return None
    box = create_message_box(message, title, icon, rich)
    if wait:
        box.exec()
        return {"button": "ok", "accepted": True}
    _open_message_boxes.append(box)
    box.finished.connect(lambda: remove_message_box(box))
    box.show()
    return {"button": "ok", "accepted": True}


def show_runtime_message(runtime, message, wait=False, title="Macro Message", icon=QMessageBox.Icon.Information, rich=False):
    if runtime is not None and hasattr(runtime, "ui") and runtime.ui is not None:
        return runtime.ui.run(show_message_box, message, wait, title, icon, rich)
    return show_message_box(message, wait, title, icon, rich)


class MessageCommand(MacroCommand):
    id = "dialogs.message"
    title = "Message"
    category = DialogsCategory
    icon = "m:message"
    description = "Show a message during macro execution."
    fields = [
        {
            "name": "message_source",
            "title": "Source",
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
            "place_holder": "Message text",
            "value_type": "string",
            "default_value": "Hello from Macro Studio",
            "visible_if": {"field": "message_source", "operator": "==", "value": "string"},
        },
        {
            "name": "message_variable",
            "title": "Variable",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {"field": "message_source", "operator": "==", "value": "variable"},
        },
        {
            "name": "wait_until_closed",
            "title": "Wait until the message is closed",
            "value_type": "boolean",
            "default_value": False,
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        wait_until_closed = parse_bool_value(values.get("wait_until_closed", False))
        wait_text = "Wait for user to close" if wait_until_closed else "Continue immediately"
        message_source = str(values.get("message_source", "string") or "string").strip().lower()

        if message_source == "variable":
            message_variable = values.get("message_variable")
            message_variable_text = "" if message_variable is None else str(message_variable).strip()
            if not message_variable_text:
                message_variable_text = "No variable selected"
            return f"Show message from variable ({message_variable_text}) - {wait_text}"

        message = values.get("message")
        message_text = "" if message is None else str(message)
        if not message_text.strip():
            message_text = "Empty message"
        return f"Show message: {message_text} - {wait_text}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        message = get_text_from_source(values, runtime, "message_source", "message", "message_variable")
        wait_until_closed = runtime.helper.parse_bool(values.get("wait_until_closed", False))
        return show_runtime_message(runtime, message, wait_until_closed)


def register_macro(registry):
    registry.register(MessageCommand)
