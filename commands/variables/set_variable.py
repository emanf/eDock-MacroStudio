from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


VariablesCategory = MacroCommandCategory("variables", "Variables", "m:code")


class SetVariableCommand(MacroCommand):
    id = "variables.set_variable"
    title = "Set Variable"
    category = VariablesCategory
    icon = "mc:e86f"
    description = "Set a runtime variable."
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
            "name": "value_source",
            "title": "Value Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
        },
        {
            "name": "variable_value",
            "required": False,
            "title": "Value",
            "place_holder": "Variable value",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "value_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "source_variable",
            "required": False,
            "title": "Variable",
            "place_holder": "x or position.x",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "value_source",
                "operator": "==",
                "value": "variable",
            },
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")
        value_source = values.get("value_source")
        variable_value = values.get("variable_value")
        source_variable = values.get("source_variable")

        if value_source == "variable":
            return f"set {variable_name} = {source_variable}"

        return f"set {variable_name} = {variable_value}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")
        value_source = values.get("value_source")
        variable_value = values.get("variable_value")
        source_variable = values.get("source_variable")

        runtime.vars.add(variable_name)
        variable_type = runtime.vars.type_of(variable_name)

        if value_source == "variable":
            source_value = runtime.vars.get(source_variable)
        else:
            source_value = variable_value

        final_value = runtime.helper.convert_variable_value(source_value, variable_type)
        runtime.vars.set(variable_name, final_value)

        return {
            "variable_name": variable_name,
            "value": final_value,
            "source": value_source,
        }


def register_macro(registry):
    registry.register(SetVariableCommand)
