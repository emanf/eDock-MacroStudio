from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


NumbersCategory = MacroCommandCategory("numbers", "Numbers", "mc:e3ce")


def build_change_number_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "counter"
    operation = values.get("operation") or "increase"
    amount_source = values.get("amount_source")
    amount_value = values.get("amount_variable") if amount_source == "variable" else values.get("amount_value")
    amount_value = str(amount_value if amount_value not in (None, "") else "1")

    symbols = {
        "increase": "+",
        "decrease": "-",
        "multiply": "*",
        "divide": "/",
    }

    symbol = symbols.get(operation, "+")
    return {
        "value": f"{target_variable} = {target_variable} {symbol} {amount_value}",
        "status": "info",
    }


class ChangeNumberCommand(MacroCommand):
    id = "numbers.change"
    title = "Change Number"
    category = NumbersCategory
    icon = "mc:e3cd"
    description = "Change an existing number variable."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "operation",
            "title": "Operation",
            "value_type": "choice",
            "options": ["increase", "decrease", "multiply", "divide"],
            "default_value": "increase",
        },
        {
            "name": "amount_source",
            "title": "Amount Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
        },
        {
            "name": "amount_value",
            "required": False,
            "title": "Amount",
            "place_holder": "1",
            "value_type": "float",
            "default_value": 1,
            "visible_if": {
                "field": "amount_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "amount_variable",
            "required": False,
            "title": "Amount Variable",
            "place_holder": "step",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "amount_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "counter",
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
            "compute_value": build_change_number_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        operation = values.get("operation")
        amount_source = values.get("amount_source")
        amount_value = values.get("amount_variable") if amount_source == "variable" else values.get("amount_value")
        return f"{operation} {target_variable} by {amount_value}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        operation = values.get("operation")
        amount_source = values.get("amount_source")

        current_value = runtime.vars.get(target_variable)
        current_number = float(current_value or 0)

        if amount_source == "variable":
            amount_value = runtime.vars.get(values.get("amount_variable"))
        else:
            amount_value = values.get("amount_value")

        amount_number = float(amount_value or 0)

        if operation == "decrease":
            result = current_number - amount_number
        elif operation == "multiply":
            result = current_number * amount_number
        elif operation == "divide":
            if amount_number == 0:
                raise ValueError("Cannot divide by zero")
            result = current_number / amount_number
        else:
            result = current_number + amount_number

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
    registry.register(ChangeNumberCommand)
