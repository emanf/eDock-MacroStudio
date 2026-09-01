from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..forms.form_builder import FormBuilder
from ..styles.main_style import MAIN_STYLE
from ..widgets.title_bar import TitleBar


class VariablesDialog(QDialog):
    _instance = None

    def __init__(self, parent=None, variables=None):
        super().__init__(parent)
        self.variables = self.merge_variables(list(variables or []), [])

        self.setWindowTitle("Variables")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(640, 420)
        self.setMinimumSize(520, 340)
        self.setStyleSheet(MAIN_STYLE)

        self.build_ui()
        self.refresh_variables_table()

    @classmethod
    def instance(cls):
        return cls._instance

    @classmethod
    def create_instance(cls, parent=None, variables=None):
        if cls._instance is None:
            cls._instance = cls(parent=parent, variables=variables)
        else:
            if parent is not None and cls._instance.parent() is None:
                cls._instance.setParent(parent)
            if variables is not None:
                cls._instance.set_variables(variables)
            else:
                cls._instance.set_variables(cls._instance.variables)
        return cls._instance

    @classmethod
    def normalize_variable(cls, variable):
        return {
            "name": str(variable.get("name", "") or "").strip(),
            "type": str(variable.get("type", "auto") or "auto").strip() or "auto",
            "value": variable.get("value", ""),
        }

    @classmethod
    def merge_variables(cls, variables, extra_variables):
        merged = []
        names = set()

        for variable in list(variables or []) + list(extra_variables or []):
            if not isinstance(variable, dict):
                continue

            normalized = cls.normalize_variable(variable)
            name = normalized.get("name", "")
            if not name or name in names:
                continue

            merged.append(normalized)
            names.add(name)

        return merged

    @classmethod
    def add_variable_if_missing(cls, variable_name, variable_type="auto", variable_value=""):
        variable_name = str(variable_name or "").strip()
        variable_type = str(variable_type or "auto").strip() or "auto"

        if not variable_name:
            return

        if cls._instance is None:
            return

        cls._instance.variables = cls.merge_variables(
            cls._instance.variables,
            [{
                "name": variable_name,
                "type": variable_type,
                "value": variable_value,
            }],
        )
        cls._instance.refresh_variables_table()

    def set_variables(self, variables):
        self.variables = self.merge_variables(list(variables or []), [])
        self.refresh_variables_table()

    def get_variable_names(self):
        return [
            str(variable.get("name", "") or "").strip()
            for variable in self.variables
            if str(variable.get("name", "") or "").strip()
        ]

    def build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        card = QWidget()
        card.setObjectName("rootCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        card.setLayout(card_layout)
        outer.addWidget(card)

        card_layout.addWidget(
            TitleBar(
                self,
                title="Variables",
                window_buttons=False,
            )
        )

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        content.setLayout(layout)
        card_layout.addWidget(content, 1)

        panel = QFrame()
        panel.setObjectName("Panel")

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 14, 14, 14)
        panel_layout.setSpacing(10)

        top = QHBoxLayout()

        title_box = QVBoxLayout()
        title = QLabel("Variables")
        title.setObjectName("Title")

        subtitle = QLabel("Manage global runtime variables used when the macro starts.")
        subtitle.setObjectName("Subtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.add_variable_button = QPushButton("Add Variable")
        self.add_variable_button.setObjectName("Primary")
        self.add_variable_button.clicked.connect(self.add_variable)

        self.remove_variable_button = QPushButton("Remove Variable")
        self.remove_variable_button.setObjectName("Danger")
        self.remove_variable_button.clicked.connect(self.remove_variable)

        top.addLayout(title_box)
        top.addStretch()
        top.addWidget(self.add_variable_button)
        top.addWidget(self.remove_variable_button)

        self.variables_table = QTableWidget(0, 3)
        self.variables_table.setHorizontalHeaderLabels(["Name", "Type", "Value"])
        self.variables_table.verticalHeader().setVisible(False)
        self.variables_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.variables_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.variables_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.variables_table.setAlternatingRowColors(False)
        self.variables_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.variables_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.variables_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.variables_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.variables_table.horizontalHeader().setStretchLastSection(True)
        self.variables_table.setColumnWidth(0, 180)
        self.variables_table.setColumnWidth(1, 100)
        self.variables_table.setColumnWidth(2, 180)
        self.variables_table.itemSelectionChanged.connect(self.update_actions)
        self.variables_table.cellDoubleClicked.connect(self.edit_variable)

        bottom = QHBoxLayout()
        bottom.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        bottom.addWidget(close_button)

        panel_layout.addLayout(top)
        panel_layout.addWidget(self.variables_table, 1)
        panel_layout.addLayout(bottom)

        layout.addWidget(panel, 1)

    def refresh_variables_table(self):
        self.variables_table.setRowCount(len(self.variables))

        for row, variable in enumerate(self.variables):
            name_item = QTableWidgetItem(str(variable.get("name", "") or ""))
            type_item = QTableWidgetItem(str(variable.get("type", "auto") or "auto"))
            value_item = QTableWidgetItem(str(variable.get("value", "") or ""))

            name_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            self.variables_table.setItem(row, 0, name_item)
            self.variables_table.setItem(row, 1, type_item)
            self.variables_table.setItem(row, 2, value_item)

        self.update_actions()

    def update_actions(self):
        self.remove_variable_button.setEnabled(self.variables_table.currentRow() >= 0)

    def variable_fields(self):
        return [
            {
                "name": "variable_name",
                "title": "Variable Name",
                "place_holder": "my_variable",
                "value_type": "string",
                "default_value": "",
            },
            {
                "name": "variable_type",
                "title": "Variable Type",
                "value_type": "choice",
                "options": ["auto", "string", "int", "float", "bool", "json"],
                "default_value": "auto",
            },
            {
                "name": "variable_value",
                "required": False,
                "title": "Value",
                "place_holder": "Initial variable value",
                "value_type": "string",
                "default_value": "",
            },
        ]

    def add_variable(self):
        data = FormBuilder.get_data(
            schema={
                "title": "Add Variable",
                "submit_text": "Add",
                "fields": self.variable_fields(),
            },
            values={
                "variable_name": "",
                "variable_type": "auto",
                "variable_value": "",
            },
            parent=self,
            runtime_variables=self.variables,
        )

        if data is None:
            return

        variable_name = str(data.get("variable_name", "") or "").strip()
        variable_type = str(data.get("variable_type", "auto") or "auto").strip()
        variable_value = data.get("variable_value", "")

        if not variable_name:
            parent = self.parent()
            if parent is not None and hasattr(parent, "show_warning"):
                parent.show_warning("Variables", "Variable name cannot be empty.")
            return

        for variable in self.variables:
            if str(variable.get("name", "") or "").strip() == variable_name:
                parent = self.parent()
                if parent is not None and hasattr(parent, "show_warning"):
                    parent.show_warning("Variables", f"Variable '{variable_name}' already exists.")
                return

        self.variables.append({
            "name": variable_name,
            "type": variable_type,
            "value": variable_value,
        })
        self.refresh_variables_table()

    def edit_variable(self, row, column):
        if row < 0 or row >= len(self.variables):
            return

        variable = self.variables[row]
        old_name = str(variable.get("name", "") or "").strip()

        data = FormBuilder.get_data(
            schema={
                "title": "Edit Variable",
                "submit_text": "Save",
                "fields": self.variable_fields(),
            },
            values={
                "variable_name": str(variable.get("name", "") or ""),
                "variable_type": str(variable.get("type", "auto") or "auto"),
                "variable_value": variable.get("value", ""),
            },
            parent=self,
            runtime_variables=self.variables,
        )

        if data is None:
            return

        variable_name = str(data.get("variable_name", "") or "").strip()
        variable_type = str(data.get("variable_type", "auto") or "auto").strip()
        variable_value = data.get("variable_value", "")

        if not variable_name:
            parent = self.parent()
            if parent is not None and hasattr(parent, "show_warning"):
                parent.show_warning("Variables", "Variable name cannot be empty.")
            return

        for index, item in enumerate(self.variables):
            if index != row and str(item.get("name", "") or "").strip() == variable_name:
                parent = self.parent()
                if parent is not None and hasattr(parent, "show_warning"):
                    parent.show_warning("Variables", f"Variable '{variable_name}' already exists.")
                return

        self.variables[row] = {
            "name": variable_name,
            "type": variable_type,
            "value": variable_value,
        }
        self.refresh_variables_table()
        self.variables_table.selectRow(row)

        if old_name and old_name != variable_name:
            self.refactor_variable_rename(old_name, variable_name)

    def refactor_variable_rename(self, old_name, new_name):
        parent = self.parent()
        if parent is None or not hasattr(parent, "rename_variable_references"):
            return

        count = parent.rename_variable_references(old_name, new_name)
        if count and hasattr(parent, "show_information"):
            parent.show_information(
                "Variable Renamed",
                f"Updated {count} reference(s) to '{old_name}' across all macros.",
            )

    def remove_variable(self):
        row = self.variables_table.currentRow()
        if row < 0 or row >= len(self.variables):
            return

        self.variables.pop(row)
        self.refresh_variables_table()

    def get_variables(self):
        return [
            {
                "name": str(variable.get("name", "") or "").strip(),
                "type": str(variable.get("type", "auto") or "auto").strip() or "auto",
                "value": variable.get("value", ""),
            }
            for variable in self.variables
            if str(variable.get("name", "") or "").strip()
        ]
