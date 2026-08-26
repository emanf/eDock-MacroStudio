from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


MouseCategory = MacroCommandCategory("mouse", "Mouse", "m:mouse")


class MouseScrollCommand(MacroCommand):
    id = "mouse.scroll"
    title = "Mouse Scroll"
    category = MouseCategory
    icon = "mc:eb2e"
    description = "Scroll mouse wheel."
    fields = [
        {
            "name": "amount",
            "title": "Amount",
            "place_holder": "Positive or negative",
            "value_type": "integer",
            "default_value": -5,
            "min_value": -9999,
            "max_value": 9999,
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"scroll mouse by {values.get('amount')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        amount = int(values.get("amount", 0) or 0)
        if runtime is None or not hasattr(runtime, "pyautogui_call"):
            raise RuntimeError("Runtime is required for mouse.scroll")
        runtime.pyautogui_call("scroll", amount)
        return None


def register_macro(registry):
    registry.register(MouseScrollCommand)
