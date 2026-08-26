from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


TimingCategory = MacroCommandCategory("timing", "Timing", "m:timer")


def parse_bool_value(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    if value is None:
        return False

    text = str(value).strip().lower()
    return text in ["true", "1", "yes", "on", "checked", "enabled"]


class RegisterTimerCommand(MacroCommand):
    id = "timing.register_timer"
    title = "Register Timer"
    category = TimingCategory
    icon = "m:timer"
    description = "Register a repeating or one-shot timer action."
    result_policy = ResultPolicy.CONTROL
    fields = [
        {
            "name": "timer_mode",
            "title": "Timer Mode",
            "value_type": "choice",
            "default_value": "repeating",
            "options": [
                {
                    "value": "repeating",
                    "title": "Repeating",
                },
                {
                    "value": "one_shot",
                    "title": "One-Shot",
                },
            ],
        },
        {
            "name": "timer_source",
            "title": "Timer Source",
            "value_type": "choice",
            "default_value": "value",
            "options": [
                {
                    "value": "value",
                    "title": "Value",
                },
                {
                    "value": "variable",
                    "title": "Variable",
                },
            ],
        },
        {
            "name": "seconds",
            "title": "Seconds",
            "place_holder": "1",
            "value_type": "float",
            "default_value": 1,
            "min_value": 0.01,
            "max_value": 86400,
            "visible_if": {
                "field": "timer_source",
                "operator": "==",
                "equals": "value",
            },
        },
        {
            "name": "seconds_variable",
            "title": "Seconds Variable",
            "place_holder": "timer_seconds",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "timer_source",
                "operator": "==",
                "equals": "variable",
            },
        },
        {
            "name": "run_immediately",
            "title": "Run Immediately",
            "value_type": "boolean",
            "default_value": False,
            "required": False,
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
            "place_holder": "you need to add a comment first",
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
        timer_mode = str(
            values.get("timer_mode", "repeating") or "repeating"
        ).strip()
        timer_source = str(
            values.get("timer_source", "value") or "value"
        ).strip()
        run_immediately = parse_bool_value(
            values.get("run_immediately", False)
        )

        if timer_source == "variable":
            seconds_text = str(
                values.get("seconds_variable", "") or ""
            ).strip()
        else:
            try:
                seconds_text = f"{float(values.get('seconds', 1) or 0):g}"
            except Exception:
                seconds_text = "1"

        action_type = str(
            values.get("action_type", "run_macro_group") or "run_macro_group"
        ).strip()

        if action_type == "jump_to_comment":
            action_text = f"jump to comment '{values.get('comment', '')}'"
        elif action_type == "run_python":
            action_text = "run Python code"
        else:
            target = values.get("target", "")

            if isinstance(target, dict):
                target = target.get("title", "") or target.get("value", "")

            background_text = (
                " in background"
                if parse_bool_value(values.get("run_in_background", False))
                else ""
            )
            action_text = f"run macro group '{target}'{background_text}"

        immediate_text = " immediately" if run_immediately else ""

        return (
            f"register {timer_mode} timer every {seconds_text} secs"
            f"{immediate_text} to {action_text}"
        )

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)

        timer_mode = str(
            values.get("timer_mode", "repeating") or "repeating"
        ).strip()

        if timer_mode not in {"repeating", "one_shot"}:
            timer_mode = "repeating"

        timer_source = str(
            values.get("timer_source", "value") or "value"
        ).strip()
        seconds_variable = ""

        if timer_source == "variable":
            seconds_variable = str(
                values.get("seconds_variable", "") or ""
            ).strip()

            if not seconds_variable:
                raise ValueError("No timer seconds variable specified.")

            if runtime is None or not hasattr(runtime, "vars"):
                raise RuntimeError("Runtime variables are not available.")

            seconds_value = runtime.vars.get(seconds_variable)
        else:
            seconds_value = values.get("seconds", 1)

        try:
            seconds = float(seconds_value)
        except Exception:
            raise ValueError("Timer seconds must be a valid number.")

        if seconds <= 0:
            raise ValueError("Timer seconds must be greater than zero.")

        seconds = min(86400.0, seconds)

        helper = getattr(runtime, "helper", None)
        parser = getattr(helper, "parse_bool", None)

        if callable(parser):
            run_immediately = parser(values.get("run_immediately", False))
            run_in_background = parser(values.get("run_in_background", False))
        else:
            run_immediately = parse_bool_value(
                values.get("run_immediately", False)
            )
            run_in_background = parse_bool_value(
                values.get("run_in_background", False)
            )

        action_type = str(
            values.get("action_type", "run_macro_group") or "run_macro_group"
        ).strip()
        target = values.get("target", "")
        comment = str(values.get("comment", "") or "").strip()
        python_code = str(values.get("python_code", "") or "")
        target_variable = str(
            values.get("target_variable", "") or ""
        ).strip()

        if isinstance(target, dict):
            target = target.get("value", "") or target.get("title", "")

        target = str(target or "").strip()

        if action_type == "run_macro_group":
            if not target:
                raise ValueError("No macro group target specified.")
        elif action_type == "jump_to_comment":
            if not comment:
                raise ValueError("No comment target specified.")
        elif action_type == "run_python":
            if not python_code.strip():
                raise ValueError("No Python code specified.")
        else:
            raise ValueError("Invalid timer action.")

        timer_id = (
            f"{timer_mode}|{timer_source}|{seconds}|{seconds_variable}|"
            f"{run_immediately}|{action_type}|{target}|{comment}|"
            f"{python_code}|{target_variable}|{run_in_background}"
        )

        return {
            "action": "register_global_timer",
            "id": timer_id,
            "timer_mode": timer_mode,
            "seconds": seconds,
            "run_immediately": run_immediately,
            "action_type": action_type,
            "target": target,
            "comment": comment,
            "python_code": python_code,
            "target_variable": target_variable,
            "run_in_background": run_in_background,
        }


def register_macro(registry):
    registry.register(RegisterTimerCommand)
