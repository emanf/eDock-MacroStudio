import time

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._window_utils import find_window


WindowsCategory = MacroCommandCategory("windows", "Window Actions", "m:window")


class WaitForWindowCommand(MacroCommand):
    id = "windows.wait_for_window"
    title = "Wait For Window"
    category = WindowsCategory
    icon = "mc:e06b"
    description = "Wait for a window and save its data to a variable."
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
            "name": "timeout",
            "title": "Timeout",
            "place_holder": "10",
            "value_type": "float",
            "default_value": 10,
            "min_value": 0,
            "max_value": 86400,
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
        timeout = values.get("timeout", 10)
        variable_name = values.get("variable_name", "")

        if variable_name:
            return f"wait for window up to {timeout:g} secs to {variable_name}"

        return f"wait for window up to {timeout:g} secs"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name", "")

        try:
            timeout = float(values.get("timeout", 10) or 0)
        except Exception:
            timeout = 10.0

        timeout = max(0.0, min(86400.0, timeout))
        end = time.time() + timeout
        result = {}

        while True:
            result = find_window(values)

            if result:
                break

            if timeout <= 0 or time.time() >= end:
                result = {}
                break

            if runtime is not None and getattr(runtime, "stopped", False):
                result = {}
                break

            if runtime is not None and hasattr(runtime, "sleep"):
                runtime.sleep(0.2)
            else:
                time.sleep(0.2)

        if variable_name and runtime is not None and hasattr(runtime, "vars"):
            runtime.vars.set(variable_name, result)

        return result


def register_macro(registry):
    registry.register(WaitForWindowCommand)
