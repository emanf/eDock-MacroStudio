from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


def format_preview_operand(source, value):
    if source == "variable":
        variable_name = str(value or "").strip() or "{Variable}"
        return f'Text from "{variable_name}"'

    return repr("" if value in (None, "") else str(value))


def build_append_text_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "{Variable}"
    base_source = values.get("base_source")
    append_source = values.get("append_source")
    separator = values.get("separator")

    base_value = values.get("base_variable") if base_source == "variable" else values.get("base_text")
    append_value = values.get("append_variable") if append_source == "variable" else values.get("append_text")

    base_value = "" if base_value in (None, "") else str(base_value)
    append_value = "" if append_value in (None, "") else str(append_value)
    separator = "" if separator in (None, "") else str(separator)

    base_expression = format_preview_operand(base_source, base_value)
    append_expression = format_preview_operand(append_source, append_value)

    expressions = [base_expression]

    if separator:
        expressions.append(repr(separator))

    expressions.append(append_expression)

    value = " + ".join(expressions)

    if base_source != "variable" and append_source != "variable":
        final_text = f"{base_value}{separator}{append_value}"
        value = f"{value} → {final_text!r}"

    return {
        "value": value,
        "status": "info",
    }


class AppendTextCommand(MacroCommand):
    id = "text.append"
    title = "Append Text"
    category = TextCategory
    icon = "mc:eae2"
    description = "Append text to another text value with an optional separator."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "base_source",
            "title": "Base Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "variable",
        },
        {
            "name": "base_text",
            "required": False,
            "title": "Base Text",
            "place_holder": "Hello",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "base_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "base_variable",
            "required": False,
            "title": "Base Variable",
            "place_holder": "text_a",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "base_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "separator",
            "required": False,
            "title": "Separator",
            "place_holder": "space, comma, dash, etc.",
            "value_type": "string",
            "default_value": "",
        },
        {
            "name": "append_source",
            "title": "Append Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
        },
        {
            "name": "append_text",
            "required": False,
            "title": "Append Text",
            "place_holder": "World",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "append_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "append_variable",
            "required": False,
            "title": "Append Variable",
            "place_holder": "text_b",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "append_source",
                "operator": "==",
                "value": "variable",
            },
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
            "title": "Text Preview",
            "value_type": "result",
            "status": "info",
            "default_value": "",
            "required": False,
            "transient": True,
            "compute_value": build_append_text_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        base_source = values.get("base_source")
        append_source = values.get("append_source")
        separator = values.get("separator")
        base_value = values.get("base_variable") if base_source == "variable" else values.get("base_text")
        append_value = values.get("append_variable") if append_source == "variable" else values.get("append_text")

        if separator:
            return f"set {target_variable} = {base_value} + {separator} + {append_value}"

        return f"set {target_variable} = {base_value} + {append_value}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        base_source = values.get("base_source")
        append_source = values.get("append_source")
        separator = str(values.get("separator", "") or "")

        if base_source == "variable":
            base_value = runtime.vars.get(values.get("base_variable"))
        else:
            base_value = values.get("base_text")

        if append_source == "variable":
            append_value = runtime.vars.get(values.get("append_variable"))
        else:
            append_value = values.get("append_text")

        base_text = "" if base_value is None else str(base_value)
        append_text = "" if append_value is None else str(append_value)
        final_text = f"{base_text}{separator}{append_text}"

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(final_text, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(AppendTextCommand)
