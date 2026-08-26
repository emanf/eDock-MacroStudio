class BaseFormField:
    def __init__(self, context=None):
        self.context = context

    def getMainWindow(self):
        if self.context is None:
            return None

        getter = getattr(self.context, "getMainWindow", None)
        if callable(getter):
            return getter()

        return None

    def create_widget(self, field, value, parent=None):
        raise NotImplementedError()

    def bind_changing(self, field, widget):
        callback = field.get("on_changing", None)
        if not callable(callback):
            return
        self.connect_change_signal(widget, callback)

    def connect_change_signal(self, widget, callback):
        pass

    def get_value(self, field, widget):
        raise NotImplementedError()

    def set_value(self, field, widget, value):
        raise NotImplementedError()

    def validate_value(self, field, widget, value):
        return None
