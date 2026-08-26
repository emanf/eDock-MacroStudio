from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


def build_text_length_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "text_length"
    text_source = values.get("text_source")
    text_value = values.get("text_variable") if text_source == "variable" else values.get("text_value")
    text_value = str(text_value if text_value not in (None, "") else "")

    return {
        "value": f"{target_variable} = length({text_value})",
        "status": "info",
    }


class TextLengthCommand(MacroCommand):
    id = "text.length"
    title = "Text Length"
    category = TextCategory
    icon = "mc:eb8d"
    description = "Get text length."
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
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "text_length",
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
            "compute_value": build_text_length_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        return f"text length -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        text_source = values.get("text_source")

        if text_source == "variable":
            text_value = runtime.vars.get(values.get("text_variable"))
        else:
            text_value = values.get("text_value")

        result_length = len(str("" if text_value is None else text_value))

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(result_length, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(TextLengthCommand)
