class RuntimeVariables:
    def __init__(self, runtime):
        self.runtime = runtime

    def root_name(self, variable_path):
        return self.runtime.helper.variable_root_name(variable_path)

    def definition(self, variable_name):
        variable_name = self.root_name(variable_name)
        if not variable_name:
            return None

        for variable in self.runtime.initial_variables:
            if not isinstance(variable, dict):
                continue

            name = str(variable.get("name", "") or "").strip()
            if name == variable_name:
                return variable

        return None

    def type_of(self, variable_name):
        variable = self.definition(variable_name)
        if not variable:
            return "auto"

        return str(variable.get("type", "auto") or "auto").strip() or "auto"

    def add(self, variable_path, value="", value_type="auto"):
        variable_name = self.root_name(variable_path)
        if not variable_name:
            return False

        for variable in self.runtime.initial_variables:
            if not isinstance(variable, dict):
                continue

            name = str(variable.get("name", "") or "").strip()
            if name == variable_name:
                if variable_name not in self.runtime.variables:
                    variable_type = str(variable.get("type", "auto") or "auto").strip() or "auto"
                    variable_value = variable.get("value", "")
                    self.runtime.variables[variable_name] = self.runtime.helper.convert_variable_value(variable_value, variable_type)
                return False

        self.runtime.initial_variables.append({
            "name": variable_name,
            "type": value_type or "auto",
            "value": value,
        })

        if variable_name not in self.runtime.variables:
            self.runtime.variables[variable_name] = self.runtime.helper.convert_variable_value(value, value_type or "auto")

        return True

    def ensure(self, variable_path, value="", value_type="auto"):
        self.add(variable_path, value, value_type)
        return self.get(variable_path)

    def exists(self, variable_path):
        variable_path = str(variable_path or "").strip()
        if not variable_path:
            return False

        parts = variable_path.split(".")
        variable_name = parts[0]

        if variable_name not in self.runtime.variables:
            return False

        if len(parts) == 1:
            return True

        marker = object()
        value = self.runtime.variables.get(variable_name)
        nested_path = ".".join(parts[1:])
        return self.runtime.helper.get_nested_value(value, nested_path, marker) is not marker

    def get(self, variable_path, default=None):
        variable_path = str(variable_path or "").strip()

        if not variable_path:
            return default

        parts = variable_path.split(".")
        variable_name = parts[0]

        if variable_name not in self.runtime.variables:
            return default

        value = self.runtime.variables.get(variable_name)
        nested_path = ".".join(parts[1:])

        if not nested_path:
            return value

        return self.runtime.helper.get_nested_value(value, nested_path, default)

    def set(self, variable_path, value, create=True):
        variable_path = str(variable_path or "").strip()
        if not variable_path:
            return False

        parts = variable_path.split(".")
        variable_name = parts[0]

        if create:
            self.add(variable_name)

        if len(parts) == 1:
            self.runtime.variables[variable_name] = value
            return True

        current = self.runtime.variables.get(variable_name)
        if not isinstance(current, dict):
            current = {}

        self.runtime.variables[variable_name] = self.runtime.helper.set_nested_value(current, ".".join(parts[1:]), value)
        return True

    def remove(self, variable_path):
        variable_name = self.root_name(variable_path)
        if not variable_name:
            return False

        removed = False

        if variable_name in self.runtime.variables:
            del self.runtime.variables[variable_name]
            removed = True

        initial_variables = []

        for variable in self.runtime.initial_variables:
            if not isinstance(variable, dict):
                initial_variables.append(variable)
                continue

            name = str(variable.get("name", "") or "").strip()
            if name == variable_name:
                removed = True
                continue

            initial_variables.append(variable)

        self.runtime.initial_variables = initial_variables
        return removed
