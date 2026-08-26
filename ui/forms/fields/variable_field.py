from weakref import WeakSet

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QWidget

from core.rendering.material_icons import MaterialIcons

from ..base_field import BaseFormField


class VariablePickerInput(QWidget):
    _instances = WeakSet()

    def __init__(self, field, value=None, parent=None, context=None):
        super().__init__(parent)

        self.field = field
        self.context = context
        self.material_font = MaterialIcons.ensure_font()

        VariablePickerInput._instances.add(self)

        self.input = QComboBox(self)
        self.input.setEditable(True)

        options = [str(option) for option in field.get("options", [])]
        self.input.addItems(options)

        self.button = QPushButton("add", self)
        self.button.setFont(QFont(self.material_font))
        self.button.clicked.connect(self.add_variable)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.input, 1)
        layout.addWidget(self.button)

        self.setText(value)
        self.refresh_variables()

    @classmethod
    def refresh_all_variables(cls):
        for instance in list(cls._instances):
            instance.refresh_variables()

    def showEvent(self, event):
        self.refresh_variables()
        super().showEvent(event)

    def add_variable(self):
        if self.context is None:
            return

        dialog = self.context.get_sync_variables_dialog()
        if dialog is None:
            return

        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        new_variables = dialog.get_variables()
        self.context.set_defined_variables(new_variables)

        callback = self.field.get("on_variable_added")
        if callable(callback):
            get_options_callback = self.field.get("get_variable_options")
            existing_options = set(get_options_callback() or []) if callable(get_options_callback) else set()

            for variable in new_variables:
                if not isinstance(variable, dict):
                    continue

                variable_name = str(variable.get("name", "") or "").strip()
                if variable_name and variable_name not in existing_options:
                    callback(variable_name)
                    existing_options.add(variable_name)

        parent_dialog = self.window()
        if hasattr(parent_dialog, "runtime_variables"):
            parent_dialog.runtime_variables = list(new_variables)

        VariablePickerInput.refresh_all_variables()

        if new_variables:
            last_variable = new_variables[-1]
            if isinstance(last_variable, dict):
                self.setText(str(last_variable.get("name", "") or ""))

    def refresh_variables(self):
        callback = self.field.get("get_variable_options")
        if callable(callback):
            options = [str(option) for option in callback() or []]
        else:
            options = self.get_runtime_variable_names()

        selected_text = self.text()

        self.input.blockSignals(True)
        self.input.clear()
        self.input.addItems(options)
        self.input.blockSignals(False)

        self.setText(selected_text)

    def get_runtime_variable_names(self):
        parent_dialog = self.window()
        runtime_variables = getattr(parent_dialog, "runtime_variables", None) if parent_dialog is not None else None

        if runtime_variables is None and self.context is not None:
            runtime_variables = self.context.get_defined_variables()

        return [
            str(variable.get("name", "") or "").strip()
            for variable in runtime_variables or []
            if isinstance(variable, dict) and str(variable.get("name", "") or "").strip()
        ]

    def text(self):
        return self.input.currentText().strip()

    def setText(self, value):
        text = "" if value is None else str(value)
        self.input.setEditText(text)


class VariableFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = VariablePickerInput(field, value, parent, self.context)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.input.editTextChanged.connect(lambda _: callback(widget.text()))
        widget.input.currentIndexChanged.connect(lambda _: callback(widget.text()))

    def get_value(self, field, widget):
        return widget.text()

    def set_value(self, field, widget, value):
        widget.setText(value)
        widget.refresh_variables()
