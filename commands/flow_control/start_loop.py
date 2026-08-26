from ...core.model.macro_command import MacroCommand
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


class StartLoopCommand(MacroCommand):
    id = "flow_control.start_loop"
    title = "Loop"
    category = FlowControlCategory
    section = "Loop"
    sort = -100
    icon = "mc:e863"
    description = "Make a loop block."
    fields = [
        {
            "name": "loop_id",
            "title": "Loop ID",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "hidden": True,
        },
        {
            "name": "mode",
            "title": "Loop Mode",
            "value_type": "choice",
            "options": [
                "Repeat Count",
                "For Each Item",
                "While Condition",
            ],
            "default_value": "Repeat Count",
        },
        {
            "name": "repeat_count",
            "title": "Repeat Count",
            "value_type": "int",
            "default_value": 3,
            "min": 0,
            "visible_if": {
                "field": "mode",
                "operator": "==",
                "value": "Repeat Count",
            },
        },
        {
            "name": "list_source",
            "title": "List Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "variable",
            "visible_if": {
                "field": "mode",
                "operator": "==",
                "value": "For Each Item",
            },
        },
        {
            "name": "list_variable",
            "title": "List Variable",
            "place_holder": "items",
            "value_type": "variable",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "For Each Item",
                },
                {
                    "field": "list_source",
                    "operator": "==",
                    "value": "variable",
                },
            ],
        },
        {
            "name": "list_value",
            "title": "List Value",
            "place_holder": "item 1, item 2, item 3",
            "value_type": "string",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "For Each Item",
                },
                {
                    "field": "list_source",
                    "operator": "==",
                    "value": "value",
                },
            ],
        },
        {
            "name": "delimiter",
            "title": "Delimiter",
            "place_holder": ",",
            "value_type": "string",
            "default_value": ",",
            "visible_if": {
                "field": "mode",
                "operator": "==",
                "value": "For Each Item",
            },
        },
        {
            "name": "item_variable",
            "title": "Current Item Variable",
            "place_holder": "current_item",
            "value_type": "variable",
            "default_value": "current_item",
            "visible_if": {
                "field": "mode",
                "operator": "==",
                "value": "For Each Item",
            },
        },
        {
            "name": "index_variable",
            "title": "Current Index Variable",
            "place_holder": "current_index",
            "value_type": "variable",
            "default_value": "current_index",
            "required": False,
            "visible_if_any": [
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "Repeat Count",
                },
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "For Each Item",
                },
            ],
        },
        {
            "name": "zero_based_index",
            "title": "Zero Based Index",
            "value_type": "bool",
            "default_value": False,
            "required": False,
            "visible_if_any": [
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "Repeat Count",
                },
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "For Each Item",
                },
            ],
        },
        {
            "name": "variable_name",
            "title": "Variable Name",
            "place_holder": "my_variable or position.x",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "mode",
                "operator": "==",
                "value": "While Condition",
            },
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
            "visible_if": {
                "field": "mode",
                "operator": "==",
                "value": "While Condition",
            },
        },
        {
            "name": "compare_source",
            "required": False,
            "title": "Compare Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
            "visible_if_all": [
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "While Condition",
                },
                {
                    "field": "operator",
                    "operator": "not in",
                    "value": ["Is True", "Is False", "is true", "is false"],
                },
            ],
        },
        {
            "name": "compare_value",
            "required": False,
            "title": "Compare Value",
            "place_holder": "Value to compare",
            "value_type": "string",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "While Condition",
                },
                {
                    "field": "compare_source",
                    "operator": "==",
                    "value": "value",
                },
            ],
        },
        {
            "name": "compare_variable",
            "required": False,
            "title": "Compare Variable",
            "place_holder": "x or position.x",
            "value_type": "variable",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "mode",
                    "operator": "==",
                    "value": "While Condition",
                },
                {
                    "field": "compare_source",
                    "operator": "==",
                    "value": "variable",
                },
            ],
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        mode = values.get("mode")

        if mode == "For Each Item":
            source = values.get("list_variable") if values.get("list_source") == "variable" else values.get("list_value")
            return f"start loop for each item in {source}"

        if mode == "While Condition":
            variable_name = values.get("variable_name")
            operator = values.get("operator")
            normalized_operator = normalize_operator(operator)

            if normalized_operator in ["is true", "is false"]:
                return f"start loop while {variable_name} {operator}"

            if values.get("compare_source") == "variable":
                return f"start loop while {variable_name} {operator} {values.get('compare_variable')}"

            return f"start loop while {variable_name} {operator} {values.get('compare_value')}"

        return f"start loop repeat {values.get('repeat_count')} times"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        return {
            "action": "start_loop",
            "values": values,
        }


def register_macro(registry):
    registry.register(StartLoopCommand)
