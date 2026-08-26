from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._window_utils import find_window, set_window_state


WindowsCategory = MacroCommandCategory("windows", "Window Actions", "m:window")


class SetWindowStateCommand(MacroCommand):
    id = "windows.set_window_state"
    title = "Set Window State"
    category = WindowsCategory
    icon = "mc:eb97"
    description = "Set a window state."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "state",
            "title": "State",
            "value_type": "choice",
            "default_value": "activate",
            "options": [
                {"value": "activate", "title": "Activate"},
                {"value": "minimize", "title": "Minimize"},
                {"value": "maximize", "title": "Maximize"},
                {"value": "restore", "title": "Restore"},
                {"value": "fullscreen", "title": "Fullscreen"},
                {"value": "restore_fullscreen", "title": "Restore Fullscreen"},
                {"value": "always_on_top", "title": "Always on Top"},
                {"value": "not_always_on_top", "title": "Not Always on Top"},
            ],
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
        state = str(values.get("state", "restore") or "restore").strip().lower()
        return f"set window state: {state}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        state = str(values.get("state", "restore") or "restore").strip().lower()
        window = find_window(values)

        if not window:
            return {
                "success": False,
                "window": {},
                "state": state,
            }

        success = set_window_state(window.get("handle", 0), state)

        return {
            "success": success,
            "window": window,
            "state": state,
        }


def register_macro(registry):
    registry.register(SetWindowStateCommand)
