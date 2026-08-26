from PySide6.QtGui import QGuiApplication

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

ClipboardCategory = MacroCommandCategory("clipboard", "Clipboard", "mc:e14f")

def get_clipboard():
    clipboard = QGuiApplication.clipboard()
    if clipboard is None:
        raise RuntimeError("Clipboard is not available")
    return clipboard

def clear_clipboard_text():
    clipboard = get_clipboard()
    clipboard.clear()
    return {
        "cleared": True,
        "text": "",
    }

class ClearClipboardCommand(MacroCommand):
    id = "clipboard.clear"
    title = "Clear Clipboard"
    category = ClipboardCategory
    icon = "mc:e4f8"
    description = "Clear clipboard text."
    result_policy = ResultPolicy.VARIABLE
    fields = []

    def display_text(self, values=None):
        return "clear clipboard"

    def execute(self, values=None, runtime=None):
        if runtime is None or not hasattr(runtime, "ui") or runtime.ui is None:
            raise RuntimeError("Runtime UI is required for clipboard.clear")
        return runtime.ui.run(clear_clipboard_text)


def register_macro(registry):
    registry.register(ClearClipboardCommand)
