from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


FlowControlCategory = MacroCommandCategory("flow_control", "Flow Control", "mc:eb92")


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


class IfVariableRunMacroGroupCommand(MacroCommand):
    id = "flow_control.if_variable_run_macro_group"
    title = "If Variable Run Macro Group"
    category = FlowControlCategory
    section = "If"
    icon = "mc:eae7"
    description = "Run a macro group if a variable condition matches."
    result_policy = ResultPolicy.CONTROL
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
            "name": "target",
            "title": "Macro Group",
            "value_type": "macro_group",
            "default_value": "",
            "placeholder": "Select a macro group to run",
            "required": True,
        },
        {
            "name": "run_in_background",
            "title": "Run In Background",
            "value_type": "boolean",
            "default_value": True,
            "required": False,
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
        target = values.get("target", "")
        run_in_background = values.get("run_in_background", False)

        if isinstance(target, dict):
            target_title = target.get("title", "")
            target_value = target.get("value", "")
            target_text = target_title or target_value
        else:
            target_text = target

        background_text = " in background" if run_in_background else ""

        if normalized_operator in ["is true", "is false"]:
            return f"if {variable_name} {operator}, run macro group '{target_text}'{background_text}"

        if compare_source == "variable":
            return f"if {variable_name} {operator} {compare_variable}, run macro group '{target_text}'{background_text}"

        return f"if {variable_name} {operator} {compare_value}, run macro group '{target_text}'{background_text}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")
        operator = normalize_operator(values.get("operator"))
        compare_source = values.get("compare_source")
        compare_value = values.get("compare_value")
        compare_variable = values.get("compare_variable")
        target = values.get("target", "")
        run_in_background = runtime.helper.parse_bool(
            values.get("run_in_background", False)
        )

        if isinstance(target, dict):
            target = target.get("value", "")

        if not target:
            raise ValueError("No macro group target specified.")

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

        if condition:
            return {
                "action": "run_macro_group",
                "target": target,
                "run_in_background": run_in_background,
                "condition": True,
                "variable_name": variable_name,
                "value": current_value,
                "compare_value": final_compare_value,
            }

        return {
            "condition": False,
            "variable_name": variable_name,
            "value": current_value,
            "compare_value": final_compare_value,
        }


def register_macro(registry):
    registry.register(IfVariableRunMacroGroupCommand)
