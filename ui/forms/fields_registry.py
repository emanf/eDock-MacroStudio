from .fields.audio_field import AudioFieldHandler
from .fields.captured_image_field import CapturedImageFieldHandler
from .fields.color_field import ColorFieldHandler
from .fields.comment_field import CommentFieldHandler
from .fields.string_field import StringFieldHandler
from .fields.text_area_field import TextAreaFieldHandler
from .fields.code_field import CodeFieldHandler
from .fields.number_field import IntegerFieldHandler, FloatFieldHandler, MinMaxFieldHandler
from .fields.bool_field import BooleanFieldHandler
from .fields.checkbox_group_field import CheckboxGroupFieldHandler
from .fields.radio_group_field import RadioGroupFieldHandler
from .fields.choice_field import ChoiceFieldHandler
from .fields.file_field import FileFieldHandler
from .fields.folder_field import FolderFieldHandler
from .fields.mouse_position_field import MousePositionFieldHandler
from .fields.screen_region_field import ScreenRegionFieldHandler
from .fields.variable_field import VariableFieldHandler
from .fields.macro_group_field import MacroGroupFieldHandler
from .fields.status_field import StatusFieldHandler


class DialogFieldRegistry:
    def __init__(self, context=None):
        self._handlers = {}
        self.context = context

    def register(self, value_type, field_handler):
        key = str(value_type or "string").strip().lower()
        self._handlers[key] = field_handler

    def get_handler(self, value_type):
        key = str(value_type or "string").strip().lower()
        return self._handlers.get(key) or self._handlers.get("string")

    def create_widget(self, field, value, parent=None):
        handler = self.get_handler(field.get("value_type", "string"))
        return handler.create_widget(field, value, parent)

    def get_value(self, field, widget):
        handler = self.get_handler(field.get("value_type", "string"))
        return handler.get_value(field, widget)

    def set_value(self, field, widget, value):
        handler = self.get_handler(field.get("value_type", "string"))
        handler.set_value(field, widget, value)

    def validate_value(self, field, widget, value):
        handler = self.get_handler(field.get("value_type", "string"))
        return handler.validate_value(field, widget, value)


def create_default_registry(context=None):
    registry = DialogFieldRegistry(context=context)

    registry.register("string", StringFieldHandler(context))
    registry.register("text", StringFieldHandler(context))

    registry.register("textarea", TextAreaFieldHandler(context))
    registry.register("text_area", TextAreaFieldHandler(context))
    registry.register("multiline", TextAreaFieldHandler(context))
    registry.register("multi_line", TextAreaFieldHandler(context))

    registry.register("code", CodeFieldHandler(context))
    registry.register("python_code", CodeFieldHandler(context))
    registry.register("python", CodeFieldHandler(context))

    registry.register("integer", IntegerFieldHandler(context))
    registry.register("int", IntegerFieldHandler(context))

    registry.register("float", FloatFieldHandler(context))
    registry.register("double", FloatFieldHandler(context))

    registry.register("min_max", MinMaxFieldHandler(context))
    registry.register("range", MinMaxFieldHandler(context))

    registry.register("boolean", BooleanFieldHandler(context))
    registry.register("bool", BooleanFieldHandler(context))

    registry.register("checkbox_group", CheckboxGroupFieldHandler(context))
    registry.register("check_group", CheckboxGroupFieldHandler(context))
    registry.register("multi_checkbox", CheckboxGroupFieldHandler(context))
    registry.register("multi_check_box", CheckboxGroupFieldHandler(context))
    registry.register("checkboxes", CheckboxGroupFieldHandler(context))
    registry.register("check_boxes", CheckboxGroupFieldHandler(context))

    registry.register("radio_group", RadioGroupFieldHandler(context))
    registry.register("radio_buttons", RadioGroupFieldHandler(context))

    registry.register("choice", ChoiceFieldHandler(context))

    registry.register("color", ColorFieldHandler(context))

    registry.register("mouse_position", MousePositionFieldHandler(context))
    registry.register("position", MousePositionFieldHandler(context))

    registry.register("file", FileFieldHandler(context))
    registry.register("file_path", FileFieldHandler(context))

    registry.register("folder", FolderFieldHandler(context))
    registry.register("folder_path", FolderFieldHandler(context))
    registry.register("directory", FolderFieldHandler(context))

    registry.register("captured_image", CapturedImageFieldHandler(context))
    registry.register("image_capture", CapturedImageFieldHandler(context))
    registry.register("screen_region_image", CapturedImageFieldHandler(context))

    registry.register("screen_region", ScreenRegionFieldHandler(context))
    registry.register("region", ScreenRegionFieldHandler(context))
    registry.register("screen_area", ScreenRegionFieldHandler(context))
    registry.register("area", ScreenRegionFieldHandler(context))

    registry.register("audio", AudioFieldHandler(context))
    registry.register("captured_audio", AudioFieldHandler(context))
    registry.register("audio_capture", AudioFieldHandler(context))
    registry.register("system_audio", AudioFieldHandler(context))

    registry.register("variable", VariableFieldHandler(context))

    registry.register("comment", CommentFieldHandler(context))

    registry.register("macro_group", MacroGroupFieldHandler(context))

    registry.register("status", StatusFieldHandler(context))
    registry.register("result", StatusFieldHandler(context))
    registry.register("message", StatusFieldHandler(context))

    return registry
