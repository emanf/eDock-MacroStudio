from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


FilesCategory = MacroCommandCategory("files", "Files", "mc:e2c7")


class ReadFileToVariableCommand(MacroCommand):
    id = "files.read_to_variable"
    title = "Read File To Variable"
    category = FilesCategory
    icon = "mc:e24d"
    description = "Read file content and save it into a variable."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "path",
            "title": "File",
            "place_holder": "File path",
            "value_type": "file",
            "default_value": "",
        },
        {
            "name": "encoding",
            "title": "Encoding",
            "place_holder": "utf-8",
            "value_type": "string",
            "default_value": "utf-8",
        },
        {
            "name": "variable_name",
            "title": "Save To Variable",
            "place_holder": "file_content",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"read file {values.get('path')} to {values.get('variable_name')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        path = str(values.get("path", "") or "")
        encoding = str(values.get("encoding", "utf-8") or "utf-8")
        variable_name = values.get("variable_name")

        with open(path, "r", encoding=encoding) as file:
            content = file.read()

        if variable_name:
            runtime.vars.set(variable_name, content)

        return {
            "path": path,
            "text": content,
            "length": len(content),
        }


def register_macro(registry):
    registry.register(ReadFileToVariableCommand)
