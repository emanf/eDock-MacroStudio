from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QSpinBox, QDoubleSpinBox, QVBoxLayout, QApplication

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


class NumberInputDialog(QDialog):
    def __init__(self, title, message, default_value=0, minimum=0, maximum=999999999, step=1, allow_float=False, decimals=2, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowTitle(str(title or "Input Number"))
        self.setMinimumWidth(FORM_MIN_WIDTH)
        self.setFixedWidth(FORM_MIN_WIDTH)
        self.setStyleSheet(FORM_STYLE)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)
        label = QLabel(str(message or ""), self)
        label.setWordWrap(True)
        root.addWidget(label)
        if allow_float:
            self.input = QDoubleSpinBox(self)
            self.input.setDecimals(max(0, int(decimals or 0)))
            self.input.setSingleStep(float(step or 1))
            self.input.setMinimum(float(minimum))
            self.input.setMaximum(float(maximum))
            self.input.setValue(float(default_value or 0))
        else:
            self.input = QSpinBox(self)
            self.input.setSingleStep(max(1, int(step or 1)))
            self.input.setMinimum(int(minimum))
            self.input.setMaximum(int(maximum))
            self.input.setValue(int(default_value or 0))
        root.addWidget(self.input)
        buttons = QDialogButtonBox(self)
        cancel_button = buttons.addButton("Cancel", QDialogButtonBox.ButtonRole.RejectRole)
        ok_button = buttons.addButton("OK", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self.accept)
        root.addWidget(buttons)
        self.input.setFocus()

    def value(self):
        return self.input.value()


def show_number_input_dialog(title, message, default_value=0, minimum=0, maximum=999999999, step=1, allow_float=False, decimals=2):
    dialog = NumberInputDialog(title, message, default_value, minimum, maximum, step, allow_float, decimals, active_parent())
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return {"accepted": True, "value": dialog.value()}
    return {"accepted": False, "value": None}


class AskNumberCommand(MacroCommand):
    id = "dialogs.ask_number"
    title = "Ask Number"
    category = DialogsCategory
    icon = "mc:e94c"
    description = "Ask the user to enter a number."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "title",
            "title": "Title",
            "value_type": "string",
            "default_value": "Input Number",
        },
        {
            "name": "message",
            "title": "Message",
            "value_type": "string",
            "default_value": "Please enter a number",
        },
        {
            "name": "number_type",
            "title": "Number Type",
            "value_type": "choice",
            "default_value": "int",
            "options": [
                {"title": "Integer", "value": "int"},
                {"title": "Float", "value": "float"},
            ],
        },
        {
            "name": "default_value",
            "title": "Default Value",
            "value_type": "float",
            "default_value": 0,
        },
        {
            "name": "minimum",
            "title": "Minimum",
            "value_type": "float",
            "default_value": 0,
        },
        {
            "name": "maximum",
            "title": "Maximum",
            "value_type": "float",
            "default_value": 999999999,
        },
        {
            "name": "step",
            "title": "Step",
            "value_type": "float",
            "default_value": 1,
        },
        {
            "name": "decimals",
            "title": "Decimals",
            "value_type": "int",
            "default_value": 2,
            "visible_if": {"field": "number_type", "operator": "==", "value": "float"},
        },
        {
            "name": "result_variable",
            "title": "Save Number To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"ask number: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        allow_float = str(values.get("number_type", "int") or "int").strip().lower() == "float"
        result = run_on_ui(
            runtime,
            show_number_input_dialog,
            str(values.get("title", "Input Number") or "Input Number"),
            str(values.get("message", "") or ""),
            float(values.get("default_value", 0) or 0),
            float(values.get("minimum", 0) or 0),
            float(values.get("maximum", 999999999) or 999999999),
            float(values.get("step", 1) or 1),
            allow_float,
            int(values.get("decimals", 2) or 2),
        )
        if result.get("accepted", False):
            value = result.get("value", 0)
            if not allow_float:
                value = int(value or 0)
            runtime.vars.set(values.get("result_variable", ""), value)
            result["value"] = value
        return result


def register_macro(registry):
    registry.register(AskNumberCommand)