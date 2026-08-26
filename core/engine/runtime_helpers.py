import json

class RuntimeHelpers:
    def __init__(self, runtime):
        self.runtime = runtime
        
    def parse_bool(self, value):
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return value != 0

        if value is None:
            return False

        text = str(value).strip().lower()
        return text in ["true", "1", "yes", "on", "checked", "enabled"]


    def convert_variable_value(self, value, value_type):
        if value_type == "auto":
            return value

        if value_type == "string":
            return "" if value is None else str(value)

        if value_type == "int":
            if value is None or value == "":
                return 0
            return int(float(value))

        if value_type == "float":
            if value is None or value == "":
                return 0.0
            return float(value)

        if value_type == "bool":
            return self.parse_bool(value)

        if value_type == "json":
            if isinstance(value, (dict, list, int, float, bool)) or value is None:
                return value
            return json.loads(str(value))

        return value


    def infer_value_type(self, value):
        if isinstance(value, bool):
            return "bool"

        if isinstance(value, int) and not isinstance(value, bool):
            return "int"

        if isinstance(value, float):
            return "float"

        if isinstance(value, (dict, list)) or value is None:
            return "json"

        return "string"


    def variable_root_name(self, variable_path):
        return str(variable_path or "").strip().split(".")[0]


    def normalize_data_path(self, path):
        text = str(path or "").strip()

        return text


    def get_nested_value(self, data, path, default=None):
        path = self.normalize_data_path(path)

        if not path:
            return data

        current = data

        for part in path.split("."):
            if not part:
                continue

            if isinstance(current, dict):
                if part not in current:
                    return default
                current = current.get(part)
                continue

            if isinstance(current, list):
                try:
                    current = current[int(part)]
                    continue
                except Exception:
                    return default

            return default

        return current


    def set_nested_value(self, data, path, value):
        path = str(path or "").strip()

        if not path:
            return value

        if not isinstance(data, dict):
            data = {}

        current = data
        parts = path.split(".")

        for part in parts[:-1]:
            if not part:
                continue

            next_value = current.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                current[part] = next_value

            current = next_value

        if parts[-1]:
            current[parts[-1]] = value

        return data


    def compare_values(self, left, operator, right):
        left_value = left
        right_value = right

        try:
            left_value = float(left)
            right_value = float(right)
        except Exception:
            pass

        if operator == "==":
            return left_value == right_value

        if operator == "!=":
            return left_value != right_value

        if operator == ">":
            return left_value > right_value

        if operator == "<":
            return left_value < right_value

        if operator == ">=":
            return left_value >= right_value

        if operator == "<=":
            return left_value <= right_value

        if operator == "contains":
            return str(right_value) in str(left_value)

        if operator == "not contains":
            return str(right_value) not in str(left_value)

        if operator == "starts with":
            return str(left_value).startswith(str(right_value))

        if operator == "ends with":
            return str(left_value).endswith(str(right_value))

        if operator == "is true":
            return self.parse_bool(left_value) is True

        if operator == "is false":
            return self.parse_bool(left_value) is False

        return False
