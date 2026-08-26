from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._window_utils import find_window, set_window_opacity


WindowsCategory = MacroCommandCategory("windows", "Window Actions", "m:window")


class SetWindowOpacityCommand(MacroCommand):
    id = "windows.set_window_opacity"
    title = "Set Window Opacity"
    category = WindowsCategory
    icon = "mc:e91c"
    description = "Set window opacity from 0 to 1."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "opacity",
            "title": "Opacity",
            "place_holder": "1",
            "value_type": "float",
            "default_value": 1,
            "min_value": 0,
            "max_value": 1,
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
        return f"set window opacity to {values.get('opacity', 1):g}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        window = find_window(values)

        if not window:
            return {
                "success": False,
                "window": {},
            }

        success = set_window_opacity(window.get("handle", 0), values.get("opacity", 1))

        return {
            "success": success,
            "window": window,
            "opacity": values.get("opacity", 1),
        }


def register_macro(registry):
    registry.register(SetWindowOpacityCommand)
