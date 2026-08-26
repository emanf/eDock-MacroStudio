from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand


ClipboardCategory = MacroCommandCategory("clipboard", "Clipboard", "mc:e14f")


class PasteClipboardCommand(MacroCommand):
    id = "clipboard.paste"
    title = "Paste Clipboard"
    category = ClipboardCategory
    icon = "mc:e862"
    description = "Paste clipboard text with keyboard shortcut."
    fields = []

    def display_text(self, values=None):
        return "paste clipboard"

    def execute(self, values=None, runtime=None):
        if runtime is None or not hasattr(runtime, "pyautogui_call"):
            raise RuntimeError("Runtime is required for clipboard.paste")
        runtime.pyautogui_call("hotkey", "ctrl", "v")
        return None


def register_macro(registry):
    registry.register(PasteClipboardCommand)
