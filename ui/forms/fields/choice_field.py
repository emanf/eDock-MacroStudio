from PySide6.QtWidgets import QComboBox

from ..base_field import BaseFormField


class ChoiceFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QComboBox(parent)
        widget.setEditable(field.get("editable", False) is True)

        place_holder = str(field.get("place_holder", "") or "")
        if place_holder:
            widget.setPlaceholderText(place_holder)
            if widget.isEditable() and widget.lineEdit():
                widget.lineEdit().setPlaceholderText(place_holder)

        options = field.get("options", [])
        if not isinstance(options, list):
            options = []

        for option in options:
            if isinstance(option, dict):
                widget.addItem(str(option.get("title", option.get("value", ""))), option.get("value", ""))
            else:
                widget.addItem(str(option), option)

        index = widget.findData(value)
        if index < 0:
            index = widget.findText(str(value))
        if index >= 0:
            widget.setCurrentIndex(index)
        elif widget.isEditable():
            widget.setCurrentText("" if value is None else str(value))
        elif place_holder:
            widget.setCurrentIndex(-1)

        self.update_placeholder_state(widget)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.currentIndexChanged.connect(lambda index: self.on_widget_changed(widget, callback))
        if widget.isEditable():
            widget.currentTextChanged.connect(lambda value: self.on_widget_changed(widget, callback))

    def on_widget_changed(self, widget, callback):
        self.update_placeholder_state(widget)
        callback(self.get_widget_value(widget))

    def get_value(self, field, widget):
        return self.get_widget_value(widget)

    def set_value(self, field, widget, value):
        place_holder = str(field.get("place_holder", "") or "")
        index = widget.findData(value)
        if index < 0:
            index = widget.findText(str(value))
        if index >= 0:
            widget.setCurrentIndex(index)
        elif widget.isEditable():
            widget.setCurrentText("" if value is None else str(value))
        elif place_holder:
            widget.setCurrentIndex(-1)

        self.update_placeholder_state(widget)

    def get_widget_value(self, widget):
        if widget.isEditable():
            return widget.currentText()

        if widget.currentIndex() < 0:
            return ""

        value = widget.currentData()
        if value is None:
            value = widget.currentText()
        return value

    def update_placeholder_state(self, widget):
        if widget.isEditable():
            has_value = bool(widget.currentText().strip())
        else:
            has_value = widget.currentIndex() >= 0

        widget.setProperty("placeholderActive", "false" if has_value else "true")
        widget.setProperty("hasValue", "true" if has_value else "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
