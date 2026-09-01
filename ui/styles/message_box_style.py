MESSAGE_BOX_STYLE = """
QMessageBox {
    background: #0b0b0d;
}
QMessageBox QLabel {
    color: #f0f0f2;
    font-size: 13px;
}
QMessageBox QPushButton {
    background: #1a1b1e;
    border: 1px solid #26272b;
    border-radius: 7px;
    padding: 7px 14px;
    color: #f0f0f2;
    min-width: 88px;
}
QMessageBox QPushButton:hover {
    background: #222327;
    border-color: #2f3036;
}
QMessageBox QPushButton:pressed {
    background: #141518;
}
QMessageBox QPushButton:disabled {
    background: #131316;
    border-color: #1f2024;
    color: #55555e;
}
"""