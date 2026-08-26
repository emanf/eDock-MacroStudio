from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from core.rendering.material_icons import MaterialIcons


class IconListItem(QWidget):
    def __init__(self, icon_key, title, font_family, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.disabled_state = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFont(QFont(font_family))

        icon_name = str(icon_key or "extension")
        self.icon_label.setText(MaterialIcons.get(icon_name, "extension"))

        self.title_label = QLabel(str(title or "Untitled"))
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        layout.addWidget(self.icon_label, 0, Qt.AlignCenter)
        layout.addWidget(self.title_label, 1, Qt.AlignVCenter)

        self.apply_style()

    def set_disabled_state(self, disabled):
        self.disabled_state = bool(disabled)
        self.apply_style()

    def apply_style(self):
        if self.disabled_state:
            icon_color = "rgba(244, 244, 245, 0.38)"
            title_color = "rgba(244, 244, 245, 0.38)"
        else:
            icon_color = "#f4f4f5"
            title_color = "#f4f4f5"

        self.icon_label.setStyleSheet(f"""
            color: {icon_color};
            background: transparent;
            font-size: 14pt;
            margin: 0;
            padding: 0;
        """)

        self.title_label.setStyleSheet(
            f"font-weight: 500; color: {title_color}; "
            "background: transparent; border: none;"
        )
