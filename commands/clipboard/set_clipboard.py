from PySide6.QtGui import QGuiApplication

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

ClipboardCategory = MacroCommandCategory("clipboard", "Clipboard", "mc:e14f")

def get_clipboard():
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        raise RuntimeError("Clipboard is not available")
    return clipboard

def set_clipboard_text(text):
    clipboard = get_clipboard()
    clipboard.setText(str(text or ""))
    return {
        "text": str(text or ""),
    }

class SetClipboardCommand(MacroCommand):
    id = "clipboard.set"
    title = "Set Clipboard"
    category = ClipboardCategory
    icon = "mc:e85d"
    description = "Set clipboard text."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "text_source",
            "title": "Text Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
        },
        {
            "name": "text",
            "required": False,
            "title": "Text",
            "place_holder": "Text to copy",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "text_variable",
            "required": False,
            "title": "Variable",
            "place_holder": "x or clipboard_text",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "variable",
            },
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        text_source = values.get("text_source")
        text_variable = values.get("text_variable")

        if text_source == "variable":
            return f"set clipboard from {text_variable}"

        text = str(values.get("text", "") or "")
        if len(text) > 40:
            text = text[:37] + "..."
        return f"set clipboard: {text}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        text_source = values.get("text_source")
        text_variable = values.get("text_variable")

        if text_source == "variable":
            text = runtime.vars.get(text_variable, "")
        else:
            text = values.get("text", "")

        text = str(text or "")

        if runtime is None or not hasattr(runtime, "ui") or runtime.ui is None:
            raise RuntimeError("Runtime UI is required for clipboard.set")
        return runtime.ui.run(set_clipboard_text, text)


def register_macro(registry):
    registry.register(SetClipboardCommand)
