from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


SystemCategory = MacroCommandCategory("system", "System", "m:settings")


DEFAULT_PYTHON_CODE = """user_name = vars.get("user_name")

if not user_name:
    user_name = "Macro Studio"

greeting = f"Hello {user_name}"

vars.add("greeting")
vars.set("greeting", greeting)

result = greeting"""


def build_python_preview(values):
    target_variable = str(values.get("target_variable", "") or "").strip() or "{Variable}"
    code = str(values.get("python_code", "") or "").strip()

    if not code:
        return {
            "value": f"{target_variable} = None",
            "status": "info",
        }

    return {
        "value": f"{target_variable} = result",
        "status": "info",
    }


class RunPythonCommand(MacroCommand):
    id = "system.run_python"
    title = "Run Python"
    category = SystemCategory
    icon = "m:code"
    description = "Run custom Python code and save the result."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "python_code",
            "title": "Python Code",
            "place_holder": "Code...",
            "value_type": "python_code",
            "default_value": DEFAULT_PYTHON_CODE,
            "line_count": 12,
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "result",
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
            "compute_value": build_python_preview,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        return f"run python -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        python_code = str(values.get("python_code", "") or "")

        local_scope = {
            "runtime": runtime,
            "vars": runtime.vars,
            "helper": runtime.helper,
            "ui": runtime.ui,
            "result": None,
        }

        try:
            exec(python_code, {}, local_scope)
        except Exception as error:
            raise RuntimeError(f"Python execution failed: {error}")

        result_value = local_scope.get("result", None)

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(result_value, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(RunPythonCommand)
