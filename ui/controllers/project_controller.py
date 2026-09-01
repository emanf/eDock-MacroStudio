from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog

from ..dialogs.variables_dialog import VariablesDialog


class ProjectController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.project = window.project
        self.messages = window.messages
        self.history = []
        self.redo_stack = []
        self.max_history = 50

    def is_busy(self):
        return self.window.run_controller.is_busy()

    def on_project_title_changed(self, value):
        self.project.title = (
            str(value or "").strip() or "Untitled Project"
        )
        self.project.name = self.window.storage.safe_name(
            self.project.title
        )

    def sync_execution_from_ui(self):
        self.project.execution = self.project.normalize_execution(
            self.window.control_bar.execution_data()
        )
        return self.project.execution

    def project_data(self):
        self.project.ensure_main_macro()
        self.window.sync_active_macro_from_ui()
        self.sync_execution_from_ui()
        return self.project.to_data(
            variables=self.collect_defined_variables(),
            execution=self.project.execution,
        )

    def has_unsaved_changes(self):
        return self.project.has_unsaved_changes(self.project_data())

    def confirm_discard_changes(self, title, text, accept_text):
        if not self.has_unsaved_changes():
            return True

        return self.messages.confirm(
            title,
            text,
            "Your current changes will be lost if you continue.",
            accept_text,
        )

    def confirm_new_macro(self):
        return self.confirm_discard_changes(
            "New Project",
            "Open a new project?",
            "New",
        )

    def confirm_open_macro(self):
        return self.confirm_discard_changes(
            "Open Project",
            "Open another project?",
            "Open",
        )

    def push_state(self):
        self.window.sync_active_macro_from_ui()
        self.sync_execution_from_ui()
        
        state = {
            "title": self.project.title,
            "name": self.project.name,
            "path": Path(self.project.path) if self.project.path else None,
            "macros": deepcopy(self.project.macros),
            "variables": deepcopy(self.project.variables),
            "execution": deepcopy(self.project.execution),
            "active_index": self.project.active_index
        }
        
        if self.history and self._states_equal(self.history[-1], state):
            return

        self.history.append(state)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if len(self.history) <= 1:
            return

        self.window.sync_active_macro_from_ui()
        self.sync_execution_from_ui()
        
        current_state = {
            "title": self.project.title,
            "name": self.project.name,
            "path": Path(self.project.path) if self.project.path else None,
            "macros": deepcopy(self.project.macros),
            "variables": deepcopy(self.project.variables),
            "execution": deepcopy(self.project.execution),
            "active_index": self.project.active_index
        }
        self.redo_stack.append(current_state)

        self.history.pop()
        previous_state = self.history[-1]
        self._apply_state(previous_state)

    def redo(self):
        if not self.redo_stack:
            return

        state = self.redo_stack.pop()
        
        self.window.sync_active_macro_from_ui()
        self.sync_execution_from_ui()
        
        current_state = {
            "title": self.project.title,
            "name": self.project.name,
            "path": Path(self.project.path) if self.project.path else None,
            "macros": deepcopy(self.project.macros),
            "variables": deepcopy(self.project.variables),
            "execution": deepcopy(self.project.execution),
            "active_index": self.project.active_index
        }
        self.history.append(current_state)
        self._apply_state(state)

    def _apply_state(self, state):
        self.project.title = state["title"]
        self.project.name = state["name"]
        self.project.path = state["path"]
        self.project.macros = deepcopy(state["macros"])
        self.project.variables = deepcopy(state["variables"])
        self.project.execution = deepcopy(state["execution"])
        self.project.active_index = state["active_index"]

        self.window.title_bar.set_project_title(self.project.title)
        self.window.control_bar.set_execution_data(self.project.execution)
        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()
        self.sync_variables_dialog()

    def _states_equal(self, s1, s2):
        try:
            return (
                s1["title"] == s2["title"] and
                s1["name"] == s2["name"] and
                s1["path"] == s2["path"] and
                s1["active_index"] == s2["active_index"] and
                len(s1["macros"]) == len(s2["macros"]) and
                len(s1["variables"]) == len(s2["variables"]) and
                s1["execution"] == s2["execution"] and
                all(
                    m1.serialize() == m2.serialize() 
                    for m1, m2 in zip(s1["macros"], s2["macros"])
                )
            )
        except Exception:
            return False

    def new_project(self, checked=False, mark_saved=False):
        if self.is_busy():
            self.messages.show_warning(
                "Macro Running",
                "Stop the running macro before creating a new project.",
            )
            return

        if not mark_saved and not self.confirm_new_macro():
            return

        self.project.reset()
        self.window.run_controller.reset_session()
        self.window.control_bar.set_execution_data(
            self.project.execution
        )

        self.window.title_bar.set_project_title(self.project.title)

        self.window.items_controller.history_map.clear()

        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()
        self.sync_variables_dialog()
        self.project.mark_saved(self.project_data())
        
        self.history.clear()
        self.redo_stack.clear()
        self.push_state()

    def collect_defined_variables(self):
        dialog = VariablesDialog.instance()
        if dialog is not None:
            self.project.variables = dialog.get_variables()
        return list(self.project.variables or [])

    def sync_variables_dialog(self):
        dialog = VariablesDialog.create_instance(
            parent=self.window,
            variables=self.project.variables,
        )
        self.window.run_controller.runner.set_variables_provider(
            dialog.get_variables
        )
        return dialog

    def show_variables_dialog(self):
        dialog = self.sync_variables_dialog()
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.project.variables = dialog.get_variables()
            self.push_state()

    def save_project(self):
        self.project.ensure_main_macro()
        self.window.sync_active_macro_from_ui()
        self.project.variables = self.collect_defined_variables()
        self.sync_execution_from_ui()

        if self.project.path is None:
            path, _ = QFileDialog.getSaveFileName(
                self.window,
                "Save Project",
                str(
                    self.window.storage.project_path(
                        self.project.name
                    )
                ),
                "Macro Project JSON (*.json)",
            )

            if not path:
                return

            self.project.path = Path(path)
            new_title = self.project.path.stem.strip()

            if new_title:
                self.project.title = new_title
                self.project.name = self.window.storage.safe_name(
                    new_title
                )
                self.window.title_bar.set_project_title(
                    self.project.title
                )

        try:
            active_macro = ""
            if (
                0
                <= self.project.active_index
                < len(self.project.macros)
            ):
                active_macro = self.project.macros[
                    self.project.active_index
                ].name

            path = self.window.storage.save_project(
                self.project.path,
                self.project.title,
                self.project.name,
                self.project.macros,
                active_macro,
                self.project.variables,
                self.project.execution,
            )
            self.project.path = path
            self.project.mark_saved(self.project_data())
            self.window.title_bar.set_project_title(self.project.title)
            self.messages.show_information(
                "Saved",
                f"Project saved:\n{path}",
            )
        except Exception as e:
            self.messages.show_critical("Save Failed", str(e))

    def open_project(self):
        if self.is_busy():
            self.messages.show_warning(
                "Macro Running",
                "Stop the running macro before opening another project.",
            )
            return

        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Open Project",
            str(self.window.storage.projects_dir()),
            "Macro Project JSON (*.json)",
        )

        if not path:
            return

        mode = self.messages.ask_open_project_mode()
        if mode is None:
            return

        if mode == "replace" and not self.confirm_open_macro():
            return

        project = self.window.storage.load_project(path)

        if mode == "merge":
            self.merge_project(project)
            return

        self.load_project(project, path)

    def load_project(self, project, path=None):
        self.project.title = (
            str(
                project.get("title", "")
                or "Untitled Project"
            ).strip()
            or "Untitled Project"
        )
        self.project.name = self.window.storage.safe_name(
            project.get("name", "") or self.project.title
        )
        self.project.path = Path(path) if path else None
        self.project.variables = list(
            project.get("variables", []) or []
        )
        self.project.execution = (
            self.project.normalize_execution(
                project.get("execution")
            )
        )
        self.project.macros = list(
            project.get("macros", []) or []
        )
        self.project.ensure_main_macro()

        self.window.title_bar.set_project_title(self.project.title)
        self.window.control_bar.set_execution_data(
            self.project.execution
        )

        self.window.items_controller.history_map.clear()

        active_macro_name = str(
            project.get("active_macro", "") or ""
        ).strip()
        self.project.active_index = 0

        for index, macro in enumerate(self.project.macros):
            if macro.name == active_macro_name:
                self.project.active_index = index
                break

        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()
        self.sync_variables_dialog()
        self.project.mark_saved(self.project_data())
        
        self.history.clear()
        self.redo_stack.clear()
        self.push_state()

    def merge_project(self, project):
        self.window.sync_active_macro_from_ui()
        self.project.ensure_main_macro()

        imported_variables = list(
            project.get("variables", []) or []
        )
        existing_variables = {
            str(variable.get("name", "") or "").strip()
            for variable in self.project.variables
            if isinstance(variable, dict)
        }

        for variable in imported_variables:
            if not isinstance(variable, dict):
                continue

            name = str(
                variable.get("name", "") or ""
            ).strip()
            if not name or name in existing_variables:
                continue

            self.project.variables.append(
                {
                    "name": name,
                    "type": str(
                        variable.get("type", "auto") or "auto"
                    ).strip()
                    or "auto",
                    "value": variable.get("value", ""),
                }
            )
            existing_variables.add(name)

        imported_macros = list(
            project.get("macros", []) or []
        )
        first_inserted_index = None

        for macro in imported_macros:
            imported = deepcopy(macro)
            imported.title = self.project.unique_macro_title(
                imported.title or "Macro1"
            )
            imported.name = self.project.unique_macro_name(
                imported.title
            )
            imported.variables = []
            self.project.macros.append(imported)

            if first_inserted_index is None:
                first_inserted_index = (
                    len(self.project.macros) - 1
                )

        if first_inserted_index is not None:
            self.project.active_index = first_inserted_index

        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()
        self.sync_variables_dialog()
        self.push_state()
