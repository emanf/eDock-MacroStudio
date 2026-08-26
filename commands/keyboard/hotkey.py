from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


KeyboardCategory = MacroCommandCategory("keyboard", "Keyboard", "m:keyboard")


class HotkeyCommand(MacroCommand):
    id = "keyboard.hotkey"
    title = "Hotkey"
    category = KeyboardCategory
    icon = "m:bolt"
    description = "Press a keyboard shortcut."
    fields = [
        {
            "name": "keys",
            "title": "Keys",
            "place_holder": "ctrl+shift+s",
            "value_type": "string",
            "default_value": "ctrl+s",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"press hotkey {values.get('keys')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        keys = str(values.get("keys", "") or "")
        parts = [p.strip() for p in keys.replace(",", "+").split("+") if p.strip()]
        if not parts:
            return None
        if runtime is None or not hasattr(runtime, "pyautogui_call"):
            raise RuntimeError("Runtime is required for keyboard.hotkey")
        runtime.pyautogui_call("hotkey", *parts)
        return None


def register_macro(registry):
    registry.register(HotkeyCommand)
