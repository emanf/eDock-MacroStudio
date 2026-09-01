MAIN_STYLE = """
QMainWindow, QDialog {
    background: transparent;
}

QWidget {
    color: #f0f0f2;
    font-size: 13px;
}

QWidget#rootCard {
    background: #0b0b0d;
    border: 1px solid #232428;
    border-radius: 12px;
}

QDialog {
    background: #0b0b0d;
}

QToolTip {
    background: #1a1b1e;
    color: #d6d6db;
    border: 1px solid #2f3036;
    border-radius: 6px;
    padding: 6px 9px;
    font-size: 12px;
}

QFrame#titleBar {
    background: transparent;
    border-bottom: 1px solid #1a1b1e;
}

QLabel#logoMark {
    background: #1e1f24;
    border-radius: 6px;
    color: #f0f0f2;
    font-size: 12px;
    font-weight: 800;
}

QLabel#appTitle {
    font-size: 13px;
    font-weight: 700;
    color: #f0f0f2;
}

QLineEdit#pathChip {
    background: #1a1b1e;
    border: 1px solid #26272b;
    border-radius: 6px;
    padding: 1px 8px;
    color: #9a9aa2;
    font-size: 10px;
}

QLineEdit#pathChip:hover {
    border-color: #2f3036;
}

QLineEdit#pathChip:focus {
    border-color: #55555e;
    color: #f0f0f2;
}

QPushButton#titleButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 0;
}

QPushButton#titleButton:hover {
    background: #1e1f24;
}

QPushButton#titleCloseButton:hover {
    background: #e5484d;
}

QPushButton#titleCloseButton:pressed {
    background: #c73740;
}

QLabel#Title {
    font-size: 15px;
    font-weight: 700;
    color: #f0f0f2;
}

QLabel#Subtitle {
    color: #9a9aa2;
    font-size: 11px;
}

QLabel#Tiny {
    color: #62626b;
    font-size: 11px;
}

QFrame#Panel {
    background: #121214;
    border: 1px solid #232428;
    border-radius: 10px;
}

QSplitter::handle {
    background: transparent;
}

QSplitter::handle:hover {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 1px;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0d0d0f;
    border: 1px solid #232428;
    border-radius: 8px;
    padding: 6px 10px;
    color: #f0f0f2;
    placeholder-text-color: #62626b;
    selection-background-color: #e6e6ea;
    selection-color: #101012;
}

QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    border-color: #2f3036;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #55555e;
}

QComboBox {
    padding-right: 34px;
    color: #62626b;
}

QComboBox[hasValue="true"] {
    color: #f0f0f2;
}

QComboBox:editable {
    color: #f0f0f2;
}

QComboBox QLineEdit {
    background: transparent;
    border: none;
    padding: 0px;
    color: #f0f0f2;
    selection-background-color: #e6e6ea;
    selection-color: #101012;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 24px;
    border: none;
    background: transparent;
}

QComboBox::down-arrow {
    image: url(apps/emanf.macro-studio/assets/chevron_down.svg);
    width: 12px;
    height: 12px;
    border: none;
    background: transparent;
}

QComboBox QAbstractItemView {
    background: #131316;
    border: 1px solid #2f3036;
    border-radius: 8px;
    padding: 4px;
    color: #f0f0f2;
    outline: none;
    selection-background-color: #e6e6ea;
    selection-color: #101012;
}

QSpinBox, QDoubleSpinBox {
    min-width: 82px;
    padding-right: 26px;
}

QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    height: 20px;
    border: none;
    border-top-right-radius: 8px;
    background: transparent;
}

QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    height: 20px;
    border: none;
    border-bottom-right-radius: 8px;
    background: transparent;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #1e1f24;
}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image: url(apps/emanf.macro-studio/assets/chevron_up.svg);
    width: 10px;
    height: 10px;
}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image: url(apps/emanf.macro-studio/assets/chevron_down.svg);
    width: 10px;
    height: 10px;
}

QPushButton {
    background: #1a1b1e;
    border: 1px solid #26272b;
    border-radius: 7px;
    padding: 5px 12px;
    color: #f0f0f2;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background: #222327;
    border-color: #2f3036;
}

QPushButton:pressed {
    background: #141518;
}

QPushButton:disabled {
    background: #131316;
    border-color: #1f2024;
    color: #55555e;
}

QPushButton#Primary {
    background: #f0f0f2;
    border: 1px solid #f0f0f2;
    color: #101012;
    font-weight: 700;
    padding: 5px 16px;
}

QPushButton#Primary:hover {
    background: #ffffff;
    border-color: #ffffff;
}

QPushButton#Primary:pressed {
    background: #d6d6db;
    border-color: #d6d6db;
}

QPushButton#Primary:disabled {
    background: #1c1d21;
    border-color: #1c1d21;
    color: #55555e;
}

QPushButton#Success {
    background: #f0f0f2;
    border: 1px solid #f0f0f2;
    color: #101012;
    font-weight: 700;
    padding: 5px 16px;
}

QPushButton#Success:hover {
    background: #ffffff;
    border-color: #ffffff;
}

QPushButton#Success:pressed {
    background: #d6d6db;
    border-color: #d6d6db;
}

QPushButton#Success:disabled {
    background: #1c1d21;
    border-color: #1c1d21;
    color: #55555e;
}

QPushButton#Accent {
    background: transparent;
    border: 1px solid #26272b;
    color: #9a9aa2;
}

QPushButton#Accent:hover {
    background: #1a1b1e;
    border-color: #2f3036;
    color: #f0f0f2;
}

QPushButton#Accent:pressed {
    background: #141518;
}

QPushButton#Accent:disabled {
    background: transparent;
    border-color: #1f2024;
    color: #55555e;
}

QPushButton#Warning {
    background: #e0b35a;
    border: 1px solid #e0b35a;
    color: #241a06;
    font-weight: 700;
}

QPushButton#Warning:hover {
    background: #eac274;
    border-color: #eac274;
}

QPushButton#Warning:pressed {
    background: #cf9f4c;
    border-color: #cf9f4c;
}

QPushButton#Warning:disabled {
    background: #1c1d21;
    border-color: #1c1d21;
    color: #55555e;
}

QPushButton#Danger {
    background: #e87868;
    border: 1px solid #e87868;
    color: #2a120d;
    font-weight: 700;
}

QPushButton#Danger:hover {
    background: #f09285;
    border-color: #f09285;
}

QPushButton#Danger:pressed {
    background: #d6604f;
    border-color: #d6604f;
}

QPushButton#Danger:disabled {
    background: #1c1d21;
    border-color: #1c1d21;
    color: #55555e;
}

QTableWidget {
    background: #121214;
    border: 1px solid #232428;
    border-radius: 8px;
    gridline-color: #232428;
    outline: none;
}

QHeaderView::section {
    background: #161618;
    color: #9a9aa2;
    border: none;
    border-bottom: 1px solid #232428;
    padding: 8px;
}

QTableWidget::item {
    padding: 6px;
    border: none;
}

QTableWidget::item:selected {
    background: #26272d;
    color: #ffffff;
}

QMenu {
    background: #131316;
    color: #f0f0f2;
    border: 1px solid #2f3036;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    padding: 8px 34px 8px 12px;
    border-radius: 5px;
}

QMenu::item:selected {
    background: #26272d;
    color: #ffffff;
}

QMenu::item:disabled {
    color: rgba(240, 240, 242, 0.38);
}

QMenu::separator {
    height: 1px;
    background: #232428;
    margin: 4px 8px;
}

QScrollBar:vertical {
    background: transparent;
    width: 9px;
    margin: 3px 2px;
}

QScrollBar::handle:vertical {
    background: #26272c;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #34353c;
}

QScrollBar::handle:vertical:pressed {
    background: #43444c;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: transparent;
    border: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 9px;
    margin: 2px 3px;
}

QScrollBar::handle:horizontal {
    background: #26272c;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #34353c;
}

QScrollBar::handle:horizontal:pressed {
    background: #43444c;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: transparent;
    border: none;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}
"""

COLORS = {
    "bg": "#0a0a0c",
    "surface": "#121214",
    "surface_hover": "#1a1b1e",
    "input_bg": "#0d0d0f",
    "border": "#232428",
    "border_hover": "#2f3036",
    "text": "#f0f0f2",
    "text_med": "#c3c3ca",
    "text_dim": "#9a9aa2",
    "text_faint": "#62626b",
    "accent": "#f0f0f2",
    "accent_hover": "#ffffff",
    "accent_press": "#d6d6db",
    "accent_ink": "#101012",
    "accent_dim": "#55555e",
    "selection_bg": "#26272d",
    "selection_text": "#ffffff",
    "success": "#d6d6db",
    "warning": "#e0b35a",
    "error": "#e87868",
    "danger": "#e87868",
    "scroll": "#26272c",
    "scroll_hover": "#34353c",
    "scroll_press": "#43444c",
}
