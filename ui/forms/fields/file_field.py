from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget
from PySide6.QtGui import QFont

from core.rendering.material_icons import MaterialIcons

from ..base_field import BaseFormField


class FilePickerInput(QWidget):
    def __init__(self, field, value=None, parent=None):
        super().__init__(parent)

        self.field = field
        self.material_font = MaterialIcons.ensure_font()

        self.input = QLineEdit(self)
        self.input.setPlaceholderText(str(field.get("place_holder", "") or ""))
        self.input.setText("" if value is None else str(value))

        self.button = QPushButton("more_horiz", self)
        self.button.setFont(QFont(self.material_font))
        self.button.clicked.connect(self.pick_file)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.input, 1)
        layout.addWidget(self.button)

    def pick_file(self):
        caption = str(self.field.get("caption", "Select File") or "Select File")
        start_dir = str(self.field.get("start_dir", "") or "")
        file_filter = str(self.field.get("file_filter", "All Files (*)") or "All Files (*)")

        path, _ = QFileDialog.getOpenFileName(self, caption, start_dir, file_filter)
        if path:
            self.input.setText(path)

    def text(self):
        return self.input.text()

    def setText(self, value):
        self.input.setText("" if value is None else str(value))


class FileFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = FilePickerInput(field, value, parent)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.input.textChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.text()

    def set_value(self, field, widget, value):
        widget.setText(value)
