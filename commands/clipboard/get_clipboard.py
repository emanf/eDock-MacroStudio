from PySide6.QtGui import QGuiApplication

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


ClipboardCategory = MacroCommandCategory("clipboard", "Clipboard", "mc:e14f")


def get_clipboard():
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        raise RuntimeError("Clipboard is not available")
    return clipboard

def get_clipboard_text():
    clipboard = get_clipboard()
    return {
        "text": clipboard.text() or "",
    }

class GetClipboardCommand(MacroCommand):
    id = "clipboard.get"
    title = "Get Clipboard"
    category = ClipboardCategory
    icon = "mc:ea8e"
    description = "Get clipboard text."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "variable_name",
            "title": "Save To Variable",
            "place_holder": "clipboard_text",
            "value_type": "variable",
            "default_value": "",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")

        if variable_name:
            return f"get clipboard to {variable_name}"

        return "get clipboard"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")

        if runtime is None or not hasattr(runtime, "ui") or runtime.ui is None:
            raise RuntimeError("Runtime UI is required for clipboard.get")

        result = runtime.ui.run(get_clipboard_text)

        if variable_name:
            runtime.vars.set(variable_name, result.get("text", ""))

        return result


def register_macro(registry):
    registry.register(GetClipboardCommand)
