from PySide6.QtWidgets import QSizePolicy, QTextEdit

from ..base_field import BaseFormField


class TextAreaFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QTextEdit(parent)
        widget.setPlaceholderText(str(field.get("place_holder", "") or ""))
        widget.setPlainText("" if value is None else str(value))
        widget.setAcceptRichText(False)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        line_count = self.get_line_count(field)
        height = self.calculate_height(widget, line_count)
        widget.setMinimumHeight(height)

        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.textChanged.connect(lambda: callback(widget.toPlainText()))

    def get_value(self, field, widget):
        return widget.toPlainText()

    def set_value(self, field, widget, value):
        widget.setPlainText("" if value is None else str(value))

    def get_line_count(self, field):
        value = field.get("line_count", field.get("lines", field.get("rows", 2)))
        try:
            value = int(value)
        except Exception:
            value = 2

        if value < 1:
            value = 1

        return value

    def calculate_height(self, widget, line_count):
        font_height = widget.fontMetrics().lineSpacing()
        margins = widget.contentsMargins()
        frame = widget.frameWidth() * 2
        padding = 18
        return font_height * line_count + margins.top() + margins.bottom() + frame + padding
