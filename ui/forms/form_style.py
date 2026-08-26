FORM_STYLE = """
QDialog {
    background: #101114;
}
QWidget {
    color: #f4f4f5;
    font-size: 13px;
}
QLabel {
    color: #f4f4f5;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
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
    color: #f4f4f5;
    padding: 8px 32px 8px 8px;
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
    color: #4b5563;
}
QComboBox[placeholderActive="false"] {
    color: #f4f4f5;
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
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #3b82f6;
}
QCheckBox {
    color: #f4f4f5;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #343849;
    background: #0f1117;
}
QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #3b82f6;
}
QComboBox QAbstractItemView {
    background: #17191f;
    border: 1px solid #343849;
    color: #f4f4f5;
    selection-background-color: #2563eb;
    selection-color: white;
    outline: none;
    padding: 3px;
}
QComboBox QAbstractItemView::item {
    min-height: 24px;
    padding: 4px 8px;
}
QComboBox QAbstractItemView::item:hover {
    background: #2d3142;
}
QComboBox QAbstractItemView::item:selected {
    background: #2563eb;
    color: white;
}
QPushButton {
    background: #232633;
    border: 1px solid #343849;
    border-radius: 10px;
    padding: 9px 14px;
    color: #f4f4f5;
}
QPushButton:hover {
    background: #2d3142;
}
QPushButton:pressed {
    background: #1d4ed8;
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
    padding: 8px 0px;
    border-radius: 8px;
}
QLabel#FormStatusField {
    background: #17191f;
    border: 1px solid #343849;
    border-radius: 8px;
    padding: 10px 12px;
    color: #d4d4d8;
}
QLabel#FormStatusField[status="normal"] {
    background: #17191f;
    border-color: #343849;
    color: #d4d4d8;
}
QLabel#FormStatusField[status="info"] {
    background: #10233f;
    border-color: #2563eb;
    color: #bfdbfe;
}
QLabel#FormStatusField[status="warning"] {
    background: #30240d;
    border-color: #d97706;
    color: #fde68a;
}
QLabel#FormStatusField[status="danger"] {
    background: #321418;
    border-color: #dc2626;
    color: #fecaca;
}
QLabel#FormStatusField[status="success"] {
    background: #10291d;
    border-color: #16a34a;
    color: #bbf7d0;
}
"""
