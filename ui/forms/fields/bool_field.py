from PySide6.QtWidgets import QCheckBox

from ..base_field import BaseFormField


class BooleanFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QCheckBox(parent)
        widget.setChecked(bool(value))
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.toggled.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.isChecked()

    def set_value(self, field, widget, value):
        widget.setChecked(bool(value))
