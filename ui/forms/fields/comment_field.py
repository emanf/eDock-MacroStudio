from PySide6.QtWidgets import QComboBox

from ..base_field import BaseFormField


class CommentFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QComboBox(parent)
        widget.setEditable(self.is_editable(field))
        widget.runtime_comments = getattr(parent, "runtime_comments", [])

        place_holder = str(field.get("place_holder", "") or "")
        if place_holder:
            widget.setPlaceholderText(place_holder)
            if widget.isEditable() and widget.lineEdit():
                widget.lineEdit().setPlaceholderText(place_holder)

        for option in self.get_comment_options(widget):
            widget.addItem(option, option)

        self.set_value(field, widget, value)
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
        normalized_value = "" if value is None else str(value)

        index = widget.findData(normalized_value)
        if index < 0:
            index = widget.findText(normalized_value)

        if index >= 0:
            widget.setCurrentIndex(index)
        elif widget.isEditable():
            widget.setCurrentText(normalized_value)
        elif place_holder:
            widget.setCurrentIndex(-1)

        self.update_placeholder_state(widget)

    def validate_value(self, field, widget, value):
        value = str(value or "").strip()
        if not value:
            return None

        options = self.get_comment_options(widget)
        mode = self.get_mode(field)

        if mode == "choice" and value not in options:
            return "selected comment does not exist."

        if mode == "name" and value in options:
            return "this comment already exists."

        return None

    def get_widget_value(self, widget):
        if widget.isEditable():
            return widget.currentText()

        if widget.currentIndex() < 0:
            return ""

        value = widget.currentData()
        if value is None:
            value = widget.currentText()
        return value

    def get_comment_options(self, widget):
        comments = getattr(widget, "runtime_comments", [])
        if not isinstance(comments, list):
            return []

        options = []
        for comment in comments:
            if isinstance(comment, dict):
                comment_name = str(comment.get("name", "") or "").strip()
            else:
                comment_name = str(comment or "").strip()

            if comment_name and comment_name not in options:
                options.append(comment_name)

        return options

    def get_mode(self, field):
        return "choice"

    def is_editable(self, field):
        if field.get("editable", False) is True:
            return True

        return False

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
