import json
import os

from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


FilesCategory = MacroCommandCategory("files", "Files", "mc:e2c7")


class InsertTextInFileCommand(MacroCommand):
    id = "files.insert_text_in_file"
    title = "Insert Text In File"
    category = FilesCategory
    icon = "mc:e148"
    description = "Insert text or a variable value at the first line, last line, or a custom line."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "path",
            "title": "File",
            "place_holder": "File path",
            "value_type": "file",
            "default_value": "",
        },
        {
            "name": "text_source",
            "title": "Text Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "value",
        },
        {
            "name": "text",
            "required": False,
            "title": "Text",
            "place_holder": "Text to insert",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "source_variable",
            "required": False,
            "title": "Variable",
            "place_holder": "file_content",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "insert_position",
            "title": "Insert Position",
            "value_type": "choice",
            "options": ["first line", "last line", "custom line"],
            "default_value": "last line",
        },
        {
            "name": "line_number",
            "required": False,
            "title": "Line Number",
            "place_holder": "1",
            "value_type": "string",
            "default_value": "1",
            "visible_if": {
                "field": "insert_position",
                "operator": "==",
                "value": "custom line",
            },
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
        text_source = values.get("text_source")
        insert_position = values.get("insert_position")
        line_number = values.get("line_number")
        path = values.get("path")

        if insert_position == "custom line":
            position_text = f"line {line_number}"
        else:
            position_text = insert_position

        if text_source == "variable":
            return f"insert {values.get('source_variable')} in {path} at {position_text}"

        return f"insert text in {path} at {position_text}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        path = str(values.get("path", "") or "")
        text_source = values.get("text_source")
        insert_position = values.get("insert_position")
        line_number = str(values.get("line_number", "1") or "1")
        encoding = str(values.get("encoding", "utf-8") or "utf-8")

        if text_source == "variable":
            source_value = runtime.vars.get(values.get("source_variable"), "")
            if isinstance(source_value, (dict, list)):
                text = json.dumps(source_value, ensure_ascii=False, indent=2)
            else:
                text = str(source_value or "")
        else:
            text = str(values.get("text", "") or "")

        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        if os.path.exists(path):
            with open(path, "r", encoding=encoding) as file:
                lines = file.readlines()
        else:
            lines = []

        if text and not text.endswith("\n"):
            text = text + "\n"

        if insert_position == "first line":
            insert_index = 0
        elif insert_position == "custom line":
            try:
                insert_index = int(line_number) - 1
            except Exception:
                insert_index = 0
            insert_index = max(0, min(insert_index, len(lines)))
        else:
            insert_index = len(lines)

        lines.insert(insert_index, text)

        with open(path, "w", encoding=encoding) as file:
            file.writelines(lines)

        return {
            "path": path,
            "text": text,
            "length": len(text),
            "insert_position": insert_position,
            "line_number": insert_index + 1,
            "line_count": len(lines),
        }


def register_macro(registry):
    registry.register(InsertTextInFileCommand)
