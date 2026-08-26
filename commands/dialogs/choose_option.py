from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QApplication

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


class ChoiceInputDialog(QDialog):
    def __init__(self, title, message, options, default_value="", multi=False, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.multi = multi
        self.options = list(options or [])
        self.setWindowTitle(str(title or "Choose"))
        self.setMinimumWidth(FORM_MIN_WIDTH)
        self.setFixedWidth(FORM_MIN_WIDTH)
        self.setStyleSheet(FORM_STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        label = QLabel(str(message or ""), self)
        label.setWordWrap(True)
        root.addWidget(label)
        self.list_widget = QListWidget(self)
        selection_mode = QListWidget.SelectionMode.MultiSelection if multi else QListWidget.SelectionMode.SingleSelection
        self.list_widget.setSelectionMode(selection_mode)
        default_values = set(to_string_list(default_value)) if multi else {str(default_value or "").strip()}
        for option in self.options:
            item = QListWidgetItem(str(option.get("title", "") or ""))
            item.setData(Qt.ItemDataRole.UserRole, str(option.get("value", "") or ""))
            self.list_widget.addItem(item)
            option_value = str(option.get("value", "") or "")
            option_title = str(option.get("title", "") or "")
            if multi:
                if option_value in default_values or option_title in default_values:
                    item.setSelected(True)
            else:
                selected_value = next(iter(default_values), "")
                if option_value == selected_value or option_title == selected_value:
                    item.setSelected(True)
        root.addWidget(self.list_widget)
        buttons = QDialogButtonBox(self)
        cancel_button = buttons.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        ok_button = buttons.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self.accept)
        root.addWidget(buttons)
        self.list_widget.setFocus()

    def value(self):
        items = self.list_widget.selectedItems()
        if self.multi:
            return [str(item.data(Qt.ItemDataRole.UserRole) or "") for item in items]
        if not items:
            return ""
        return str(items[0].data(Qt.ItemDataRole.UserRole) or "")


def show_choice_input_dialog(title, message, options, default_value="", multi=False):
    dialog = ChoiceInputDialog(title, message, options, default_value, multi, active_parent())
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return {"accepted": True, "value": dialog.value()}
    return {"accepted": False, "value": [] if multi else ""}


class ChooseOptionCommand(MacroCommand):
    id = "dialogs.choose_option"
    title = "Choose Option"
    category = DialogsCategory
    icon = "m:list"
    description = "Let the user choose one option."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "title",
            "title": "Title",
            "value_type": "string",
            "default_value": "Choose Option",
        },
        {
            "name": "message",
            "title": "Message",
            "value_type": "string",
            "default_value": "Please choose one option",
        },
        {
            "name": "options_text",
            "title": "Options",
            "value_type": "textarea",
            "default_value": "Option 1\nOption 2\nOption 3",
        },
        {
            "name": "default_value",
            "title": "Default Value",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "result_variable",
            "title": "Save Selected Option To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"choose option: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        options = to_option_items(str(values.get("options_text", "") or "").splitlines())
        result = run_on_ui(
            runtime,
            show_choice_input_dialog,
            str(values.get("title", "Choose Option") or "Choose Option"),
            str(values.get("message", "") or ""),
            options,
            str(values.get("default_value", "") or ""),
            False,
        )
        if result.get("accepted", False):
            runtime.vars.set(values.get("result_variable", ""), result.get("value", ""))
        return result


def register_macro(registry):
    registry.register(ChooseOptionCommand)