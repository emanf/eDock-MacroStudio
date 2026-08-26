MAIN_STYLE = """
QMainWindow {
    background: #101114;
}
QWidget {
    color: #f4f4f5;
    font-size: 13px;
}
QToolTip {
    background: #17191f;
    color: #f4f4f5;
    border: 1px solid #343849;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 12px;
}
QFrame#Panel {
    background: #17191f;
    border: 1px solid #252833;
    border-radius: 16px;
}
QSplitter::handle {
    background: transparent;
    border: none;
}
QSplitter::handle:horizontal {
    width: 14px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.42 transparent, stop:0.43 #252833, stop:0.57 #252833, stop:0.58 transparent, stop:1 transparent);
}
QSplitter::handle:vertical {
    height: 14px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 transparent, stop:0.42 transparent, stop:0.43 #252833, stop:0.57 #252833, stop:0.58 transparent, stop:1 transparent);
}
QSplitter::handle:horizontal:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.42 transparent, stop:0.43 #343849, stop:0.57 #343849, stop:0.58 transparent, stop:1 transparent);
}
QSplitter::handle:vertical:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 transparent, stop:0.42 transparent, stop:0.43 #343849, stop:0.57 #343849, stop:0.58 transparent, stop:1 transparent);
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0f1117;
    border: 1px solid #343849;
    border-radius: 8px;
    padding: 8px;
    color: #f4f4f5;
    placeholder-text-color: #4b5563;
    selection-background-color: #2563eb;
    selection-color: white;
}
QComboBox {
    padding-right: 34px;
    color: #4b5563;
    placeholder-text-color: #4b5563;
}
QComboBox[hasValue="true"] {
    color: #f4f4f5;
}
QComboBox:editable {
    color: #f4f4f5;
    placeholder-text-color: #4b5563;
}
QComboBox QLineEdit {
    background: transparent;
    border: none;
    padding: 0px;
    color: #f4f4f5;
    placeholder-text-color: #4b5563;
    selection-background-color: #2563eb;
    selection-color: white;
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
    background: #17191f;
    border: 1px solid #343849;
    color: #f4f4f5;
    selection-background-color: #2563eb;
    selection-color: white;
    outline: none;
}
QSpinBox, QDoubleSpinBox {
    min-width: 82px;
    padding-right: 30px;
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
QTextEdit, QPlainTextEdit {
    min-height: 72px;
}
QLabel#Title {
    font-size: 22px;
    font-weight: 700;
}
QLabel#Subtitle {
    color: #a1a1aa;
}
QLabel#Tiny {
    color: #a1a1aa;
    font-size: 12px;
}
QListWidget {
    background: #17191f;
    border: 1px solid #252833;
    border-radius: 14px;
    padding: 8px;
    outline: none;
}
QListWidget::item {
    padding: 10px;
    border-radius: 10px;
}
QListWidget::item:selected {
    background: #3b82f6;
    color: white;
}
QPushButton {
    background: #232633;
    border: 1px solid #343849;
    border-radius: 10px;
    padding: 9px 14px;
}
QPushButton:hover {
    background: #2d3142;
}
QPushButton:pressed {
    background: #1d4ed8;
}
QPushButton:disabled {
    background: #151720;
    border-color: #252833;
    color: rgba(244, 244, 245, 0.5);
}
QPushButton:disabled:hover {
    background: #151720;
    border-color: #252833;
}
QPushButton:disabled:pressed {
    background: #151720;
    border-color: #252833;
}
QPushButton#Primary {
    background: #2563eb;
    border-color: #2563eb;
    color: white;
}
QPushButton#Primary:disabled {
    background: #15336f;
    border-color: #15336f;
    color: rgba(255, 255, 255, 0.5);
}
QPushButton#Success {
    background: #15803d;
    border-color: #16a34a;
    color: white;
}
QPushButton#Success:disabled {
    background: #0b3f20;
    border-color: #0b4f25;
    color: rgba(255, 255, 255, 0.5);
}
QPushButton#Accent {
    background: #0f766e;
    border-color: #0d9488;
    color: white;
}
QPushButton#Accent:disabled {
    background: #073d38;
    border-color: #084c45;
    color: rgba(255, 255, 255, 0.5);
}
QPushButton#Warning {
    background: #a16207;
    border-color: #ca8a04;
    color: white;
}
QPushButton#Warning:disabled {
    background: #503103;
    border-color: #654502;
    color: rgba(255, 255, 255, 0.5);
}
QPushButton#Danger {
    background: #7f1d1d;
    border-color: #991b1b;
    color: white;
}
QPushButton#Danger:disabled {
    background: #3f0e0e;
    border-color: #4c0d0d;
    color: rgba(255, 255, 255, 0.5);
}
QTableWidget {
    background: #17191f;
    border: 1px solid #252833;
    border-radius: 14px;
    gridline-color: #252833;
    outline: none;
}
QHeaderView::section {
    background: #11131a;
    color: #a1a1aa;
    border: none;
    border-bottom: 1px solid #252833;
    padding: 10px 8px;
}
QTableWidget::item {
    padding: 8px;
    border: none;
}
QTableWidget::item:selected {
    background: #3b82f6;
    color: white;
}
QMenu {
    background: #17191f;
    border: 1px solid #343849;
    border-radius: 10px;
    padding: 6px;
    color: #f4f4f5;
}
QMenu::item {
    background: transparent;
    color: #f4f4f5;
    padding: 8px 34px 8px 12px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: #2563eb;
    color: white;
}
QMenu::item:disabled {
    color: rgba(244, 244, 245, 0.38);
}
QMenu::separator {
    height: 1px;
    background: #252833;
    margin: 6px 8px;
}
QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 6px 2px 6px 2px;
}
QScrollBar::handle:vertical {
    background: #343849;
    min-height: 28px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #4b5565;
}
QScrollBar::handle:vertical:pressed {
    background: #5b6474;
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
    height: 12px;
    margin: 2px 6px 2px 6px;
}
QScrollBar::handle:horizontal {
    background: #343849;
    min-width: 28px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background: #4b5565;
}
QScrollBar::handle:horizontal:pressed {
    background: #5b6474;
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
