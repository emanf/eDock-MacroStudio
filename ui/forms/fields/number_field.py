from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QWidget,
)

from ..base_field import BaseFormField


class IntegerFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QSpinBox(parent)
        widget.setMinimum(int(field.get("min_value", -2147483648)))
        widget.setMaximum(int(field.get("max_value", 2147483647)))
        try:
            widget.setValue(int(value))
        except Exception:
            widget.setValue(int(field.get("default_value", 0) or 0))
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.valueChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.value()

    def set_value(self, field, widget, value):
        try:
            widget.setValue(int(value))
        except Exception:
            widget.setValue(int(field.get("default_value", 0) or 0))


class FloatFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QDoubleSpinBox(parent)
        widget.setMinimum(float(field.get("min_value", -999999999)))
        widget.setMaximum(float(field.get("max_value", 999999999)))
        widget.setDecimals(int(field.get("decimals", 2) or 2))
        try:
            widget.setValue(float(value))
        except Exception:
            widget.setValue(float(field.get("default_value", 0) or 0))
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.valueChanged.connect(lambda value: callback(value))

    def get_value(self, field, widget):
        return widget.value()

    def set_value(self, field, widget, value):
        try:
            widget.setValue(float(value))
        except Exception:
            widget.setValue(float(field.get("default_value", 0) or 0))


class MinMaxFieldHandler(BaseFormField):
    def create_widget(self, field, value, parent=None):
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        widget.number_type = str(field.get("number_type", "integer") or "integer").strip().lower()

        min_label = QLabel(str(field.get("min_title", "Min") or "Min"), widget)
        max_label = QLabel(str(field.get("max_title", "Max") or "Max"), widget)

        if widget.number_type in ("float", "double"):
            widget.min_input = QDoubleSpinBox(widget)
            widget.max_input = QDoubleSpinBox(widget)
            decimals = int(field.get("decimals", 2) or 2)
            widget.min_input.setDecimals(decimals)
            widget.max_input.setDecimals(decimals)
            minimum = float(field.get("min_value", -999999999))
            maximum = float(field.get("max_value", 999999999))
        else:
            widget.min_input = QSpinBox(widget)
            widget.max_input = QSpinBox(widget)
            minimum = int(field.get("min_value", -2147483648))
            maximum = int(field.get("max_value", 2147483647))

        widget.min_input.setMinimum(minimum)
        widget.min_input.setMaximum(maximum)
        widget.max_input.setMinimum(minimum)
        widget.max_input.setMaximum(maximum)

        layout.addWidget(min_label)
        layout.addWidget(widget.min_input, 1)
        layout.addWidget(max_label)
        layout.addWidget(widget.max_input, 1)

        self.set_value(field, widget, value)
        self.bind_changing(field, widget)
        return widget

    def connect_change_signal(self, widget, callback):
        widget.min_input.valueChanged.connect(lambda value: self.on_widget_changed(widget, callback))
        widget.max_input.valueChanged.connect(lambda value: self.on_widget_changed(widget, callback))

    def on_widget_changed(self, widget, callback):
        callback(self.get_widget_value(widget))

    def get_value(self, field, widget):
        return self.get_widget_value(widget)

    def set_value(self, field, widget, value):
        min_value, max_value = self.normalize_value(field, widget, value)
        widget.min_input.setValue(min_value)
        widget.max_input.setValue(max_value)

    def get_widget_value(self, widget):
        return {
            "min_value": widget.min_input.value(),
            "max_value": widget.max_input.value(),
        }

    def normalize_value(self, field, widget, value):
        default_value = field.get("default_value", 0)

        if isinstance(default_value, dict):
            min_default = default_value.get("min_value", 0)
            max_default = default_value.get("max_value", 0)
        else:
            min_default = default_value
            max_default = default_value

        if isinstance(value, dict):
            min_value = value.get("min_value", min_default)
            max_value = value.get("max_value", max_default)
        elif isinstance(value, (list, tuple)) and len(value) >= 2:
            min_value = value[0]
            max_value = value[1]
        else:
            min_value = min_default
            max_value = max_default

        if widget.number_type in ("float", "double"):
            try:
                min_value = float(min_value)
            except Exception:
                min_value = float(min_default or 0)

            try:
                max_value = float(max_value)
            except Exception:
                max_value = float(max_default or 0)
        else:
            try:
                min_value = int(min_value)
            except Exception:
                min_value = int(min_default or 0)

            try:
                max_value = int(max_value)
            except Exception:
                max_value = int(max_default or 0)

        return min_value, max_value
