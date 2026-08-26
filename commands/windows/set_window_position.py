from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._window_utils import find_window, set_window_position


WindowsCategory = MacroCommandCategory("windows", "Window Actions", "m:window")


class SetWindowPositionCommand(MacroCommand):
    id = "windows.set_window_position"
    title = "Set Window Position"
    category = WindowsCategory
    icon = "mc:e8aa"
    description = "Move a window to a screen position."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "x",
            "title": "X",
            "value_type": "int",
            "default_value": 0,
            "min_value": -100000,
            "max_value": 100000,
        },
        {
            "name": "y",
            "title": "Y",
            "value_type": "int",
            "default_value": 0,
            "min_value": -100000,
            "max_value": 100000,
        },
        {
            "name": "title",
            "title": "Window Title",
            "place_holder": "Untitled - Notepad",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "process_name",
            "title": "Process",
            "place_holder": "notepad.exe",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "class_name",
            "title": "Class Name",
            "place_holder": "Notepad",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "handle",
            "title": "Handle",
            "place_holder": "0x00000000",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "match_mode",
            "title": "Match Mode",
            "value_type": "choice",
            "default_value": "contains",
            "options": [
                {"value": "contains", "title": "Contains"},
                {"value": "exact", "title": "Exact"},
                {"value": "regex", "title": "Regex"},
            ],
        },
        {
            "name": "visible_only",
            "title": "Visible Only",
            "value_type": "bool",
            "default_value": True,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"set window position to {values.get('x', 0)}, {values.get('y', 0)}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        window = find_window(values)

        if not window:
            return {
                "success": False,
                "window": {},
            }

        success = set_window_position(window.get("handle", 0), values.get("x", 0), values.get("y", 0))

        return {
            "success": success,
            "window": window,
            "x": values.get("x", 0),
            "y": values.get("y", 0),
        }


def register_macro(registry):
    registry.register(SetWindowPositionCommand)
