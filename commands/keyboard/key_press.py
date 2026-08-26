from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


KeyboardCategory = MacroCommandCategory("keyboard", "Keyboard", "m:keyboard")


class KeyPressCommand(MacroCommand):
    id = "keyboard.key_press"
    title = "Key Press"
    category = KeyboardCategory
    icon = "m:keyboard"
    description = "Press one keyboard key."
    fields = [
        {
            "name": "key",
            "title": "Key",
            "place_holder": "enter, tab, esc, a, b...",
            "value_type": "string",
            "default_value": "enter",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"press key {values.get('key')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        key = str(values.get("key", "") or "")
        if runtime is None or not hasattr(runtime, "pyautogui_call"):
            raise RuntimeError("Runtime is required for keyboard.key_press")
        runtime.pyautogui_call("press", key)
        return None


def register_macro(registry):
    registry.register(KeyPressCommand)
