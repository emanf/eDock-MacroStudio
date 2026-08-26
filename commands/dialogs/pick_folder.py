from PySide6.QtWidgets import QApplication, QFileDialog

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


DialogsCategory = MacroCommandCategory("dialogs", "Dialogs", "m:chat")


def active_parent():
    return QApplication.activeWindow()


def run_on_ui(runtime, callback, *args):
    if runtime is not None and hasattr(runtime, "ui") and runtime.ui is not None:
        return runtime.ui.run(callback, *args)
    return callback(*args)


def show_pick_folder_dialog(title, start_dir=""):
    path = QFileDialog.getExistingDirectory(active_parent(), str(title or "Select Folder"), str(start_dir or ""))
    return {"accepted": bool(path), "value": str(path or "")}


class PickFolderCommand(MacroCommand):
    id = "dialogs.pick_folder"
    title = "Pick Folder"
    category = DialogsCategory
    icon = "m:folder"
    description = "Open a folder picker dialog."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "title",
            "title": "Dialog Title",
            "value_type": "string",
            "default_value": "Select Folder",
        },
        {
            "name": "start_dir",
            "title": "Start Directory",
            "value_type": "folder",
            "default_value": "",
            "required": False,
        },
        {
            "name": "result_variable",
            "title": "Save Folder Path To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"pick folder: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        result = run_on_ui(
            runtime,
            show_pick_folder_dialog,
            str(values.get("title", "Select Folder") or "Select Folder"),
            str(values.get("start_dir", "") or ""),
        )
        if result.get("accepted", False):
            runtime.vars.set(values.get("result_variable", ""), result.get("value", ""))
        return result


def register_macro(registry):
    registry.register(PickFolderCommand)