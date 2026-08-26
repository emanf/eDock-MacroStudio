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


def show_pick_file_dialog(title, start_dir="", file_filter="All Files (*)"):
    path, _ = QFileDialog.getOpenFileName(active_parent(), str(title or "Select File"), str(start_dir or ""), str(file_filter or "All Files (*)"))
    return {"accepted": bool(path), "value": str(path or "")}


class PickFileCommand(MacroCommand):
    id = "dialogs.pick_file"
    title = "Pick File"
    category = DialogsCategory
    icon = "m:description"
    description = "Open a file picker dialog."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "title",
            "title": "Dialog Title",
            "value_type": "string",
            "default_value": "Select File",
        },
        {
            "name": "start_dir",
            "title": "Start Directory",
            "value_type": "folder",
            "default_value": "",
            "required": False,
        },
        {
            "name": "file_filter",
            "title": "File Filter",
            "value_type": "string",
            "default_value": "All Files (*)",
            "required": False,
        },
        {
            "name": "result_variable",
            "title": "Save File Path To Variable",
            "value_type": "variable",
            "default_value": "",
            "required": False,
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"pick file: {values.get('title')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        result = run_on_ui(
            runtime,
            show_pick_file_dialog,
            str(values.get("title", "Select File") or "Select File"),
            str(values.get("start_dir", "") or ""),
            str(values.get("file_filter", "All Files (*)") or "All Files (*)"),
        )
        if result.get("accepted", False):
            runtime.vars.set(values.get("result_variable", ""), result.get("value", ""))
        return result


def register_macro(registry):
    registry.register(PickFileCommand)