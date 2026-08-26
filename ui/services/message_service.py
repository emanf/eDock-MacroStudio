from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from ...ui.styles.message_box_style import MESSAGE_BOX_STYLE


class MessageService:
    def __init__(self, parent):
        self.parent = parent

    def show_message(self, icon, title, message, on_closed=None):
        box = QMessageBox(self.parent)
        box.setWindowModality(Qt.WindowModality.WindowModal)
        box.setIcon(icon)
        box.setWindowTitle(str(title or "Message"))
        box.setText(str(message or ""))
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.setStyleSheet(MESSAGE_BOX_STYLE)
        box.exec()

        if callable(on_closed):
            on_closed()

    def show_information(self, title, message, on_closed=None):
        self.show_message(QMessageBox.Icon.Information, title, message, on_closed=on_closed)

    def show_warning(self, title, message):
        self.show_message(QMessageBox.Icon.Warning, title, message)

    def show_critical(self, title, message):
        self.show_message(QMessageBox.Icon.Critical, title, message)

    def confirm(self, title, text, informative_text, accept_text, cancel_text="Cancel"):
        box = QMessageBox(self.parent)
        box.setWindowModality(Qt.WindowModality.WindowModal)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(title)
        box.setText(text)
        box.setInformativeText(informative_text)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.button(QMessageBox.StandardButton.Yes).setText(accept_text)
        box.button(QMessageBox.StandardButton.No).setText(cancel_text)
        box.setStyleSheet(MESSAGE_BOX_STYLE)

        return box.exec() == QMessageBox.StandardButton.Yes

    def ask_open_project_mode(self):
        box = QMessageBox(self.parent)
        box.setWindowModality(Qt.WindowModality.WindowModal)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Open Project")
        box.setText("How do you want to open this project?")
        replace_button = box.addButton("Load Project", QMessageBox.ButtonRole.AcceptRole)
        merge_button = box.addButton("Merge", QMessageBox.ButtonRole.ActionRole)
        box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(replace_button)
        box.setStyleSheet(MESSAGE_BOX_STYLE)
        box.exec()

        clicked = box.clickedButton()
        if clicked == replace_button:
            return "replace"
        if clicked == merge_button:
            return "merge"
        return None
