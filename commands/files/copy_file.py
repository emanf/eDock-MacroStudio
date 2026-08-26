import shutil

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


FilesCategory = MacroCommandCategory("files", "Files", "mc:e2c7")


class CopyFileCommand(MacroCommand):
    id = "files.copy_file"
    title = "Copy File"
    category = FilesCategory
    icon = "mc:e14d"
    description = "Copy a file from source to destination."
    fields = [
        {
            "name": "source",
            "title": "Source",
            "place_holder": "Source path",
            "value_type": "file",
            "default_value": "",
        },
        {
            "name": "destination",
            "title": "Destination",
            "place_holder": "Destination path",
            "value_type": "folder",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"copy file from {values.get('source')} to {values.get('destination')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        source = str(values.get("source", "") or "")
        destination = str(values.get("destination", "") or "")
        if source and destination:
            shutil.copy2(source, destination)
        return None


def register_macro(registry):
    registry.register(CopyFileCommand)
