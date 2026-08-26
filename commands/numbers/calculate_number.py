from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


NumbersCategory = MacroCommandCategory("numbers", "Numbers", "mc:e3ce")


def build_calculate_number_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "result_number"
    left_source = values.get("left_source")
    right_source = values.get("right_source")
    left_value = values.get("left_variable") if left_source == "variable" else values.get("left_value")
    right_value = values.get("right_variable") if right_source == "variable" else values.get("right_value")
    operator = values.get("operator") or "Add (+)"

    left_value = str(left_value if left_value not in (None, "") else "0")
    right_value = str(right_value if right_value not in (None, "") else "0")

    return {
        "value": f"{target_variable} = {left_value} {operator} {right_value}",
        "status": "info",
    }


class CalculateNumberCommand(MacroCommand):
    id = "numbers.calculate"
    title = "Calculate Number"
    category = NumbersCategory
    icon = "mc:ea5f"
    description = "Perform calculations using numbers or variables."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "left_source",
            "title": "Left Number Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "variable",
        },
        {
            "name": "left_value",
            "required": False,
            "title": "Left Number",
            "place_holder": "1",
            "value_type": "float",
            "default_value": 0,
            "visible_if": {
                "field": "left_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "left_variable",
            "required": False,
            "title": "Left Number Variable",
            "place_holder": "x",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "left_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "operator",
            "title": "Calculation",
            "value_type": "choice",
            "options": [
                "Add (+)",
                "Subtract (-)",
                "Multiply (×)",
                "Divide (÷)",
                "Remainder (%)",
                "Power (^)",
                "Minimum",
                "Maximum",
            ],
            "default_value": "Add (+)",
        },
        {
            "name": "right_source",
            "title": "Right Number Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
        },
        {
            "name": "right_value",
            "required": False,
            "title": "Right Number",
            "place_holder": "1",
            "value_type": "float",
            "default_value": 1,
            "visible_if": {
                "field": "right_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "right_variable",
            "required": False,
            "title": "Right Number Variable",
            "place_holder": "y",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "right_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "result_number",
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
            "compute_value": build_calculate_number_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        left_source = values.get("left_source")
        right_source = values.get("right_source")
        left_value = values.get("left_variable") if left_source == "variable" else values.get("left_value")
        right_value = values.get("right_variable") if right_source == "variable" else values.get("right_value")
        operator = values.get("operator")
        return f"set {target_variable} = {left_value} {operator} {right_value}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        left_source = values.get("left_source")
        right_source = values.get("right_source")
        operator = values.get("operator")

        if left_source == "variable":
            left_value = runtime.vars.get(values.get("left_variable"))
        else:
            left_value = values.get("left_value")

        if right_source == "variable":
            right_value = runtime.vars.get(values.get("right_variable"))
        else:
            right_value = values.get("right_value")

        left_number = float(left_value or 0)
        right_number = float(right_value or 0)

        if operator == "Add (+)":
            result = left_number + right_number
        elif operator == "Subtract (-)":
            result = left_number - right_number
        elif operator == "Multiply (×)":
            result = left_number * right_number
        elif operator == "Divide (÷)":
            if right_number == 0:
                raise ValueError("Cannot divide by zero")
            result = left_number / right_number
        elif operator == "Remainder (%)":
            if right_number == 0:
                raise ValueError("Cannot calculate a remainder with zero")
            result = left_number % right_number
        elif operator == "Power (^)":
            result = left_number ** right_number
        elif operator == "Minimum":
            result = min(left_number, right_number)
        elif operator == "Maximum":
            result = max(left_number, right_number)
        else:
            result = left_number + right_number

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
    registry.register(CalculateNumberCommand)
