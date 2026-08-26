from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


def build_split_text_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "text_parts"
    text_source = values.get("text_source")
    text_value = values.get("text_variable") if text_source == "variable" else values.get("text_value")
    separator = str(values.get("separator", "") or "")

    text_value = str(text_value if text_value not in (None, "") else "")
    separator_text = "whitespace" if separator == "" else separator

    return {
        "value": f"{target_variable} = split {text_value} by {separator_text}",
        "status": "info",
    }


class SplitTextCommand(MacroCommand):
    id = "text.split"
    title = "Split Text"
    category = TextCategory
    icon = "mc:e0b6"
    description = "Split text into a list of values."
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
            "place_holder": "apple,banana,orange",
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
            "name": "separator",
            "title": "Separator",
            "place_holder": "Leave empty for whitespace",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "remove_empty",
            "title": "Remove Empty Items",
            "value_type": "bool",
            "default_value": False,
        },
        {
            "name": "trim_items",
            "title": "Trim Items",
            "value_type": "bool",
            "default_value": False,
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "text_parts",
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
            "compute_value": build_split_text_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        return f"split text -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        text_source = values.get("text_source")
        separator = str(values.get("separator", "") or "")
        remove_empty = bool(values.get("remove_empty", False))
        trim_items = bool(values.get("trim_items", False))

        if text_source == "variable":
            text_value = runtime.vars.get(values.get("text_variable"))
        else:
            text_value = values.get("text_value")

        source_text = str("" if text_value is None else text_value)
        result_items = source_text.split(separator if separator else None)

        if trim_items:
            result_items = [item.strip() for item in result_items]

        if remove_empty:
            result_items = [item for item in result_items if item != ""]

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(result_items, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(SplitTextCommand)
