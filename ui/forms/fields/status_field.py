from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy

from ..base_field import BaseFormField


class StatusFieldHandler(BaseFormField):
    VALID_STATUSES = {
        "normal",
        "info",
        "warning",
        "danger",
        "success",
    }

    def create_widget(self, field, value, parent=None):
        widget = QLabel(parent)
        widget.setObjectName("FormStatusField")
        widget.setWordWrap(True)
        widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.set_status(widget, field.get("status", "normal"))
        self.set_value(field, widget, value)
        return widget

    def get_value(self, field, widget):
        return widget.text()

    def set_value(self, field, widget, value):
        status = field.get("status", "normal")
        text = value

        if isinstance(value, dict):
            status = value.get("status", status)
            text = value.get("value", value.get("text", ""))

        self.set_status(widget, status)
        widget.setText("" if text is None else str(text))
        widget.updateGeometry()

    def set_status(self, widget, status):
        normalized_status = str(status or "normal").strip().lower()

        if normalized_status not in self.VALID_STATUSES:
            normalized_status = "normal"

        widget.setProperty("status", normalized_status)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
