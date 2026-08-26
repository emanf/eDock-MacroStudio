import random

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


MouseCategory = MacroCommandCategory("mouse", "Mouse", "m:mouse")


class MouseClickCommand(MacroCommand):
    id = "mouse.click"
    title = "Mouse Click"
    category = MouseCategory
    icon = "mc:e762"
    description = "Send mouse click."
    os = "linux"
    fields = [
        {
            "name": "click_mode",
            "title": "Click Mode",
            "value_type": "choice",
            "default_value": "current",
            "options": ["current", "position"],
        },
        {
            "name": "position_type",
            "title": "Position Type",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
            "visible_if": {
                "field": "click_mode",
                "operator": "==",
                "value": "position",
            },
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
            "visible_if_all": [
                {
                    "field": "click_mode",
                    "operator": "==",
                    "value": "position",
                },
                {
                    "field": "position_type",
                    "operator": "==",
                    "value": "value",
                },
            ],
        },
        {
            "name": "x_variable",
            "title": "X Variable",
            "place_holder": "Variable name",
            "value_type": "variable",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "click_mode",
                    "operator": "==",
                    "value": "position",
                },
                {
                    "field": "position_type",
                    "operator": "==",
                    "value": "variable",
                },
            ],
        },
        {
            "name": "y_variable",
            "title": "Y Variable",
            "place_holder": "Variable name",
            "value_type": "variable",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "click_mode",
                    "operator": "==",
                    "value": "position",
                },
                {
                    "field": "position_type",
                    "operator": "==",
                    "value": "variable",
                },
            ],
        },
        {
            "name": "random_offset",
            "title": "Random Additional",
            "value_type": "min_max",
            "number_type": "integer",
            "default_value": {
                "min_value": -10,
                "max_value": 10,
            },
            "min_value": -1000,
            "max_value": 1000,
        },
        {
            "name": "button",
            "title": "Button",
            "value_type": "choice",
            "default_value": "left",
            "options": ["left", "right", "middle"],
        },
        {
            "name": "clicks",
            "title": "Clicks",
            "value_type": "integer",
            "default_value": 1,
            "min_value": 1,
            "max_value": 20,
        },
        {
            "name": "no_move",
            "title": "Click without moving cursor",
            "value_type": "boolean",
            "default_value": False,
            "os": "windows",
            "visible_if": {
                "field": "click_mode",
                "operator": "==",
                "value": "position",
            },
        },
    ]

    def get_position(self, values, runtime=None):
        click_mode = str(values.get("click_mode", "current") or "current")
        if click_mode != "position":
            return None, None

        position_type = str(values.get("position_type", "value") or "value")
        if position_type == "variable":
            if runtime is None or not hasattr(runtime, "vars"):
                raise RuntimeError("Runtime variables are required for mouse.click")
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            x = int(runtime.vars.get(x_variable) or 0)
            y = int(runtime.vars.get(y_variable) or 0)
        else:
            position = values.get("position") or {}
            if not isinstance(position, dict):
                position = {}
            x = int(position.get("x", values.get("x", 0)) or 0)
            y = int(position.get("y", values.get("y", 0)) or 0)

        random_offset = values.get("random_offset") or {}
        if not isinstance(random_offset, dict):
            random_offset = {}
        random_offset_min = int(random_offset.get("min", -10) or 0)
        random_offset_max = int(random_offset.get("max", 10) or 0)
        if random_offset_min > random_offset_max:
            random_offset_min, random_offset_max = random_offset_max, random_offset_min

        x += random.randint(random_offset_min, random_offset_max)
        y += random.randint(random_offset_min, random_offset_max)

        return x, y

    def display_text(self, values=None):
        values = self.normalize_values(values)
        click_mode = str(values.get("click_mode", "current") or "current")
        no_move = values.get("no_move", False)
        suffix = " (no move)" if no_move and click_mode == "position" else ""

        if click_mode != "position":
            return f"send {values.get('button')} click on current position"

        position_type = str(values.get("position_type", "value") or "value")
        if position_type == "variable":
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            position_text = f"{x_variable}, {y_variable}"
        else:
            position = values.get("position") or {}
            if not isinstance(position, dict):
                position = {}
            x = int(position.get("x", values.get("x", 0)) or 0)
            y = int(position.get("y", values.get("y", 0)) or 0)
            position_text = f"{x}, {y}"
        return f"send {values.get('button')} click on {position_text}{suffix}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        x, y = self.get_position(values, runtime)
        clicks = int(values.get("clicks", 1) or 1)
        button = str(values.get("button", "left") or "left")
        no_move = values.get("no_move", False)
        interval = random.uniform(0.04, 0.16)

        if runtime is None or not hasattr(runtime, "os_helpers"):
            raise RuntimeError("Runtime with OS helpers is required for mouse.click")

        if x is None or y is None:
            runtime.pyautogui_call("click", clicks=clicks, interval=interval, button=button)
        else:
            runtime.os_helpers.click_at_position(
                x=x,
                y=y,
                button=button,
                clicks=clicks,
                no_move=no_move,
                interval=interval
            )
        return None


def register_macro(registry):
    registry.register(MouseClickCommand)
