from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton

from . import app_icons


class TitleBar(QFrame):
    project_title_changed = Signal(str)
    def __init__(
        self,
        window,
        title="Macro Studio",
        window_buttons=True,
    ):
        super().__init__(window)
        self.setObjectName("titleBar")
        self.window_ref = window
        self._drag_offset = None
        self.setFixedHeight(48)

        layout = QHBoxLayout()
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(10)
        self.setLayout(layout)

        logo = QLabel("M")
        logo.setObjectName("logoMark")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedSize(24, 24)

        title_label = QLabel(title)
        title_label.setObjectName("appTitle")

        layout.addWidget(logo)
        layout.addWidget(title_label)
        layout.addStretch()
        self._action_index = layout.count()
        self.project_chip = None

        self.btn_minimize = None
        self.btn_maximize = None

        if window_buttons:
            self.btn_minimize = self._window_button(
                "remove", self._on_minimize
            )
            self.btn_maximize = self._window_button(
                "fullscreen", self._on_toggle_maximize
            )
            layout.addWidget(self.btn_minimize)
            layout.addWidget(self.btn_maximize)

        self.btn_close = self._window_button(
            "close", self._on_close
        )
        self.btn_close.setObjectName("titleCloseButton")
        self.btn_close.installEventFilter(self)
        layout.addWidget(self.btn_close)

    def eventFilter(self, obj, event):
        if obj is self.btn_close:
            if event.type() == QEvent.Enter:
                self.btn_close.setIcon(
                    app_icons.icon("close", 14, "#ffffff")
                )
            elif event.type() == QEvent.Leave:
                self.btn_close.setIcon(
                    app_icons.icon("close", 14, "#9a9aa2")
                )

        return super().eventFilter(obj, event)

    def _window_button(self, glyph_name, handler):
        button = QPushButton()
        button.setObjectName("titleButton")
        button.setIcon(
            app_icons.icon(glyph_name, 14, "#9a9aa2")
        )
        button.setIconSize(QSize(14, 14))
        button.setFixedSize(34, 26)
        button.clicked.connect(handler)
        return button

    def add_action_button(self, glyph_name, tooltip, handler):
        button = self._window_button(glyph_name, handler)
        button.setToolTip(tooltip)
        self.layout().insertWidget(self._action_index, button)
        self._action_index += 1
        return button

    def set_project_title(self, title):
        if self.project_chip is None:
            self.project_chip = QLineEdit()
            self.project_chip.setObjectName("pathChip")
            self.project_chip.setFixedHeight(20)
            self.project_chip.setMinimumWidth(90)
            self.project_chip.setMaximumWidth(200)
            self.project_chip.setAlignment(Qt.AlignCenter)
            self.project_chip.setToolTip("Project title")
            self.project_chip.editingFinished.connect(
                self._on_project_title_edited
            )
            self.layout().insertWidget(
                self._action_index, self.project_chip
            )
            self._action_index += 1

        text = str(title or "")
        self._project_title = text.strip()

        if not self.project_chip.hasFocus():
            self.project_chip.setText(text)

        self.project_chip.setVisible(True)

    def _on_project_title_edited(self):
        text = self.project_chip.text().strip()

        if not text:
            self.project_chip.setText(self._project_title)
            return

        self._project_title = text
        self.project_title_changed.emit(text)

    def _on_minimize(self):
        self.window_ref.showMinimized()

    def _on_toggle_maximize(self):
        if self.btn_maximize is None:
            return

        window = self.window_ref

        if window.isMaximized():
            window.showNormal()
            self.btn_maximize.setIcon(
                app_icons.icon("fullscreen", 14, "#9a9aa2")
            )
        else:
            window.showMaximized()
            self.btn_maximize.setIcon(
                app_icons.icon("fullscreen_exit", 14, "#9a9aa2")
            )

    def _on_close(self):
        self.window_ref.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.window_ref.isMaximized():
            self._drag_offset = (
                event.globalPosition().toPoint()
                - self.window_ref.frameGeometry().topLeft()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            self.window_ref.move(
                event.globalPosition().toPoint() - self._drag_offset
            )
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.btn_maximize is not None:
            self._on_toggle_maximize()
            event.accept()
            return

        super().mouseDoubleClickEvent(event)
