from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ...core import refactor
from ...core.macro_registry import MacroRegistry
from ...core.macro_storage import MacroStorage
from ...core.model.macro_group import MacroGroup
from ...core.model.macro_project import MacroProject
from ..widgets.category_list import CategoryList
from ..widgets.command_list import CommandList
from ..widgets.control_bar import ControlBar
from ..widgets.header_bar import HeaderBar
from ..widgets.macro_list import MacroList
from ..widgets.macro_tabs import MacroTabs
from ..dialogs.variables_dialog import VariablesDialog
from ..forms.form_builder import FormBuilder
from ..forms.form_context import FormContext
from ..forms.fields_registry import create_default_registry
from ..services.message_service import MessageService
from ..controllers.run_controller import RunController
from ..controllers.macro_tabs_controller import MacroTabsController
from ..controllers.macro_items_controller import MacroItemsController
from ..controllers.project_controller import ProjectController

from ...ui.styles.main_style import MAIN_STYLE


class MacroStudioWindow(QMainWindow):
    def __init__(self, app_ref, registry: MacroRegistry, storage: MacroStorage, parent=None):
        super().__init__(parent)
        self.app_ref = app_ref
        self.registry = registry
        self.storage = storage

        self.project = MacroProject(safe_name=storage.safe_name)
        self.current_group = MacroGroup(name="main", title="Main", items=[], variables=[])
        self.messages = MessageService(self)
        self.run_controller = RunController(self)
        self.tabs_controller = MacroTabsController(self)
        self.items_controller = MacroItemsController(self)
        self.project_controller = ProjectController(self)

        FormBuilder.set_registry(create_default_registry(FormContext(self)))

        icon_path = Path(__file__).resolve().parents[2] / "assets" / "macro_studio.png"

        self.setWindowTitle("Macro Studio")
        self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1240, 760)
        self.setMinimumSize(1040, 660)
        self.apply_theme_change()
        self.build_ui()
        self.variables_dialog = VariablesDialog.create_instance(parent=self, variables=self.project.variables)
        self.run_controller.runner.set_variables_provider(self.collect_defined_variables)
        self.load_categories()
        self.project_controller.new_project(mark_saved=True)

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.header_bar = HeaderBar()
        self.header_bar.title_changed.connect(self.project_controller.on_project_title_changed)
        self.header_bar.new_clicked.connect(self.project_controller.new_project)
        self.header_bar.open_clicked.connect(self.project_controller.open_project)
        self.header_bar.save_clicked.connect(self.project_controller.save_project)
        layout.addWidget(self.header_bar)

        self.control_bar = ControlBar()
        self.control_bar.run_main_clicked.connect(self.run_controller.run_main_macro)
        self.control_bar.run_selected_clicked.connect(self.run_controller.run_macro)
        self.control_bar.pause_clicked.connect(self.run_controller.toggle_pause)
        self.control_bar.record_clicked.connect(self.run_controller.toggle_recording)
        layout.addWidget(self.control_bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.category_list = CategoryList()
        self.category_list.setMinimumWidth(50)
        self.category_list.category_selected.connect(self.on_category_selected)

        self.command_list = CommandList()
        self.command_list.setMinimumWidth(50)
        self.command_list.command_requested.connect(self.items_controller.add_macro_by_id)

        self.macro_list = MacroList()
        self.macro_list.item_edit_requested.connect(self.items_controller.edit_macro_item)
        self.macro_list.macro_dropped.connect(self.items_controller.add_macro_by_id_at)
        self.macro_list.item_delete_requested.connect(self.items_controller.delete_item_at)
        self.macro_list.item_copy_requested.connect(self.items_controller.copy_item_at)
        self.macro_list.item_cut_requested.connect(self.items_controller.cut_item_at)
        self.macro_list.item_paste_requested.connect(self.items_controller.paste_item_at)
        self.macro_list.item_toggle_enabled_requested.connect(self.items_controller.toggle_item_enabled)
        self.macro_list.undo_requested.connect(self.items_controller.undo)
        self.macro_list.redo_requested.connect(self.items_controller.redo)
        self.macro_list.history_state_requested.connect(self.items_controller.record_state)

        self.macro_tabs = MacroTabs()
        self.macro_tabs.macro_selected.connect(self.tabs_controller.select_macro)
        self.macro_tabs.macro_new_requested.connect(self.tabs_controller.add_project_macro)
        self.macro_tabs.macro_new_here_requested.connect(self.tabs_controller.add_project_macro_at_index)
        self.macro_tabs.macro_edit_requested.connect(self.tabs_controller.edit_project_macro_title)
        self.macro_tabs.macro_copy_requested.connect(self.tabs_controller.copy_project_macro)
        self.macro_tabs.macro_cut_requested.connect(self.tabs_controller.cut_project_macro)
        self.macro_tabs.macro_paste_requested.connect(self.tabs_controller.paste_project_macro)
        self.macro_tabs.macro_delete_requested.connect(self.tabs_controller.delete_project_macro)
        self.macro_tabs.macro_save_requested.connect(self.tabs_controller.save_project_macro_group)
        self.macro_tabs.macro_reordered.connect(self.tabs_controller.reorder_project_macro)

        self.delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.macro_list)
        self.delete_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.delete_shortcut.activated.connect(self.on_delete_shortcut_activated)

        sidebar_panel = self.panel("Categories", self.category_list)
        commands_panel = self.panel("Commands", self.command_list)
        macro_panel = self.macro_list_panel()

        splitter.addWidget(sidebar_panel)
        splitter.addWidget(commands_panel)
        splitter.addWidget(macro_panel)
        splitter.setSizes([280, 280, 680])

        layout.addWidget(splitter, 1)

    def on_delete_shortcut_activated(self):
        selected_rows = self.macro_list.selected_rows()
        if selected_rows:
            self.items_controller.delete_item_at(selected_rows)

    def panel(self, title, widget):
        frame = QFrame()
        frame.setObjectName("Panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label = QLabel(title)
        label.setObjectName("Subtitle")

        layout.addWidget(label)
        layout.addWidget(widget, 1)

        return frame

    def macro_list_panel(self):
        frame = QFrame()
        frame.setObjectName("Panel")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        label = QLabel("Macro")
        label.setObjectName("Subtitle")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Active macro title")
        self.name_input.setMinimumWidth(220)
        self.name_input.textChanged.connect(self.on_title_changed)

        self.variables_button = QPushButton("Variables")
        self.variables_button.clicked.connect(self.project_controller.show_variables_dialog)

        header_layout.addWidget(label)
        header_layout.addWidget(self.name_input, 1)
        header_layout.addWidget(self.variables_button)

        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)

        tabs_panel = QFrame()
        tabs_panel.setMinimumWidth(110)
        tabs_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        tabs_layout = QVBoxLayout(tabs_panel)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(0)

        self.macro_tabs.setMinimumWidth(96)
        self.macro_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        tabs_layout.addWidget(self.macro_tabs, 1)

        content_splitter.addWidget(tabs_panel)
        content_splitter.addWidget(self.macro_list)
        content_splitter.setSizes([150, 620])

        layout.addLayout(header_layout)
        layout.addWidget(content_splitter, 1)

        return frame

    def apply_theme_change(self):
        self.setStyleSheet(MAIN_STYLE)

    def load_categories(self):
        self.category_list.set_categories(self.registry.categories())

    def on_category_selected(self, category_id):
        self.command_list.set_commands(self.registry.category_commands(category_id))

    def on_title_changed(self, value):
        if self.project.active_index < 0 or self.project.active_index >= len(self.project.macros):
            return

        if self.project.active_index == 0:
            return

        title = str(value or "").strip() or "Untitled Macro"
        macro = self.project.macros[self.project.active_index]
        old_title = str(macro.title or "").strip()
        old_name = str(macro.name or "").strip()

        macro.title = title
        macro.name = self.project.unique_macro_name(title, exclude_index=self.project.active_index)
        self.current_group = macro

        count = refactor.rename_macro_group_references(
            self.project.macros,
            self.registry,
            old_name,
            macro.name,
            old_title=old_title,
            new_title=macro.title,
        )
        if count:
            self.macro_list.refresh(restore_scroll=True)

        self.refresh_macro_tabs()

    def sync_active_macro_from_ui(self):
        if self.project.active_index < 0 or self.project.active_index >= len(self.project.macros):
            return

        macro = self.project.macros[self.project.active_index]

        if self.project.active_index == 0:
            macro.title = "Main"
            macro.name = "main"
        else:
            macro.title = self.name_input.text().strip() or macro.title or "Untitled Macro"
            macro.name = self.project.unique_macro_name(macro.title, exclude_index=self.project.active_index)

        macro.items = list(self.macro_list.items_data)
        macro.variables = []
        self.current_group = macro

    def refresh_macro_tabs(self):
        self.project.ensure_main_macro()
        self.macro_tabs.set_macros(self.project.macros, self.project.active_index)

    def load_active_macro_to_ui(self):
        if self.project.active_index < 0 or self.project.active_index >= len(self.project.macros):
            self.current_group = MacroGroup(name="", title="", items=[], variables=[])
            self.name_input.blockSignals(True)
            self.name_input.setReadOnly(False)
            self.name_input.setText("")
            self.name_input.blockSignals(False)
            self.macro_list.set_macro_items([], self.registry)
            return

        self.current_group = self.project.macros[self.project.active_index]
        self.name_input.blockSignals(True)
        self.name_input.setReadOnly(self.project.active_index == 0)
        self.name_input.setText(self.current_group.title or "Untitled Macro")
        self.name_input.blockSignals(False)
        self.macro_list.set_macro_items(self.current_group.items, self.registry)
        self.items_controller.initialize_baseline_state()

    def get_macro_history_availability(self):
        return self.items_controller.get_history_availability()

    @property
    def runner(self):
        return self.run_controller.runner

    @property
    def recorder(self):
        return self.run_controller.recorder

    @property
    def project_macros(self):
        return self.project.macros

    @project_macros.setter
    def project_macros(self, value):
        self.project.macros = list(value or [])

    @property
    def project_variables(self):
        return self.project.variables

    @project_variables.setter
    def project_variables(self, value):
        self.project.variables = list(value or [])

    @property
    def active_macro_index(self):
        return self.project.active_index

    @active_macro_index.setter
    def active_macro_index(self, value):
        self.project.active_index = value

    @property
    def macro_clipboard_group(self):
        return self.tabs_controller.clipboard_group

    @property
    def macro_clipboard_item(self):
        return self.items_controller.clipboard_item

    def rename_variable_references(self, old_name, new_name):
        self.sync_active_macro_from_ui()
        count = refactor.rename_variable_references(self.project.macros, self.registry, old_name, new_name)
        if count:
            self.load_active_macro_to_ui()
        return count

    def collect_defined_variables(self):
        return self.project_controller.collect_defined_variables()

    def sync_variables_dialog(self):
        return self.project_controller.sync_variables_dialog()

    def has_unsaved_changes(self):
        return self.project_controller.has_unsaved_changes()

    def show_information(self, title, message):
        self.messages.show_information(title, message)

    def show_warning(self, title, message):
        self.messages.show_warning(title, message)

    def show_critical(self, title, message):
        self.messages.show_critical(title, message)
