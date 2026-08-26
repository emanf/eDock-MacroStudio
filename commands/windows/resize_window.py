from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._window_utils import find_window, resize_window


WindowsCategory = MacroCommandCategory("windows", "Window Actions", "m:window")


class ResizeWindowCommand(MacroCommand):
    id = "windows.resize_window"
    title = "Resize Window"
    category = WindowsCategory
    icon = "mc:ec08"
    description = "Resize a window."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "width",
            "title": "Width",
            "value_type": "int",
            "default_value": 800,
            "min_value": 1,
            "max_value": 100000,
        },
        {
            "name": "height",
            "title": "Height",
            "value_type": "int",
            "default_value": 600,
            "min_value": 1,
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
        return f"resize window to {values.get('width', 800)}x{values.get('height', 600)}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        window = find_window(values)

        if not window:
            return {
                "success": False,
                "window": {},
            }

        success = resize_window(window.get("handle", 0), values.get("width", 800), values.get("height", 600))

        return {
            "success": success,
            "window": window,
            "width": values.get("width", 800),
            "height": values.get("height", 600),
        }


def register_macro(registry):
    registry.register(ResizeWindowCommand)
