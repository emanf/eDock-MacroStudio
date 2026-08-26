from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


def build_join_text_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "joined_text"
    items_variable = str(values.get("items_variable", "") or "").strip() or "text_parts"
    separator = str(values.get("separator", "") or "")

    return {
        "value": f"{target_variable} = join {items_variable} with {separator}",
        "status": "info",
    }


class JoinTextCommand(MacroCommand):
    id = "text.join"
    title = "Join Text"
    category = TextCategory
    icon = "mc:ef6d"
    description = "Join a list of values into text."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "items_variable",
            "title": "Items Variable",
            "place_holder": "text_parts",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "separator",
            "title": "Separator",
            "place_holder": ", ",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "joined_text",
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
            "compute_value": build_join_text_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        return f"join text -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        items_variable = values.get("items_variable")
        separator = str(values.get("separator", "") or "")
        target_variable = values.get("target_variable")

        items = runtime.vars.get(items_variable)

        if not isinstance(items, (list, tuple)):
            raise ValueError("Items Variable must contain a list.")

        final_text = separator.join(
            "" if item is None else str(item)
            for item in items
        )

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(final_text, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(JoinTextCommand)
