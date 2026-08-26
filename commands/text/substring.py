from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


def build_substring_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "substring_text"
    text_source = values.get("text_source")
    text_value = values.get("text_variable") if text_source == "variable" else values.get("text_value")
    start_index = values.get("start_index", 0)
    end_index = values.get("end_index")

    text_value = str(text_value if text_value not in (None, "") else "")
    start_index = 0 if start_index in (None, "") else start_index
    end_text = "end" if end_index in (None, "") else str(end_index)

    return {
        "value": f"{target_variable} = substring({text_value}, {start_index}, {end_text})",
        "status": "info",
    }


class SubstringCommand(MacroCommand):
    id = "text.substring"
    title = "Substring"
    category = TextCategory
    icon = "mc:e94b"
    description = "Extract a portion of text using start and end indexes."
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
            "place_holder": "Hello world",
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
            "name": "start_index",
            "title": "Start Index",
            "place_holder": "0",
            "value_type": "int",
            "default_value": 0,
        },
        {
            "name": "end_index",
            "title": "End Index",
            "place_holder": "Leave empty for end of text",
            "value_type": "int",
            "default_value": "",
            "required": False,
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "substring_text",
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
            "compute_value": build_substring_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        return f"substring text -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        text_source = values.get("text_source")

        if text_source == "variable":
            text_value = runtime.vars.get(values.get("text_variable"))
        else:
            text_value = values.get("text_value")

        text_value = str("" if text_value is None else text_value)

        start_index = values.get("start_index", 0)
        end_index = values.get("end_index")

        try:
            start_index = int(start_index or 0)
        except (TypeError, ValueError):
            raise ValueError("Start Index must be an integer.")

        if end_index in (None, ""):
            result_text = text_value[start_index:]
        else:
            try:
                end_index = int(end_index)
            except (TypeError, ValueError):
                raise ValueError("End Index must be an integer.")

            result_text = text_value[start_index:end_index]

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(result_text, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(SubstringCommand)
