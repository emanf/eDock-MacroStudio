from ..dialogs.message_dialog import MessageDialog

_ICON_NAMES = {
    "Information": "info",
    "Warning": "warning",
    "Critical": "error",
}


class MessageService:
    def __init__(self, parent):
        self.parent = parent

    def show_message(self, icon, title, message, on_closed=None):
        icon_name = _ICON_NAMES.get(
            str(getattr(icon, "name", icon) or "info"), "info"
        )
        dialog = MessageDialog(
            self.parent,
            str(title or "Message"),
            str(message or ""),
            buttons=[("OK", "ok", True)],
            icon_name=icon_name,
        )
        dialog.exec()

        if callable(on_closed):
            on_closed()

    def show_information(self, title, message, on_closed=None):
        self.show_message("Information", title, message, on_closed=on_closed)

    def show_warning(self, title, message):
        self.show_message("Warning", title, message)

    def show_critical(self, title, message):
        self.show_message("Critical", title, message)

    def confirm(self, title, text, informative_text, accept_text, cancel_text="Cancel"):
        dialog = MessageDialog(
            self.parent,
            str(title or ""),
            str(text or ""),
            informative_text=informative_text,
            buttons=[
                (str(accept_text or "Yes"), "yes", True),
                (str(cancel_text or "No"), "no", False),
            ],
            icon_name="warning",
        )
        dialog.exec()

        return dialog.result_key == "yes"

    def ask_open_project_mode(self):
        dialog = MessageDialog(
            self.parent,
            "Open Project",
            "How do you want to open this project?",
            buttons=[
                ("Load Project", "replace", True),
                ("Merge", "merge", False),
                ("Cancel", "cancel", False),
            ],
            icon_name="info",
        )
        dialog.exec()

        if dialog.result_key in ("replace", "merge"):
            return dialog.result_key

        return None

