import math

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


NumbersCategory = MacroCommandCategory("numbers", "Numbers", "mc:e3ce")


def build_round_number_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "rounded_number"
    number_source = values.get("number_source")
    number_value = values.get("number_variable") if number_source == "variable" else values.get("number_value")
    operation = values.get("operation") or "round"
    digits = values.get("digits", 0)

    number_value = str(number_value if number_value not in (None, "") else "0")

    if operation == "round":
        expression = f"round({number_value}, {digits})"
    else:
        expression = f"{operation}({number_value})"

    return {
        "value": f"{target_variable} = {expression}",
        "status": "info",
    }


class RoundNumberCommand(MacroCommand):
    id = "numbers.round"
    title = "Round Number"
    category = NumbersCategory
    icon = "mc:eaf6"
    description = "Round, floor, or ceiling a number."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "number_source",
            "title": "Number Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "variable",
        },
        {
            "name": "number_value",
            "required": False,
            "title": "Number",
            "place_holder": "12.5",
            "value_type": "float",
            "default_value": 0,
            "visible_if": {
                "field": "number_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "number_variable",
            "required": False,
            "title": "Number Variable",
            "place_holder": "x",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "number_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "operation",
            "title": "Operation",
            "value_type": "choice",
            "options": ["round", "floor", "ceiling"],
            "default_value": "round",
        },
        {
            "name": "digits",
            "title": "Digits",
            "place_holder": "0",
            "value_type": "int",
            "default_value": 0,
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "rounded_number",
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
            "compute_value": build_round_number_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        operation = values.get("operation")
        return f"{operation} number -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        number_source = values.get("number_source")
        operation = values.get("operation")
        digits = int(values.get("digits", 0) or 0)

        if number_source == "variable":
            number_value = runtime.vars.get(values.get("number_variable"))
        else:
            number_value = values.get("number_value")

        number_value = float(number_value or 0)

        if operation == "floor":
            result = math.floor(number_value)
        elif operation == "ceiling":
            result = math.ceil(number_value)
        else:
            result = round(number_value, digits)

        if isinstance(result, float) and result.is_integer():
            result = int(result)

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(result, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(RoundNumberCommand)
