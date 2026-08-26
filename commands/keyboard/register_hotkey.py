from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


KeyboardCategory = MacroCommandCategory("keyboard", "Keyboard", "m:keyboard")


def parse_bool_value(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    if value is None:
        return False

    text = str(value).strip().lower()
    return text in ["true", "1", "yes", "on", "checked", "enabled"]


class RegisterHotkeyCommand(MacroCommand):
    id = "keyboard.register_hotkey"
    title = "Register Hotkey"
    category = KeyboardCategory
    icon = "mc:ef40"
    description = "Register a global hotkey that runs an action."
    result_policy = ResultPolicy.CONTROL
    fields = [
        {
            "name": "keys",
            "title": "Keys",
            "place_holder": "ctrl+shift+p",
            "value_type": "string",
            "default_value": "ctrl+p",
            "required": True,
        },
        {
            "name": "action_type",
            "title": "Action",
            "value_type": "choice",
            "default_value": "run_macro_group",
            "options": [
                {
                    "value": "run_macro_group",
                    "title": "Run Macro Group",
                },
                {
                    "value": "jump_to_comment",
                    "title": "Jump To Comment",
                },
                {
                    "value": "run_python",
                    "title": "Run Python Code",
                },
            ],
        },
        {
            "name": "target",
            "title": "Macro Group",
            "value_type": "macro_group",
            "default_value": "",
            "placeholder": "Select a macro group to run",
            "visible_if": {
                "field": "action_type",
                "operator": "==",
                "equals": "run_macro_group",
            },
        },
        {
            "name": "run_in_background",
            "title": "Run In Background",
            "value_type": "boolean",
            "default_value": True,
            "required": False,
            "visible_if": {
                "field": "action_type",
                "operator": "==",
                "equals": "run_macro_group",
            },
        },
        {
            "name": "comment",
            "title": "Comment",
            "place_holder": "Select a comment",
            "value_type": "comment",
            "default_value": "",
            "visible_if": {
                "field": "action_type",
                "operator": "==",
                "equals": "jump_to_comment",
            },
        },
        {
            "name": "python_code",
            "title": "Python Code",
            "place_holder": "Code...",
            "value_type": "python_code",
            "default_value": "",
            "line_count": 12,
            "visible_if": {
                "field": "action_type",
                "operator": "==",
                "equals": "run_python",
            },
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "result",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "action_type",
                "operator": "==",
                "equals": "run_python",
            },
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        keys = str(values.get("keys", "") or "").strip()
        action_type = str(
            values.get("action_type", "run_macro_group") or "run_macro_group"
        ).strip()

        if action_type == "jump_to_comment":
            return f"register hotkey {keys} to jump to comment {values.get('comment', '')}"

        if action_type == "run_python":
            return f"register hotkey {keys} to run Python code"

        target = values.get("target", "")

        if isinstance(target, dict):
            target = target.get("title", "") or target.get("value", "")

        background_text = (
            " in background"
            if parse_bool_value(values.get("run_in_background", False))
            else ""
        )

        return f"register hotkey {keys} to run macro group '{target}'{background_text}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        keys = str(values.get("keys", "") or "").strip()
        action_type = str(
            values.get("action_type", "run_macro_group") or "run_macro_group"
        ).strip()

        helper = getattr(runtime, "helper", None)
        parser = getattr(helper, "parse_bool", None)

        if callable(parser):
            run_in_background = parser(values.get("run_in_background", False))
        else:
            run_in_background = parse_bool_value(
                values.get("run_in_background", False)
            )

        if not keys:
            raise ValueError("No hotkey keys specified.")

        target = values.get("target", "")
        comment = str(values.get("comment", "") or "").strip()
        python_code = str(values.get("python_code", "") or "")
        target_variable = str(values.get("target_variable", "") or "").strip()

        if isinstance(target, dict):
            target = target.get("value", "") or target.get("title", "")

        target = str(target or "").strip()

        if action_type == "jump_to_comment":
            if not comment:
                raise ValueError("No comment target specified.")
        elif action_type == "run_macro_group":
            if not target:
                raise ValueError("No macro group target specified.")
        elif action_type == "run_python":
            if not python_code.strip():
                raise ValueError("No Python code specified.")
        else:
            raise ValueError("Invalid hotkey action.")

        hotkey_id = (
            f"{keys}|{action_type}|{target}|{comment}|{python_code}|"
            f"{target_variable}|{run_in_background}"
        )

        return {
            "action": "register_global_hotkey",
            "id": hotkey_id,
            "keys": keys,
            "action_type": action_type,
            "target": target,
            "comment": comment,
            "python_code": python_code,
            "target_variable": target_variable,
            "run_in_background": run_in_background,
        }


def register_macro(registry):
    registry.register(RegisterHotkeyCommand)
