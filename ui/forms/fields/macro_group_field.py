from PySide6.QtWidgets import QComboBox
from ..base_field import BaseFormField

class MacroGroupFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QComboBox(parent)

        if self.context:
            options = self.context.get_macro_group_options()
            for option in options:
                label = option.get("label", "Untitled Macro")
                val = option.get("value", "")
                widget.addItem(str(label), str(val))

        self.set_value(field, widget, value)
        self.bind_changing(field, widget)
        return widget

    def get_value(self, field, widget):
        return {
            "title": widget.currentText(),
            "value": widget.currentData(),
        }

    def set_value(self, field, widget, value):
        if isinstance(value, dict):
            value = value.get("value", "")

        index = widget.findData(str(value or ""))
        if index >= 0:
            widget.setCurrentIndex(index)
        elif widget.count() > 0:
            widget.setCurrentIndex(0)

    def validate_value(self, field, widget, value):
        if isinstance(value, dict):
            value = value.get("value", "")

        if not value:
            return "Please select a macro group."
        return None
