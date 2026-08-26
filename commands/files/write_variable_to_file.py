import json
import os

from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


FilesCategory = MacroCommandCategory("files", "Files", "mc:e2c7")


class WriteVariableToFileCommand(MacroCommand):
    id = "files.write_variable_to_file"
    title = "Write Variable To File"
    category = FilesCategory
    icon = "mc:e161"
    description = "Write a variable value into a file."
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
            "name": "source_variable",
            "title": "Variable",
            "place_holder": "file_content",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "encoding",
            "title": "Encoding",
            "place_holder": "utf-8",
            "value_type": "string",
            "default_value": "utf-8",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"write {values.get('source_variable')} to file {values.get('path')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        path = str(values.get("path", "") or "")
        source_variable = values.get("source_variable")
        encoding = str(values.get("encoding", "utf-8") or "utf-8")
        source_value = runtime.vars.get(source_variable, "")

        if isinstance(source_value, (dict, list)):
            text = json.dumps(source_value, ensure_ascii=False, indent=2)
        else:
            text = str(source_value or "")

        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(path, "w", encoding=encoding) as file:
            file.write(text)

        return {
            "path": path,
            "text": text,
            "length": len(text),
        }


def register_macro(registry):
    registry.register(WriteVariableToFileCommand)
