from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


VariablesCategory = MacroCommandCategory("variables", "Variables", "m:code")


OPERATOR_VALUES = {
    "Equals (==)": "==",
    "Not Equals (!=)": "!=",
    "Greater Than (>)": ">",
    "Less Than (<)": "<",
    "Greater Than or Equal (>=)": ">=",
    "Less Than or Equal (<=)": "<=",
    "Contains": "contains",
    "Does Not Contain": "not contains",
    "Starts With": "starts with",
    "Ends With": "ends with",
    "Is True": "is true",
    "Is False": "is false",
}


def normalize_operator(operator):
    return OPERATOR_VALUES.get(operator, operator)


class CheckVariableCommand(MacroCommand):
    id = "variables.check"
    title = "Check Variable"
    category = VariablesCategory
    icon = "mc:f0c5"
    description = "Check a runtime variable value and save the result."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "variable_name",
            "title": "Variable Name",
            "place_holder": "my_variable or position.x",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "operator",
            "title": "Operator",
            "value_type": "choice",
            "options": [
                "Equals (==)",
                "Not Equals (!=)",
                "Greater Than (>)",
                "Less Than (<)",
                "Greater Than or Equal (>=)",
                "Less Than or Equal (<=)",
                "Contains",
                "Does Not Contain",
                "Starts With",
                "Ends With",
                "Is True",
                "Is False",
            ],
            "default_value": "Equals (==)",
        },
        {
            "name": "compare_source",
            "required": False,
            "title": "Compare Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
            "visible_if": {
                "field": "operator",
                "operator": "not in",
                "value": ["Is True", "Is False", "is true", "is false"],
            },
        },
        {
            "name": "compare_value",
            "required": False,
            "title": "Compare Value",
            "place_holder": "Value to compare",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "compare_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "compare_variable",
            "required": False,
            "title": "Compare Variable",
            "place_holder": "x or position.x",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "compare_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "condition_result",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")
        operator = values.get("operator")
        normalized_operator = normalize_operator(operator)
        compare_source = values.get("compare_source")
        compare_value = values.get("compare_value")
        compare_variable = values.get("compare_variable")
        target_variable = values.get("target_variable")

        if normalized_operator in ["is true", "is false"]:
            return f"set {target_variable} = check {variable_name} {operator}"

        if compare_source == "variable":
            return f"set {target_variable} = check {variable_name} {operator} {compare_variable}"

        return f"set {target_variable} = check {variable_name} {operator} {compare_value}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")
        operator = normalize_operator(values.get("operator"))
        compare_source = values.get("compare_source")
        compare_value = values.get("compare_value")
        compare_variable = values.get("compare_variable")
        target_variable = values.get("target_variable")
        compare_type = runtime.vars.type_of(variable_name)

        current_value = runtime.vars.get(variable_name)

        if compare_source == "variable":
            source_compare_value = runtime.vars.get(compare_variable)
        else:
            source_compare_value = compare_value

        final_compare_value = runtime.helper.convert_variable_value(
            source_compare_value,
            compare_type,
        )
        condition = runtime.helper.compare_values(
            current_value,
            operator,
            final_compare_value,
        )

        runtime.vars.add(target_variable)
        target_type = runtime.vars.type_of(target_variable)
        final_condition = runtime.helper.convert_variable_value(
            condition,
            target_type,
        )
        runtime.vars.set(target_variable, final_condition)

        return {
            "condition": condition,
            "variable_name": variable_name,
            "value": current_value,
            "compare_value": final_compare_value,
            "variable_name": target_variable,
            "value": final_condition,
        }


def register_macro(registry):
    registry.register(CheckVariableCommand)
