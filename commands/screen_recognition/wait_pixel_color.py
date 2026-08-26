import time

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


ScreenRecognitionCategory = MacroCommandCategory("screen_recognition", "Screen Recognition", "m:visibility")


class WaitPixelColorCommand(MacroCommand):
    id = "screen_recognition.wait_pixel_color"
    title = "Wait Pixel Color"
    category = ScreenRecognitionCategory
    icon = "mc:e3b8"
    description = "Wait until a pixel matches a color."
    fields = [
        {
            "name": "color",
            "title": "Color",
            "place_holder": "#ffffff",
            "value_type": "color",
            "default_value": "#ffffff",
        },
        {
            "name": "position_type",
            "title": "Position Type",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "position",
            "title": "Position",
            "place_holder": "Screen X, Y",
            "value_type": "mouse_position",
            "default_value": {
                "x": 0,
                "y": 0,
            },
            "visible_if": {
                "field": "position_type",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "x_variable",
            "title": "X Variable",
            "place_holder": "Variable name",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "position_type",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "y_variable",
            "title": "Y Variable",
            "place_holder": "Variable name",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "position_type",
                "operator": "==",
                "value": "variable",
            },
        },
    ]

    def get_position(self, values, runtime=None):
        position_type = str(values.get("position_type", "value") or "value")
        if position_type == "variable":
            if runtime is None or not hasattr(runtime, "vars"):
                raise RuntimeError("Runtime variables are required for screen_recognition.wait_pixel_color")
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            x = int(runtime.vars.get(x_variable) or 0)
            y = int(runtime.vars.get(y_variable) or 0)
            return x, y

        position = values.get("position") or {}
        if not isinstance(position, dict):
            position = {}
        return int(position.get("x", values.get("x", 0)) or 0), int(position.get("y", values.get("y", 0)) or 0)

    def display_text(self, values=None):
        values = self.normalize_values(values)
        position_type = str(values.get("position_type", "value") or "value")
        if position_type == "variable":
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            position_text = f"{x_variable}, {y_variable}"
        else:
            x, y = self.get_position(values)
            position_text = f"{x}, {y}"
        return f"wait pixel {position_text} for {values.get('color')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        x, y = self.get_position(values, runtime)
        expected = str(values.get("color", "#ffffff") or "#ffffff").strip().lower()
        try:
            import pyautogui
        except Exception:
            raise RuntimeError("pyautogui is required for screen recognition commands. Install it with: pip install pyautogui")

        while True:
            if runtime is not None and getattr(runtime, "stopped", False):
                return None
            pixel = pyautogui.pixel(x, y)
            current = "#{:02x}{:02x}{:02x}".format(pixel[0], pixel[1], pixel[2]).lower()
            if current == expected:
                return None
            time.sleep(0.03)


def register_macro(registry):
    registry.register(WaitPixelColorCommand)
