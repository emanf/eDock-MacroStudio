from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HeaderBar(QWidget):
    title_changed = Signal(str)
    new_clicked = Signal()
    open_clicked = Signal()
    save_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.build_ui()

    def build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title_box = QVBoxLayout()

        title = QLabel("Macro Studio")
        title.setObjectName("Title")

        subtitle = QLabel("Record, build, run, loop, and control Python-powered macro workflows.")
        subtitle.setObjectName("Subtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        layout.addLayout(title_box)
        layout.addStretch()

        self.project_input = QLineEdit()
        self.project_input.setPlaceholderText("Project title")
        self.project_input.setMinimumWidth(260)
        self.project_input.textChanged.connect(self.title_changed.emit)

        new_button = QPushButton("New Project")
        open_button = QPushButton("Open")
        save_button = QPushButton("Save")
        save_button.setObjectName("Primary")

        new_button.clicked.connect(lambda: self.new_clicked.emit())
        open_button.clicked.connect(lambda: self.open_clicked.emit())
        save_button.clicked.connect(lambda: self.save_clicked.emit())

        layout.addWidget(self.project_input)
        layout.addWidget(new_button)
        layout.addWidget(open_button)
        layout.addWidget(save_button)

    def set_project_title(self, title):
        self.project_input.blockSignals(True)
        self.project_input.setText(str(title or ""))
        self.project_input.blockSignals(False)
