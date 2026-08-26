from PySide6.QtWidgets import QButtonGroup, QRadioButton, QVBoxLayout, QWidget

from ..base_field import BaseFormField


class RadioGroupFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        widget.radio_group = QButtonGroup(widget)
        widget.radio_items = []

        for index, option in enumerate(self.get_options(field)):
            radio = QRadioButton(widget)
            radio.setText(str(option.get("title", option.get("value", ""))))
            radio.option_name = str(option.get("name", option.get("value", "")) or "")
            radio.option_value = option.get("value", "")
            widget.radio_group.addButton(radio, index)
            layout.addWidget(radio)
            widget.radio_items.append(radio)

        self.set_value(field, widget, value)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.radio_group.buttonToggled.connect(lambda button, checked: callback(self.get_widget_value(widget)) if checked else None)

    def get_value(self, field, widget):
        return self.get_widget_value(widget)

    def set_value(self, field, widget, value):
        for radio in getattr(widget, "radio_items", []):
            radio.setChecked(getattr(radio, "option_value", "") == value)

    def get_widget_value(self, widget):
        checked_button = widget.radio_group.checkedButton()
        if checked_button is None:
            return ""

        return getattr(checked_button, "option_value", "")

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
