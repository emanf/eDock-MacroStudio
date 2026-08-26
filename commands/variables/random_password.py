import secrets
import string

from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


VariablesCategory = MacroCommandCategory("variables", "Variables", "m:code")


class RandomPasswordCommand(MacroCommand):
    id = "variables.random_password"
    title = "Random Password"
    category = VariablesCategory
    icon = "mc:e043"
    description = "Generate a secure random password and save it into a variable."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "length",
            "title": "Length",
            "place_holder": "24",
            "value_type": "int",
            "default_value": 24,
            "min_value": 8,
            "max_value": 4096,
        },
        {
            "name": "include_uppercase",
            "title": "Include Uppercase",
            "value_type": "bool",
            "default_value": True,
        },
        {
            "name": "include_lowercase",
            "title": "Include Lowercase",
            "value_type": "bool",
            "default_value": True,
        },
        {
            "name": "include_numbers",
            "title": "Include Numbers",
            "value_type": "bool",
            "default_value": True,
        },
        {
            "name": "include_symbols",
            "title": "Include Symbols",
            "value_type": "bool",
            "default_value": True,
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
        variable = values.get("variable")
        return f"random password length {length} -> {variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        variable = str(values.get("variable", "") or "").strip()
        length = int(values.get("length", 24) or 24)
        include_uppercase = bool(values.get("include_uppercase", True))
        include_lowercase = bool(values.get("include_lowercase", True))
        include_numbers = bool(values.get("include_numbers", True))
        include_symbols = bool(values.get("include_symbols", True))
        length = max(8, min(4096, length))

        groups = []
        if include_uppercase:
            groups.append(string.ascii_uppercase)
        if include_lowercase:
            groups.append(string.ascii_lowercase)
        if include_numbers:
            groups.append(string.digits)
        if include_symbols:
            groups.append("!@#$%^&*()-_=+[]{};:,.<>?/")

        if not groups:
            groups = [string.ascii_uppercase, string.ascii_lowercase, string.digits, "!@#$%^&*()-_=+[]{};:,.<>?/"]

        alphabet = "".join(groups)
        required_chars = [secrets.choice(group) for group in groups]
        remaining_length = max(0, length - len(required_chars))
        password_chars = required_chars + [secrets.choice(alphabet) for _ in range(remaining_length)]

        for index in range(len(password_chars) - 1, 0, -1):
            swap_index = secrets.randbelow(index + 1)
            password_chars[index], password_chars[swap_index] = password_chars[swap_index], password_chars[index]

        result = "".join(password_chars)
        if runtime is not None and variable:
            runtime.vars.add(variable)
            runtime.vars.set(variable, result)
        return result


def register_macro(registry):
    registry.register(RandomPasswordCommand)
