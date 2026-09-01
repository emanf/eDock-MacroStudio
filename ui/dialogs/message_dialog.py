from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..styles.main_style import MAIN_STYLE
from ..widgets import app_icons
from ..widgets.title_bar import TitleBar

ICON_COLORS = {
    "info": "#9a9aa2",
    "warning": "#e0b35a",
    "error": "#e87868",
}


class MessageDialog(QDialog):
    def __init__(
        self,
        parent,
        title,
        text,
        informative_text="",
        buttons=None,
        icon_name="info",
    ):
        super().__init__(parent)
        self.result_key = None
        buttons = list(buttons or [("OK", "ok", True)])

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(440)
        self.setStyleSheet(MAIN_STYLE)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        card = QWidget()
        card.setObjectName("rootCard")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        card.setLayout(card_layout)
        outer.addWidget(card)

        card_layout.addWidget(
            TitleBar(
                self,
                title=str(title or "Message"),
                window_buttons=False,
            )
        )

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(18, 14, 18, 16)
        content_layout.setSpacing(14)
        content.setLayout(content_layout)
        card_layout.addWidget(content, 1)

        body = QHBoxLayout()
        body.setSpacing(12)

        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(
                app_icons.paint_glyph(
                    app_icons.glyph(icon_name),
                    22,
                    ICON_COLORS.get(icon_name, "#9a9aa2"),
                )
            )
            icon_label.setFixedSize(22, 22)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("background: transparent; border: none;")
            body.addWidget(icon_label, 0, Qt.AlignTop)

        text_box = QVBoxLayout()
        text_box.setSpacing(6)

        text_label = QLabel(str(text or ""))
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_label.setStyleSheet("background: transparent; border: none;")
        text_box.addWidget(text_label)

        informative = str(informative_text or "").strip()
        if informative:
            info_label = QLabel(informative)
            info_label.setWordWrap(True)
            info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info_label.setStyleSheet(
                "color: #9a9aa2; background: transparent; border: none;"
            )
            text_box.addWidget(info_label)

        text_box.addStretch()
        body.addLayout(text_box, 1)
        content_layout.addLayout(body, 1)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)
        buttons_row.addStretch()

        for label_text, key, primary in buttons:
            button = QPushButton(str(label_text))
            if primary:
                button.setObjectName("Primary")
            button.clicked.connect(
                lambda checked=False, key_value=key: self._accept_key(key_value)
            )
            buttons_row.addWidget(button)

        content_layout.addLayout(buttons_row)

    def _accept_key(self, key):
        self.result_key = key
        self.accept()
