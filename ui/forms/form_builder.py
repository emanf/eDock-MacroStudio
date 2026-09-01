import platform
from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel, QMessageBox, QSizePolicy, QVBoxLayout, QWidget

from ..widgets.title_bar import TitleBar
from .fields_registry import DialogFieldRegistry, create_default_registry
from .form_context import FormContext
from .form_style import FORM_STYLE

FORM_MIN_WIDTH = 520


class FormBuilder(QDialog):
    _registry = None

    def __init__(self, schema, values=None, parent=None, runtime_variables=None, runtime_comments=None, context=None):
        super().__init__(parent)
        self.schema = deepcopy(schema) if isinstance(schema, dict) else {}
        self.values = deepcopy(values) if isinstance(values, dict) else {}
        self.inputs = {}
        self._refreshing_computed_fields = False

        self.context = context if context else (FormContext(parent) if parent else None)
        self.registry = self.get_registry(self.context)

        self.runtime_variables = deepcopy(runtime_variables) if isinstance(runtime_variables, list) else []
        self.runtime_comments = deepcopy(runtime_comments) if isinstance(runtime_comments, list) else []

        title_text = str(self.schema.get("title", "Input") or "Input")
        self.setWindowTitle(title_text)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(FORM_MIN_WIDTH)
        self.setFixedWidth(FORM_MIN_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setStyleSheet(FORM_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        card = QWidget()
        card.setObjectName("rootCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        card.setLayout(card_layout)
        root.addWidget(card)

        card_layout.addWidget(
            TitleBar(
                self,
                title=title_text,
                window_buttons=False,
            )
        )

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(18, 12, 18, 16)
        content_layout.setSpacing(14)
        content.setLayout(content_layout)
        card_layout.addWidget(content, 1)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form = form

        for field in self.schema.get("fields", []) or []:
            if not isinstance(field, dict):
                continue

            name = str(field.get("name", "") or "").strip()
            if not name:
                continue

            field = self.prepare_field(field)

            if self.is_hidden_field(field):
                continue

            title = str(field.get("title", name) or name)
            value = self.values.get(name, field.get("default_value", ""))
            widget = self.registry.create_widget(field, value, self)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, widget.sizePolicy().verticalPolicy())
            label = QLabel(title, self)

            self.inputs[name] = {
                "field": field,
                "widget": widget,
                "label": label,
            }

            form.addRow(label, widget)
            self.bind_field_change(name)

        content_layout.addLayout(form)

        buttons = QDialogButtonBox()
        cancel_button = buttons.addButton(
            "Cancel", QDialogButtonBox.ButtonRole.RejectRole
        )
        save_button = buttons.addButton(
            str(self.schema.get("submit_text", "Save/Add") or "Save/Add"),
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        cancel_button.clicked.connect(self.reject)
        save_button.clicked.connect(self.accept)
        content_layout.addWidget(buttons)

        self.refresh_computed_fields()
        self.apply_field_rules()

    @classmethod
    def get_registry(cls, context=None):
        if cls._registry is None:
            cls._registry = create_default_registry(context)
        return cls._registry

    @classmethod
    def set_registry(cls, registry):
        if isinstance(registry, DialogFieldRegistry):
            cls._registry = registry

    @classmethod
    def register_field(cls, value_type, field_handler):
        registry = cls.get_registry()
        registry.register(value_type, field_handler)

    def prepare_field(self, field):
        prepared = dict(field)
        value_type = str(prepared.get("value_type", "string") or "string").strip().lower()

        if "hidden" not in prepared and "hide" in prepared:
            prepared["hidden"] = bool(prepared.get("hide"))
        elif "hidden" in prepared:
            prepared["hidden"] = bool(prepared.get("hidden"))

        if "required" not in prepared:
            prepared["required"] = value_type not in ("status", "result", "message")

        if value_type == "variable":
            options = []

            for variable in self.runtime_variables:
                if isinstance(variable, dict):
                    variable_name = str(variable.get("name", "") or "").strip()
                else:
                    variable_name = str(variable or "").strip()

                if variable_name and variable_name not in options:
                    options.append(variable_name)

            prepared["options"] = options
            prepared["on_variable_added"] = self.on_runtime_variable_added
            prepared["get_variable_options"] = self.get_runtime_variable_options

        if value_type == "comment":
            prepared["value_type"] = "choice"
            prepared["options"] = self.get_runtime_comment_options()
            prepared["validate_comment_exists"] = True

        return prepared

    def is_hidden_field(self, field):
        if not isinstance(field, dict):
            return False

        if field.get("hidden") is True:
            return True

        if field.get("hide") is True:
            return True

        if not self.evaluate_os(field):
            return True

        return False

    def get_runtime_variable_options(self):
        options = []

        for variable in self.runtime_variables:
            if isinstance(variable, dict):
                variable_name = str(variable.get("name", "") or "").strip()
            else:
                variable_name = str(variable or "").strip()

            if variable_name and variable_name not in options:
                options.append(variable_name)

        return options

    def get_runtime_comment_options(self):
        options = []

        for comment in self.runtime_comments:
            if isinstance(comment, dict):
                comment_name = str(comment.get("name", "") or "").strip()
            else:
                comment_name = str(comment or "").strip()

            if comment_name and comment_name not in options:
                options.append(comment_name)

        return options

    def on_runtime_variable_added(self, name):
        variable_name = str(name or "").strip()

        if not variable_name:
            return

        for variable in self.runtime_variables:
            if isinstance(variable, dict) and str(variable.get("name", "") or "").strip() == variable_name:
                return

            if not isinstance(variable, dict) and str(variable or "").strip() == variable_name:
                return

        self.runtime_variables.append({
            "name": variable_name,
            "type": "auto",
        })

    def has_field(self, name):
        name = str(name or "").strip()
        return name in self.inputs

    def has_visible_fields(self):
        return bool(self.inputs)

    def field_widget(self, name):
        name = str(name or "").strip()
        item = self.inputs.get(name)

        if not item:
            return None

        return item["widget"]

    def field_value(self, name, default=None):
        name = str(name or "").strip()
        item = self.inputs.get(name)

        if not item:
            return default

        field = item["field"]
        widget = item["widget"]
        return self.registry.get_value(field, widget)

    def set_field_value(self, name, value):
        name = str(name or "").strip()
        item = self.inputs.get(name)

        if not item:
            return False

        field = item["field"]
        widget = item["widget"]
        self.registry.set_value(field, widget, value)
        self.values[name] = deepcopy(value)
        self.refresh_computed_fields()
        self.apply_field_rules()
        return True

    def set_data(self, values):
        if not isinstance(values, dict):
            return

        for name, value in values.items():
            item = self.inputs.get(str(name or "").strip())

            if not item:
                continue

            field = item["field"]
            widget = item["widget"]
            self.registry.set_value(field, widget, value)
            self.values[name] = deepcopy(value)

        self.refresh_computed_fields()
        self.apply_field_rules()

    def current_values(self, include_transient=False):
        result = {}

        for name, item in self.inputs.items():
            field = item["field"]

            if not include_transient and field.get("transient") is True:
                continue

            widget = item["widget"]
            result[name] = self.registry.get_value(field, widget)

        return result

    def data(self):
        return deepcopy(self.current_values(include_transient=False))

    def bind_field_change(self, name):
        item = self.inputs.get(name)

        if not item:
            return

        field = item["field"]

        if field.get("transient") is True:
            return

        widget = item["widget"]
        handler = self.registry.get_handler(field.get("value_type", "string"))

        if not handler:
            return

        try:
            handler.connect_change_signal(
                widget,
                lambda value=None, field_name=name: self.on_field_changed(field_name),
            )
        except Exception:
            pass

    def on_field_changed(self, name):
        self.values[name] = deepcopy(self.field_value(name))
        self.clear_field_error(name)
        self.refresh_computed_fields()
        self.apply_field_rules()

    def refresh_computed_fields(self):
        if self._refreshing_computed_fields:
            return

        self._refreshing_computed_fields = True

        try:
            current_values = deepcopy(self.current_values(include_transient=False))

            for name, item in self.inputs.items():
                field = item["field"]
                callback = field.get("compute_value")

                if not callable(callback):
                    continue

                try:
                    computed_value = callback(deepcopy(current_values))
                except Exception as error:
                    computed_value = {
                        "value": str(error),
                        "status": "danger",
                    }

                self.registry.set_value(field, item["widget"], computed_value)
                self.values[name] = deepcopy(computed_value)
        finally:
            self._refreshing_computed_fields = False

    def accept(self):
        if not self.inputs:
            super().accept()
            return

        if not self.validate_required_fields():
            return

        if not self.validate_comment_fields():
            return

        super().accept()

    def validate_required_fields(self):
        if not self.inputs:
            return True

        first_invalid_widget = None
        invalid_titles = []

        for name, item in self.inputs.items():
            field = item["field"]
            widget = item["widget"]
            label = item["label"]

            self.clear_field_error(name)

            if field.get("transient") is True:
                continue

            if not self.is_required_field(field):
                continue

            if not widget.isVisible() or not widget.isEnabled():
                continue

            value = self.registry.get_value(field, widget)

            if not self.is_empty_value(value):
                continue

            title = str(field.get("title", name) or name)
            invalid_titles.append(title)
            label.setStyleSheet("color: #e87868;")
            widget.setStyleSheet(widget.styleSheet() + "border-color: #e87868;")

            if first_invalid_widget is None:
                first_invalid_widget = widget

        if not invalid_titles:
            return True

        if first_invalid_widget:
            first_invalid_widget.setFocus()

        warning = QMessageBox(self)
        warning.setWindowModality(Qt.WindowModality.WindowModal)
        warning.setIcon(QMessageBox.Icon.Warning)
        warning.setWindowTitle("Required Fields")
        warning.setText("Please fill required field(s):\n" + "\n".join(invalid_titles))
        warning.setStandardButtons(QMessageBox.StandardButton.Ok)
        warning.exec()

        return False

    def validate_comment_fields(self):
        if not self.inputs:
            return True

        first_invalid_widget = None
        invalid_messages = []
        runtime_comments = self.get_runtime_comment_options()

        for name, item in self.inputs.items():
            field = item["field"]
            widget = item["widget"]
            label = item["label"]

            if field.get("transient") is True:
                continue

            if not widget.isVisible() or not widget.isEnabled():
                continue

            value = str(self.registry.get_value(field, widget) or "").strip()
            title = str(field.get("title", name) or name)

            if field.get("validate_comment_exists") is True and value not in runtime_comments:
                invalid_messages.append(f"{title}: selected comment does not exist.")
                label.setStyleSheet("color: #e87868;")
                widget.setStyleSheet(widget.styleSheet() + "border-color: #e87868;")

                if first_invalid_widget is None:
                    first_invalid_widget = widget

            if field.get("validate_comment_unique") is True and value in runtime_comments:
                invalid_messages.append(f"{title}: this comment already exists.")
                label.setStyleSheet("color: #e87868;")
                widget.setStyleSheet(widget.styleSheet() + "border-color: #e87868;")

                if first_invalid_widget is None:
                    first_invalid_widget = widget

        if not invalid_messages:
            return True

        if first_invalid_widget:
            first_invalid_widget.setFocus()

        warning = QMessageBox(self)
        warning.setWindowModality(Qt.WindowModality.WindowModal)
        warning.setIcon(QMessageBox.Icon.Warning)
        warning.setWindowTitle("Comment Validation")
        warning.setText("\n".join(invalid_messages))
        warning.setStandardButtons(QMessageBox.StandardButton.Ok)
        warning.exec()

        return False

    def clear_field_error(self, name):
        item = self.inputs.get(name)

        if not item:
            return

        label = item["label"]
        widget = item["widget"]
        label.setStyleSheet("")
        widget.setStyleSheet("")

    def is_required_field(self, field):
        return field.get("required", True) is True

    def apply_field_rules(self):
        for name, item in self.inputs.items():
            field = item["field"]
            label = item["label"]
            widget = item["widget"]

            is_visible = self.evaluate_visible(field)
            is_enabled = self.evaluate_enabled(field)

            label.setVisible(is_visible)
            widget.setVisible(is_visible)
            label.setEnabled(is_enabled)
            widget.setEnabled(is_enabled)

        self.form.invalidate()
        self.form.activate()
        self.layout().invalidate()
        self.layout().activate()

        hint = self.sizeHint()
        width = max(hint.width(), FORM_MIN_WIDTH)
        self.setMinimumWidth(FORM_MIN_WIDTH)
        self.setFixedWidth(width)
        self.setFixedHeight(hint.height())

    def evaluate_visible(self, field):
        if not self.evaluate_os(field):
            return False

        if "visible_if" in field:
            return self.evaluate_rule(field.get("visible_if"))

        if "visible_if_all" in field:
            return self.evaluate_all_rules(field.get("visible_if_all"))

        if "visible_if_any" in field:
            return self.evaluate_any_rules(field.get("visible_if_any"))

        return True

    def evaluate_enabled(self, field):
        if not self.evaluate_os(field):
            return False

        if "enabled_if" in field:
            return self.evaluate_rule(field.get("enabled_if"))

        if "enabled_if_all" in field:
            return self.evaluate_all_rules(field.get("enabled_if_all"))

        if "enabled_if_any" in field:
            return self.evaluate_any_rules(field.get("enabled_if_any"))

        return True

    def evaluate_os(self, field):
        allowed_os = field.get("os")
        if not allowed_os:
            return True

        current = platform.system().lower()
        if isinstance(allowed_os, str):
            allowed_os = [allowed_os.lower()]
        elif isinstance(allowed_os, list):
            allowed_os = [str(o).lower() for o in allowed_os]
        else:
            return True

        mapping = {
            "windows": "windows", "win": "windows", 
            "linux": "linux", 
            "macos": "darwin", "mac": "darwin", "darwin": "darwin"
        }
        normalized_allowed = [mapping.get(o, o) for o in allowed_os]
        return current in normalized_allowed

    def evaluate_all_rules(self, rules):
        if not isinstance(rules, list) or not rules:
            return True

        for rule in rules:
            if not self.evaluate_rule(rule):
                return False

        return True

    def evaluate_any_rules(self, rules):
        if not isinstance(rules, list) or not rules:
            return True

        for rule in rules:
            if self.evaluate_rule(rule):
                return True

        return False

    def evaluate_rule(self, rule):
        if not isinstance(rule, dict):
            return True

        field_name = str(rule.get("field", "") or "").strip()

        if not field_name:
            return True

        operator = str(rule.get("operator", "==") or "==").strip().lower()
        current_value = self.field_value(field_name)

        if operator == "is true":
            return bool(current_value) is True

        if operator == "is false":
            return bool(current_value) is False

        if operator == "empty":
            return self.is_empty_value(current_value)

        if operator == "not empty":
            return not self.is_empty_value(current_value)

        if "equals" in rule and "value" not in rule:
            expected_value = rule.get("equals")
        else:
            expected_value = rule.get("value")

        if operator in ("==", "=", "equal", "equals"):
            return current_value == expected_value

        if operator in ("!=", "<>", "not equal", "not_equals", "not"):
            return current_value != expected_value

        if operator == "in":
            if isinstance(expected_value, (list, tuple, set)):
                return current_value in expected_value

            return False

        if operator == "not in":
            if isinstance(expected_value, (list, tuple, set)):
                return current_value not in expected_value

            return True

        return False

    def is_empty_value(self, value):
        if value is None:
            return True

        if isinstance(value, str):
            return value.strip() == ""

        if isinstance(value, (list, tuple, dict, set)):
            return len(value) == 0

        return False

    @staticmethod
    def get_data(schema, values=None, parent=None, runtime_variables=None, runtime_comments=None, context=None):
        dialog = FormBuilder(
            schema=schema,
            values=values,
            parent=parent,
            runtime_variables=runtime_variables,
            runtime_comments=runtime_comments,
            context=context,
        )

        if not dialog.inputs:
            return dialog.data()

        result = dialog.exec()

        if result != QDialog.DialogCode.Accepted:
            return None

        return dialog.data()
