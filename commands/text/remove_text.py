from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


def build_remove_text_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "result_text"
    text_source = values.get("text_source")
    text_value = values.get("text_variable") if text_source == "variable" else values.get("text_value")
    remove_text = values.get("remove_text")

    text_value = str(text_value if text_value not in (None, "") else "")
    remove_text = str(remove_text if remove_text not in (None, "") else "")

    return {
        "value": f"{target_variable} = remove {remove_text} from {text_value}",
        "status": "info",
    }


class RemoveTextCommand(MacroCommand):
    id = "text.remove"
    title = "Remove Text"
    category = TextCategory
    icon = "mc:eb80"
    description = "Remove matching text from a string."
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
            "name": "remove_text",
            "title": "Remove",
            "place_holder": "world",
            "value_type": "string",
            "default_value": "",
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
            "compute_value": build_remove_text_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        return f"remove text -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        text_source = values.get("text_source")
        remove_text = str(values.get("remove_text", "") or "")

        if text_source == "variable":
            text_value = runtime.vars.get(values.get("text_variable"))
        else:
            text_value = values.get("text_value")

        final_text = str("" if text_value is None else text_value).replace(remove_text, "")

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(final_text, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(RemoveTextCommand)
