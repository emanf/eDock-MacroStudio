from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


KeyboardCategory = MacroCommandCategory("keyboard", "Keyboard", "m:keyboard")


class TypeTextCommand(MacroCommand):
    id = "keyboard.type_text"
    title = "Type Text"
    category = KeyboardCategory
    icon = "mc:e264"
    description = "Type text with keyboard."
    fields = [
        {
            "name": "text",
            "title": "Text",
            "place_holder": "Text to type",
            "value_type": "string",
            "default_value": "",
        },
        {
            "name": "interval",
            "title": "Interval",
            "place_holder": "Seconds between chars",
            "value_type": "float",
            "default_value": 0,
            "min_value": 0,
            "max_value": 10,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        text = str(values.get("text", ""))
        if len(text) > 40:
            text = text[:37] + "..."
        return f"type text: {text}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        text = str(values.get("text", "") or "")
        interval = float(values.get("interval", 0) or 0)
        speed = 1.0
        if runtime is not None:
            speed = max(0.05, float(getattr(runtime, "speed", 1.0) or 1.0))
        if runtime is None or not hasattr(runtime, "pyautogui_call"):
            raise RuntimeError("Runtime is required for keyboard.type_text")
        runtime.pyautogui_call("write", text, interval=interval / speed)
        return None


def register_macro(registry):
    registry.register(TypeTextCommand)
