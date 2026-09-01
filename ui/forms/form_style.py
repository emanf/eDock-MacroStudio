FORM_STYLE = """
QDialog {
    background: transparent;
}
QWidget#rootCard {
    background: #0b0b0d;
    border: 1px solid #232428;
    border-radius: 12px;
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
QWidget {
    color: #f0f0f2;
    font-size: 13px;
}
QLabel {
    color: #f0f0f2;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0d0d0f;
    border: 1px solid #232428;
    border-radius: 8px;
    padding: 6px 10px;
    color: #f0f0f2;
    placeholder-text-color: #62626b;
    selection-background-color: #e6e6ea;
    selection-color: #101012;
}
QComboBox {
    color: #f0f0f2;
    padding: 6px 28px 6px 10px;
}
QComboBox::drop-down {
    width: 28px;
    border: none;
    background: transparent;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox[placeholderActive="true"] {
    color: #62626b;
}
QComboBox[placeholderActive="false"] {
    color: #f0f0f2;
}
QComboBox QLineEdit {
    background: transparent;
    border: none;
    padding: 0px;
    color: #f0f0f2;
    placeholder-text-color: #62626b;
    selection-background-color: #e6e6ea;
    selection-color: #101012;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #55555e;
}
QCheckBox {
    color: #f0f0f2;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #3a3b42;
    background: #101012;
}
QCheckBox::indicator:hover {
    border-color: #6a6a73;
}
QCheckBox::indicator:checked {
    background: #e6e6ea;
    border-color: #e6e6ea;
}
QComboBox QAbstractItemView {
    background: #131316;
    border: 1px solid #2f3036;
    border-radius: 8px;
    color: #f0f0f2;
    selection-background-color: #e6e6ea;
    selection-color: #101012;
    outline: none;
    padding: 3px;
}
QComboBox QAbstractItemView::item {
    min-height: 24px;
    padding: 4px 8px;
}
QComboBox QAbstractItemView::item:hover {
    background: #1a1b1e;
}
QComboBox QAbstractItemView::item:selected {
    background: #26272d;
    color: #ffffff;
}
QPushButton {
    background: #1a1b1e;
    border: 1px solid #26272b;
    border-radius: 7px;
    padding: 7px 14px;
    color: #f0f0f2;
    font-size: 12px;
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
QDialogButtonBox QPushButton {
    min-width: 88px;
}
ColorPickerInput QLineEdit {
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
}
ColorPickerInput QPushButton {
    min-width: 38px;
    max-width: 38px;
    padding: 6px 0px;
    border-radius: 8px;
}
QLabel#FormStatusField {
    background: #121214;
    border: 1px solid #232428;
    border-radius: 8px;
    padding: 10px 12px;
    color: #c3c3ca;
}
QLabel#FormStatusField[status="normal"] {
    background: #121214;
    border-color: #232428;
    color: #c3c3ca;
}
QLabel#FormStatusField[status="info"] {
    background: #1a1b1e;
    border-color: #2f3036;
    color: #d6d6db;
}
QLabel#FormStatusField[status="warning"] {
    background: #292114;
    border-color: #e0b35a;
    color: #ecd9ad;
}
QLabel#FormStatusField[status="danger"] {
    background: #2a1c1b;
    border-color: #e87868;
    color: #f4b8ae;
}
QLabel#FormStatusField[status="success"] {
    background: #1e1f24;
    border-color: #55555e;
    color: #d6d6db;
}
"""
