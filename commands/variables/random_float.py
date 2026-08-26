import random

from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


VariablesCategory = MacroCommandCategory("variables", "Variables", "m:code")


class RandomFloatCommand(MacroCommand):
    id = "variables.random_float"
    title = "Random Float"
    category = VariablesCategory
    icon = "mc:e043"
    description = "Generate a random float and save it into a variable."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "min_value",
            "title": "Min Value",
            "place_holder": "0",
            "value_type": "float",
            "default_value": 0,
        },
        {
            "name": "max_value",
            "title": "Max Value",
            "place_holder": "1",
            "value_type": "float",
            "default_value": 1,
        },
        {
            "name": "variable",
            "title": "Save to Variable",
            "place_holder": "Variable name",
            "value_type": "variable",
            "default_value": "",
            "required": True,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        variable = values.get("variable")
        min_value = values.get("min_value")
        max_value = values.get("max_value")
        return f"random float {min_value} to {max_value} -> {variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable = str(values.get("variable", "") or "").strip()
        min_value = float(values.get("min_value", 0) or 0)
        max_value = float(values.get("max_value", 1) or 1)
        if min_value > max_value:
            min_value, max_value = max_value, min_value
        result = random.uniform(min_value, max_value)
        if runtime is not None and variable:
            runtime.vars.add(variable)
            runtime.vars.set(variable, result)
        return result


def register_macro(registry):
    registry.register(RandomFloatCommand)
