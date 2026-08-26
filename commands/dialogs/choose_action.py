from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QApplication

from ...ui.forms.form_builder import FORM_MIN_WIDTH, FORM_STYLE
from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


DialogsCategory = MacroCommandCategory("dialogs", "Dialogs", "m:chat")


def active_parent():
    return QApplication.activeWindow()


def run_on_ui(runtime, callback, *args):
    if runtime is not None and hasattr(runtime, "ui") and runtime.ui is not None:
        return runtime.ui.run(callback, *args)
    return callback(*args)


def to_string_list(value):
    if isinstance(value, list):
        result = []
        for item in value:
            text = str(item or "").strip()
            if text:
                result.append(text)
        return result
    text = str(value or "").strip()
    if not text:
        return []
    parts = [part.strip() for part in text.replace("\n", ",").split(",")]
    return [part for part in parts if part]


def to_option_items(value):
    items = []
    raw_items = value if isinstance(value, list) else to_string_list(value)
    for item in raw_items:
        if isinstance(item, dict):
            title = str(item.get("title", item.get("label", item.get("value", ""))) or "").strip()
            item_value = str(item.get("value", title) or "").strip()
        else:
            title = str(item or "").strip()
            item_value = title
        if title:
            items.append({
                "title": title,
                "value": item_value,
            })
    return items


class ActionDialog(QDialog):
    def __init__(self, title, message, actions, default_action="", parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.actions = list(actions or [])
        self.selected_action = ""
        self.setWindowTitle(str(title or "Choose Action"))
        self.setMinimumWidth(FORM_MIN_WIDTH)
        self.setFixedWidth(FORM_MIN_WIDTH)
        self.setStyleSheet(FORM_STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        label = QLabel(str(message or ""), self)
        label.setWordWrap(True)
        root.addWidget(label)
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        for action in self.actions:
            title_text = str(action.get("title", action.get("value", "")) or "").strip()
            value_text = str(action.get("value", title_text) or "").strip()
            if not title_text:
                continue
            button = QPushButton(title_text, self)
            if value_text == str(default_action or "").strip():
                button.setDefault(True)
            button.clicked.connect(lambda checked=False, action_value=value_text: self.select_action(action_value))
            buttons_row.addWidget(button)
        root.addLayout(buttons_row)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)
        root.addWidget(cancel_button)

    def select_action(self, value):
        self.selected_action = str(value or "")
        self.accept()

    def value(self):
        return self.selected_action


def show_action_dialog(title, message, actions, default_action=""):
    dialog = ActionDialog(title, message, actions, default_action, active_parent())
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return {"accepted": True, "value": dialog.value()}
    return {"accepted": False, "value": ""}


class ChooseActionCommand(MacroCommand):
    id = "dialogs.choose_action"
    title = "Choose Action"
    category = DialogsCategory
    icon = "mc:e919"
    description = "Show multiple action buttons and return selected action."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "title",
            "title": "Title",
            "value_type": "string",
            "default_value": "Choose Action",
        },
        {
            "name": "message",
            "title": "Message",
            "value_type": "string",
            "default_value": "Select an action",
        },
        {
            "name": "actions_text",
            "title": "Actions",
            "value_type": "textarea",
            "default_value": "Continue\nRetry\nSkip\nStop",
        },
        {
            "name": "default_action",
            "title": "Default Action",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "result_variable",
            "title": "Save Selected Action To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"choose action: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        actions = to_option_items(str(values.get("actions_text", "") or "").splitlines())
        result = run_on_ui(
            runtime,
            show_action_dialog,
            str(values.get("title", "Choose Action") or "Choose Action"),
            str(values.get("message", "") or ""),
            actions,
            str(values.get("default_action", "") or ""),
        )
        if result.get("accepted", False):
            runtime.vars.set(values.get("result_variable", ""), result.get("value", ""))
        return result


def register_macro(registry):
    registry.register(ChooseActionCommand)