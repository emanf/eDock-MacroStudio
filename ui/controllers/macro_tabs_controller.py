import json
from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog

from ...core import refactor
from ...core.model.macro_group import MacroGroup
from ..forms.form_builder import FormBuilder


class MacroTabsController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.project = window.project
        self.messages = window.messages
        self.clipboard_group = None

    def is_busy(self):
        return self.window.run_controller.is_busy()

    def select_macro(self, index):
        if self.is_busy() and not self.window.run_controller.tab_switch_in_progress:
            self.window.refresh_macro_tabs()
            return

        if index == self.project.active_index:
            return

        self.window.items_controller.sync_history_before_switch()
        self.window.sync_active_macro_from_ui()

        if index < 0 or index >= len(self.project.macros):
            return

        self.project.active_index = index
        self.window.load_active_macro_to_ui()

    def add_project_macro(self):
        if self.is_busy():
            return

        self.window.sync_active_macro_from_ui()
        self.project.ensure_main_macro()

        title = self.project.unique_macro_title("Macro1")
        name = self.project.unique_macro_name(title)
        macro = MacroGroup(name=name, title=title, items=[], variables=[])
        self.project.macros.append(macro)
        self.project.active_index = len(self.project.macros) - 1
        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()

    def add_project_macro_at_index(self, index):
        if self.is_busy():
            return

        self.window.sync_active_macro_from_ui()
        self.project.ensure_main_macro()

        insert_index = max(1, min(int(index), len(self.project.macros)))

        title = self.project.unique_macro_title("Macro1")
        name = self.project.unique_macro_name(title)
        macro = MacroGroup(name=name, title=title, items=[], variables=[])

        self.project.macros.insert(insert_index, macro)
        self.project.active_index = insert_index
        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()

    def edit_project_macro_title(self, index):
        if self.is_busy():
            return

        if index <= 0 or index >= len(self.project.macros):
            return

        macro = self.project.macros[index]

        data = FormBuilder.get_data(
            schema={
                "title": "Edit Macro Title",
                "submit_text": "Save",
                "fields": [
                    {
                        "name": "title",
                        "title": "Title",
                        "value_type": "string",
                        "default_value": macro.title or "Untitled Macro",
                    },
                ],
            },
            values={
                "title": macro.title or "Untitled Macro",
            },
            parent=self.window,
        )

        if data is None:
            return

        old_title = str(macro.title or "").strip()
        old_name = str(macro.name or "").strip()

        title = self.project.unique_macro_title(
            str(data.get("title", "") or "Untitled Macro").strip(),
            exclude_index=index,
        )
        macro.title = title
        macro.name = self.project.unique_macro_name(title, exclude_index=index)

        count = refactor.rename_macro_group_references(
            self.project.macros,
            self.window.registry,
            old_name,
            macro.name,
            old_title=old_title,
            new_title=macro.title,
        )

        if count or index == self.project.active_index:
            self.window.load_active_macro_to_ui()

        self.window.refresh_macro_tabs()

        if count:
            self.messages.show_information(
                "Macro Group Renamed",
                f"Updated {count} 'Run Macro Group' reference(s) to '{old_title or old_name}'.",
            )

    def copy_project_macro(self, index):
        if index < 0 or index >= len(self.project.macros):
            return

        self.window.sync_active_macro_from_ui()
        self.clipboard_group = deepcopy(self.project.macros[index])

    def cut_project_macro(self, index):
        if self.is_busy():
            return

        if index <= 0 or index >= len(self.project.macros):
            return

        self.window.sync_active_macro_from_ui()
        self.clipboard_group = deepcopy(self.project.macros[index])
        self.remove_project_macro_at(index)

    def paste_project_macro(self, index):
        if self.is_busy():
            return

        if self.clipboard_group is None:
            return

        self.window.sync_active_macro_from_ui()
        self.project.ensure_main_macro()

        macro = deepcopy(self.clipboard_group)
        macro.title = self.project.unique_macro_title(macro.title or "Macro1")
        macro.name = self.project.unique_macro_name(macro.title)
        macro.variables = []

        insert_index = index + 1 if index >= 0 else len(self.project.macros)
        insert_index = max(1, min(insert_index, len(self.project.macros)))

        self.project.macros.insert(insert_index, macro)
        self.project.active_index = insert_index
        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()

    def save_project_macro_group(self, index):
        if index < 0 or index >= len(self.project.macros):
            return

        self.window.sync_active_macro_from_ui()

        macro = self.project.macros[index]
        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Save Macro Group",
            str(self.window.storage.macro_path(macro.name or macro.title)),
            "Macro JSON (*.json)",
        )

        if not path:
            return

        try:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(macro.to_json(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.messages.show_information("Saved", f"Macro group saved:\n{output_path}")
        except Exception as e:
            self.messages.show_critical("Save Failed", str(e))

    def delete_project_macro(self, index):
        if self.is_busy():
            return

        if index <= 0 or index >= len(self.project.macros):
            return

        confirmed = self.messages.confirm(
            "Delete Macro",
            f"Delete macro '{self.project.macros[index].title}'?",
            "This macro tab and its items will be removed.",
            "Delete",
        )

        if not confirmed:
            return

        self.remove_project_macro_at(index)

    def remove_project_macro_at(self, index):
        if index <= 0 or index >= len(self.project.macros):
            return

        self.project.macros.pop(index)

        if self.project.active_index >= len(self.project.macros):
            self.project.active_index = len(self.project.macros) - 1
        elif index < self.project.active_index:
            self.project.active_index -= 1
        elif index == self.project.active_index:
            self.project.active_index = min(index, len(self.project.macros) - 1)

        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()

    def reorder_project_macro(self, source_row, target_row):
        if self.is_busy():
            return

        if source_row <= 0 or source_row >= len(self.project.macros):
            return

        self.window.sync_active_macro_from_ui()

        target_row = max(1, min(target_row, len(self.project.macros)))

        macro = self.project.macros.pop(source_row)

        if source_row < target_row:
            target_row -= 1

        target_row = max(1, min(target_row, len(self.project.macros)))
        self.project.macros.insert(target_row, macro)

        if self.project.active_index == source_row:
            self.project.active_index = target_row
        elif source_row < self.project.active_index <= target_row:
            self.project.active_index -= 1
        elif target_row <= self.project.active_index < source_row:
            self.project.active_index += 1

        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()
