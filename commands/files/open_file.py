import os

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


FilesCategory = MacroCommandCategory("files", "Files", "mc:e2c7")


class OpenFileCommand(MacroCommand):
    id = "files.open_file"
    title = "Open File"
    category = FilesCategory
    icon = "mc:e89e"
    description = "Open a file or folder."
    fields = [
        {
            "name": "path",
            "title": "Path",
            "place_holder": "File or folder path",
            "value_type": "file",
            "default_value": "",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"open file: {values.get('path')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        path = str(values.get("path", "") or "")
        context = getattr(runtime, "context", None) if runtime is not None else None
        if context is not None and hasattr(context, "run_file"):
            context.run_file(path)
            return None
        if path:
            os.startfile(path)
        return None


def register_macro(registry):
    registry.register(OpenFileCommand)
