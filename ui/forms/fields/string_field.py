from PySide6.QtWidgets import QLineEdit

from ..base_field import BaseFormField


class StringFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QLineEdit(parent)
        widget.setPlaceholderText(str(field.get("place_holder", "") or ""))
        widget.setText("" if value is None else str(value))
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.textChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.text()

    def set_value(self, field, widget, value):
        widget.setText("" if value is None else str(value))
