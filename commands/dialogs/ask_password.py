from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QLabel, QVBoxLayout, QApplication

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


class AskPasswordCommand(MacroCommand):
    id = "dialogs.ask_password"
    title = "Ask Password"
    category = DialogsCategory
    icon = "mc:f042"
    description = "Ask the user to enter a hidden password."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "title",
            "title": "Title",
            "value_type": "string",
            "default_value": "Input Password",
        },
        {
            "name": "message",
            "title": "Message",
            "value_type": "string",
            "default_value": "Please enter your password",
        },
        {
            "name": "default_value",
            "title": "Default Value",
            "value_type": "string",
            "default_value": "",
            "required": False,
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
            "title": "Save Password To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"ask password: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        result = run_on_ui(
            runtime,
            show_text_input_dialog,
            str(values.get("title", "Input Password") or "Input Password"),
            str(values.get("message", "") or ""),
            str(values.get("default_value", "") or ""),
            str(values.get("placeholder", "") or ""),
            True,
        )
        if result.get("accepted", False):
            runtime.vars.set(values.get("result_variable", ""), result.get("value", ""))
        return result


def register_macro(registry):
    registry.register(AskPasswordCommand)