from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


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


def get_text_from_source(values, runtime, source_field, text_field, variable_field):
    source = str(values.get(source_field, "string") or "string").strip().lower()
    if source == "variable":
        variable_name = str(values.get(variable_field, "") or "").strip()
        return str(runtime.vars.get(variable_name, "") or "")
    return str(values.get(text_field, "") or "")


def remove_message_box(box):
    remove_open_widget(box, _open_message_boxes)


def ask_confirmation_box(message, title="Confirm", yes_text="Yes", no_text="No", default_button="yes", wait=True):
    parent = active_parent()
    box = QMessageBox(parent)
    box.setWindowModality(Qt.WindowModality.WindowModal)
    box.setWindowTitle(str(title or "Confirm"))
    box.setText(str(message or ""))
    box.setIcon(QMessageBox.Icon.Question)
    box.setStyleSheet(MESSAGE_BOX_STYLE)
    yes_button = box.addButton(str(yes_text or "Yes"), QMessageBox.ButtonRole.YesRole)
    no_button = box.addButton(str(no_text or "No"), QMessageBox.ButtonRole.NoRole)
    if str(default_button or "yes").strip().lower() == "no":
        box.setDefaultButton(no_button)
    else:
        box.setDefaultButton(yes_button)
    if wait:
        box.exec()
        clicked = box.clickedButton()
        accepted = clicked == yes_button
        return {
            "confirmed": accepted,
            "button": "yes" if accepted else "no",
            "accepted": accepted,
        }
    _open_message_boxes.append(box)
    box.finished.connect(lambda: remove_message_box(box))
    box.show()
    return {
        "confirmed": False,
        "button": "",
        "accepted": False,
    }


def show_runtime_confirm(runtime, message, title="Confirm", yes_text="Yes", no_text="No", default_button="yes", wait=True):
    if runtime is not None and hasattr(runtime, "ui") and runtime.ui is not None:
        return runtime.ui.run(ask_confirmation_box, message, title, yes_text, no_text, default_button, wait)
    return ask_confirmation_box(message, title, yes_text, no_text, default_button, wait)


class ConfirmCommand(MacroCommand):
    id = "dialogs.confirm"
    title = "Confirm"
    category = DialogsCategory
    icon = "m:help"
    description = "Ask the user to confirm with yes or no."
    result_policy = ResultPolicy.DATA
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
            "default_value": "Do you want to continue?",
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
            "name": "title",
            "title": "Title",
            "value_type": "string",
            "default_value": "Confirm",
        },
        {
            "name": "yes_text",
            "title": "Yes Button Text",
            "value_type": "string",
            "default_value": "Yes",
        },
        {
            "name": "no_text",
            "title": "No Button Text",
            "value_type": "string",
            "default_value": "No",
        },
        {
            "name": "default_button",
            "title": "Default Button",
            "value_type": "choice",
            "default_value": "yes",
            "options": [
                {"title": "Yes", "value": "yes"},
                {"title": "No", "value": "no"},
            ],
        },
        {
            "name": "result_variable",
            "title": "Save Result To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"ask confirm: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        message = get_text_from_source(values, runtime, "message_source", "message", "message_variable")
        result = show_runtime_confirm(
            runtime,
            message,
            str(values.get("title", "Confirm") or "Confirm"),
            str(values.get("yes_text", "Yes") or "Yes"),
            str(values.get("no_text", "No") or "No"),
            str(values.get("default_button", "yes") or "yes"),
            True,
        )
        runtime.vars.set(values.get("result_variable", ""), result.get("confirmed", False))
        return result


def register_macro(registry):
    registry.register(ConfirmCommand)