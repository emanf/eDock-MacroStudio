from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._window_utils import close_window, find_window


WindowsCategory = MacroCommandCategory("windows", "Windows", "m:window")


class CloseWindowCommand(MacroCommand):
    id = "windows.close_window"
    title = "Close Window"
    category = WindowsCategory
    icon = "mc:e0e9"
    description = "Close a window by title, process, class, or handle."
    result_policy = ResultPolicy.DATA
    fields = [
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
                {
                    "value": "contains",
                    "title": "Contains",
                },
                {
                    "value": "exact",
                    "title": "Exact",
                },
                {
                    "value": "regex",
                    "title": "Regex",
                },
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
        return "close window"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        window = find_window(values)

        if not window:
            return {
                "success": False,
                "window": {},
            }

        success = close_window(window.get("handle", 0))

        return {
            "success": success,
            "window": window,
        }


def register_macro(registry):
    registry.register(CloseWindowCommand)
