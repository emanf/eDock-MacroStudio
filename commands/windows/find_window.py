from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._window_utils import find_window


WindowsCategory = MacroCommandCategory("windows", "Window Actions", "m:window")


class FindWindowCommand(MacroCommand):
    id = "windows.find_window"
    title = "Find Window"
    category = WindowsCategory
    icon = "mc:ef70"
    description = "Find a window by title, process, class, or handle."
    result_policy = ResultPolicy.VARIABLE
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
        {
            "name": "variable_name",
            "title": "Save To Variable",
            "place_holder": "window_data",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name", "")

        if variable_name:
            return f"find window to {variable_name}"

        return "find window"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name", "")
        result = find_window(values)

        if variable_name and runtime is not None and hasattr(runtime, "vars"):
            runtime.vars.set(variable_name, result)

        return result


def register_macro(registry):
    registry.register(FindWindowCommand)
