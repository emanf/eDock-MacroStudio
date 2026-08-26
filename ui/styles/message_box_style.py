MESSAGE_BOX_STYLE = """
QMessageBox {
    background: #101114;
}
QMessageBox QLabel {
    color: #f4f4f5;
    font-size: 13px;
}
QMessageBox QPushButton {
    background: #232633;
    border: 1px solid #343849;
    border-radius: 10px;
    padding: 9px 14px;
    color: #f4f4f5;
    min-width: 88px;
}
QMessageBox QPushButton:hover {
    background: #2d3142;
}
QMessageBox QPushButton:pressed {
    background: #1d4ed8;
}
QMessageBox QPushButton:disabled {
    background: #151720;
    border-color: #252833;
    color: rgba(244, 244, 245, 0.5);
}
"""