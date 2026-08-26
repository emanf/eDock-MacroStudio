from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class NumberListItem(QWidget):
    def __init__(self, number, title, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.running = False
        self.disabled_state = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.number_label = QLabel(str(number))
        self.number_label.setFixedSize(24, 24)
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.setFont(QFont("Arial", 11))

        self.title_label = QLabel(str(title or "Untitled"))
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        layout.addWidget(self.number_label, 0, Qt.AlignVCenter)
        layout.addWidget(self.title_label, 1, Qt.AlignVCenter)

        self.apply_style()

    def set_running(self, enabled):
        self.running = bool(enabled)
        self.apply_style()

    def set_disabled_state(self, enabled):
        self.disabled_state = bool(enabled)
        self.apply_style()

    def apply_style(self):
        if self.running:
            self.number_label.setStyleSheet("""
                color: #ffffff;
                background: #dc2626;
                font-weight: 700;
                margin: 0;
                padding: 0;
                border-radius: 4px;
            """)
            self.title_label.setStyleSheet("""
                font-weight: 700;
                color: #ffffff;
                background: transparent;
                border: none;
            """)
            return

        if self.disabled_state:
            self.number_label.setStyleSheet("""
                color: rgba(244, 244, 245, 0.52);
                background: rgba(51, 51, 51, 0.42);
                font-weight: 600;
                margin: 0;
                padding: 0;
                border-radius: 4px;
            """)
            self.title_label.setStyleSheet("""
                font-weight: 500;
                color: rgba(244, 244, 245, 0.52);
                background: transparent;
                border: none;
            """)
            return

        self.number_label.setStyleSheet("""
            color: #f4f4f5;
            background: #AA333333;
            font-weight: 600;
            margin: 0;
            padding: 0;
            border-radius: 4px;
        """)
        self.title_label.setStyleSheet("""
            font-weight: 500;
            color: #f4f4f5;
            background: transparent;
            border: none;
        """)
