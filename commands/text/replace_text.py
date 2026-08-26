import re

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


def build_replace_text_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "result_text"
    text_source = values.get("text_source")
    text_value = values.get("text_variable") if text_source == "variable" else values.get("text_value")
    find_text = values.get("find_text")
    replace_text = values.get("replace_text")
    use_regex = bool(values.get("use_regex", False))
    case_sensitive = bool(values.get("case_sensitive", True))

    text_value = str(text_value if text_value not in (None, "") else "")
    find_text = str(find_text if find_text not in (None, "") else "")
    replace_text = str(replace_text if replace_text not in (None, "") else "")

    operation = "regex replace" if use_regex else "replace"
    case_mode = "case-sensitive" if case_sensitive else "case-insensitive"

    return {
        "value": (
            f"{target_variable} = {operation} {find_text} with "
            f"{replace_text} in {text_value} ({case_mode})"
        ),
        "status": "info",
    }


class ReplaceTextCommand(MacroCommand):
    id = "text.replace"
    title = "Replace Text"
    category = TextCategory
    icon = "mc:f232"
    description = "Replace matching text inside a string."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "text_source",
            "title": "Text Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "variable",
        },
        {
            "name": "text_value",
            "required": False,
            "title": "Text",
            "place_holder": "hello world",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "text_variable",
            "required": False,
            "title": "Text Variable",
            "place_holder": "text_value",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "find_text",
            "title": "Find",
            "place_holder": "world",
            "value_type": "string",
            "default_value": "",
        },
        {
            "name": "replace_text",
            "title": "Replace With",
            "place_holder": "Macro Studio",
            "value_type": "string",
            "default_value": "",
        },
        {
            "name": "use_regex",
            "title": "Use Regex",
            "value_type": "bool",
            "default_value": False,
        },
        {
            "name": "case_sensitive",
            "title": "Case Sensitive",
            "value_type": "bool",
            "default_value": True,
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "result_text",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "result_preview",
            "title": "Result",
            "value_type": "result",
            "status": "info",
            "default_value": "",
            "required": False,
            "transient": True,
            "compute_value": build_replace_text_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        return f"replace text -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        text_source = values.get("text_source")
        find_text = str(values.get("find_text", "") or "")
        replace_text = str(values.get("replace_text", "") or "")
        use_regex = bool(values.get("use_regex", False))
        case_sensitive = bool(values.get("case_sensitive", True))

        if text_source == "variable":
            text_value = runtime.vars.get(values.get("text_variable"))
        else:
            text_value = values.get("text_value")

        source_text = str("" if text_value is None else text_value)

        try:
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                final_text = re.sub(find_text, replace_text, source_text, flags=flags)
            elif case_sensitive:
                final_text = source_text.replace(find_text, replace_text)
            else:
                final_text = re.sub(
                    re.escape(find_text),
                    lambda match: replace_text,
                    source_text,
                    flags=re.IGNORECASE,
                )
        except re.error as error:
            raise ValueError(f"Invalid regular expression: {error}") from error

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(final_text, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(ReplaceTextCommand)
