import secrets
import string

from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


VariablesCategory = MacroCommandCategory("variables", "Variables", "m:code")


class RandomStringCommand(MacroCommand):
    id = "variables.random_string"
    title = "Random String"
    category = VariablesCategory
    icon = "mc:e043"
    description = "Generate a random string and save it into a variable."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "length",
            "title": "Length",
            "place_holder": "16",
            "value_type": "int",
            "default_value": 16,
            "min_value": 1,
            "max_value": 4096,
        },
        {
            "name": "character_set",
            "title": "Character Set",
            "place_holder": "Letters and Numbers",
            "value_type": "choice",
            "default_value": "letters_numbers",
            "options": [
                {"title": "Letters and Numbers", "value": "letters_numbers"},
                {"title": "Letters", "value": "letters"},
                {"title": "Numbers", "value": "numbers"},
                {"title": "Lowercase Letters", "value": "lowercase"},
                {"title": "Uppercase Letters", "value": "uppercase"},
                {"title": "Letters, Numbers and Symbols", "value": "letters_numbers_symbols"},
            ],
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
        length = values.get("length")
        character_set = values.get("character_set")
        variable = values.get("variable")
        return f"random string length {length} ({character_set}) -> {variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable = str(values.get("variable", "") or "").strip()
        length = int(values.get("length", 16) or 16)
        character_set = str(values.get("character_set", "letters_numbers") or "letters_numbers")
        length = max(1, min(4096, length))

        if character_set == "letters":
            alphabet = string.ascii_letters
        elif character_set == "numbers":
            alphabet = string.digits
        elif character_set == "lowercase":
            alphabet = string.ascii_lowercase
        elif character_set == "uppercase":
            alphabet = string.ascii_uppercase
        elif character_set == "letters_numbers_symbols":
            alphabet = string.ascii_letters + string.digits + string.punctuation
        else:
            alphabet = string.ascii_letters + string.digits

        result = "".join(secrets.choice(alphabet) for _ in range(length))
        if runtime is not None and variable:
            runtime.vars.add(variable)
            runtime.vars.set(variable, result)
        return result


def register_macro(registry):
    registry.register(RandomStringCommand)
