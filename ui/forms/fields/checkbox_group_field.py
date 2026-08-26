from PySide6.QtWidgets import QCheckBox, QVBoxLayout, QWidget

from ..base_field import BaseFormField


class CheckboxGroupFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        widget.checkbox_items = []
        selected_values = self.normalize_values(value)

        for option in self.get_options(field):
            checkbox = QCheckBox(widget)
            checkbox.setText(str(option.get("title", option.get("value", ""))))
            checkbox.option_name = str(option.get("name", option.get("value", "")) or "")
            checkbox.option_value = option.get("value", "")
            checkbox.setChecked(checkbox.option_value in selected_values)
            layout.addWidget(checkbox)
            widget.checkbox_items.append(checkbox)

        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        for checkbox in getattr(widget, "checkbox_items", []):
            checkbox.toggled.connect(lambda checked=False, target=widget: callback(self.get_widget_value(target)))

    def get_value(self, field, widget):
        return self.get_widget_value(widget)

    def set_value(self, field, widget, value):
        selected_values = self.normalize_values(value)

        for checkbox in getattr(widget, "checkbox_items", []):
            checkbox.setChecked(getattr(checkbox, "option_value", "") in selected_values)

    def get_widget_value(self, widget):
        result = []

        for checkbox in getattr(widget, "checkbox_items", []):
            if checkbox.isChecked():
                result.append(getattr(checkbox, "option_value", ""))

        return result

    def get_options(self, field):
        options = field.get("options", [])
        if not isinstance(options, list):
            return []

        result = []
        for option in options:
            if isinstance(option, dict):
                option_value = option.get("value", "")
                result.append({
                    "name": option.get("name", option_value),
                    "title": option.get("title", option_value),
                    "value": option_value,
                })
            else:
                result.append({
                    "name": option,
                    "title": option,
                    "value": option,
                })

        return result

    def normalize_values(self, value):
        if value is None:
            return []

        if isinstance(value, list):
            return value

        if isinstance(value, tuple):
            return list(value)

        if isinstance(value, set):
            return list(value)

        return [value]
