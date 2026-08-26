from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QLabel, QVBoxLayout, QApplication

from ...ui.forms.form_builder import FORM_MIN_WIDTH, FORM_STYLE
from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


DialogsCategory = MacroCommandCategory("dialogs", "Dialogs", "m:chat")


def active_parent():
    return QApplication.activeWindow()


def get_text_from_source(values, runtime, source_field, text_field, variable_field):
    source = str(values.get(source_field, "string") or "string").strip().lower()
    if source == "variable":
        variable_name = str(values.get(variable_field, "") or "").strip()
        return str(runtime.vars.get(variable_name, "") or "")
    return str(values.get(text_field, "") or "")


def run_on_ui(runtime, callback, *args):
    if runtime is not None and hasattr(runtime, "ui") and runtime.ui is not None:
        return runtime.ui.run(callback, *args)
    return callback(*args)


class TextInputDialog(QDialog):
    def __init__(self, title, message, default_value="", placeholder="", password=False, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle(str(title or "Input"))
        self.setMinimumWidth(FORM_MIN_WIDTH)
        self.setFixedWidth(FORM_MIN_WIDTH)
        self.setStyleSheet(FORM_STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        label = QLabel(str(message or ""), self)
        label.setWordWrap(True)
        root.addWidget(label)
        self.input = QLineEdit(self)
        self.input.setPlaceholderText(str(placeholder or ""))
        self.input.setText(str(default_value or ""))
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        root.addWidget(self.input)
        buttons = QDialogButtonBox(self)
        cancel_button = buttons.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        ok_button = buttons.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self.accept)
        root.addWidget(buttons)
        self.input.selectAll()
        self.input.setFocus()

    def value(self):
        return self.input.text()


def show_text_input_dialog(title, message, default_value="", placeholder="", password=False):
    dialog = TextInputDialog(title, message, default_value, placeholder, password, active_parent())
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return {"accepted": True, "value": dialog.value()}
    return {"accepted": False, "value": ""}


class AskTextCommand(MacroCommand):
    id = "dialogs.ask_text"
    title = "Ask Text"
    category = DialogsCategory
    icon = "mc:e94c"
    description = "Ask the user to enter text."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "title",
            "title": "Title",
            "value_type": "string",
            "default_value": "Input Text",
        },
        {
            "name": "message",
            "title": "Message",
            "value_type": "string",
            "default_value": "Please enter a value",
        },
        {
            "name": "default_value_source",
            "title": "Default Value Source",
            "value_type": "choice",
            "default_value": "string",
            "options": [
                {"title": "String", "value": "string"},
                {"title": "Variable", "value": "variable"},
            ],
        },
        {
            "name": "default_value",
            "title": "Default Value",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "visible_if": {"field": "default_value_source", "operator": "==", "value": "string"},
        },
        {
            "name": "default_value_variable",
            "title": "Default Value Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
            "visible_if": {"field": "default_value_source", "operator": "==", "value": "variable"},
        },
        {
            "name": "placeholder",
            "title": "Placeholder",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "result_variable",
            "title": "Save Text To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"ask text: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        default_value = get_text_from_source(values, runtime, "default_value_source", "default_value", "default_value_variable")
        result = run_on_ui(
            runtime,
            show_text_input_dialog,
            str(values.get("title", "Input Text") or "Input Text"),
            str(values.get("message", "") or ""),
            default_value,
            str(values.get("placeholder", "") or ""),
            False,
        )
        if result.get("accepted", False):
            runtime.vars.set(values.get("result_variable", ""), result.get("value", ""))
        return result


def register_macro(registry):
    registry.register(AskTextCommand)