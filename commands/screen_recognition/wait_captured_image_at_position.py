import base64
import time
from io import BytesIO

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


ScreenRecognitionCategory = MacroCommandCategory("screen_recognition", "Screen Recognition", "m:visibility")


def captured_image_to_pil_image(value):
    if not isinstance(value, dict):
        return None
    image_base64 = str(value.get("image_base64", "") or "").strip()
    if not image_base64:
        return None
    try:
        from PIL import Image
        raw = base64.b64decode(image_base64)
        image = Image.open(BytesIO(raw))
        return image.convert("RGB")
    except Exception:
        return None


def images_match(first, second, confidence):
    if first is None or second is None:
        return False

    if first.size != second.size:
        return False

    first = first.convert("RGB")
    second = second.convert("RGB")

    confidence = max(0.0, min(1.0, float(confidence or 0)))

    if confidence >= 1:
        return first.tobytes() == second.tobytes()

    try:
        from PIL import ImageChops, ImageStat
        diff = ImageChops.difference(first, second)
        stat = ImageStat.Stat(diff)
        mean = stat.mean
        if not mean:
            return False
        difference = sum(mean) / (len(mean) * 255)
        score = 1 - difference
        return score >= confidence
    except Exception:
        return first.tobytes() == second.tobytes()


def save_result_to_variable(runtime, variable_name, value):
    variable_name = str(variable_name or "").strip()
    if not variable_name or runtime is None or not hasattr(runtime, "vars"):
        return value
    runtime.vars.set(variable_name, value)
    return value


class WaitCapturedImageAtPositionCommand(MacroCommand):
    id = "screen_recognition.wait_captured_image_at_position"
    title = "Wait Captured Image At Position"
    category = ScreenRecognitionCategory
    icon = "mc:e433"
    description = "Wait until the captured image is found at a position."
    fields = [
        {
            "name": "image",
            "title": "Captured Image",
            "value_type": "captured_image",
            "default_value": {
                "image_base64": "",
                "start_x": 0,
                "start_y": 0,
                "end_x": 0,
                "end_y": 0,
                "width": 0,
                "height": 0,
            },
        },
        {
            "name": "position_type",
            "title": "Position Type",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "position",
            "title": "Position",
            "place_holder": "Screen X, Y",
            "value_type": "mouse_position",
            "default_value": {
                "x": 0,
                "y": 0,
            },
            "visible_if": {
                "field": "position_type",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "x_variable",
            "title": "X Variable",
            "place_holder": "Variable name",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "position_type",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "y_variable",
            "title": "Y Variable",
            "place_holder": "Variable name",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "position_type",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "confidence",
            "title": "Confidence",
            "place_holder": "80%",
            "value_type": "float",
            "default_value": 80,
            "min_value": 0,
            "max_value": 100,
            "decimals": 2,
        },
        {
            "name": "save_to_variable",
            "title": "Save To Variable",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def get_position(self, values, runtime=None):
        position_type = str(values.get("position_type", "value") or "value")
        if position_type == "variable":
            if runtime is None or not hasattr(runtime, "vars"):
                raise RuntimeError("Runtime variables are required for screen_recognition.wait_captured_image_at_position")
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            x = int(runtime.vars.get(x_variable) or 0)
            y = int(runtime.vars.get(y_variable) or 0)
            return x, y

        position = values.get("position") or {}
        if not isinstance(position, dict):
            position = {}
        return int(position.get("x", values.get("x", 0)) or 0), int(position.get("y", values.get("y", 0)) or 0)

    def display_text(self, values=None):
        values = self.normalize_values(values)
        position_type = str(values.get("position_type", "value") or "value")
        if position_type == "variable":
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            position_text = f"{x_variable}, {y_variable}"
        else:
            x, y = self.get_position(values)
            position_text = f"{x}, {y}"

        image = values.get("image") or {}
        width = int(image.get("width", 0) or 0) if isinstance(image, dict) else 0
        height = int(image.get("height", 0) or 0) if isinstance(image, dict) else 0
        return f"wait captured image {width}x{height} at {position_text}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        x, y = self.get_position(values, runtime)
        image_value = values.get("image") or {}
        confidence = max(0.0, min(100.0, float(values.get("confidence", 80) or 80))) / 100.0
        captured_image = captured_image_to_pil_image(image_value)
        if captured_image is None:
            return None

        width = int(image_value.get("width", captured_image.width) or captured_image.width)
        height = int(image_value.get("height", captured_image.height) or captured_image.height)

        if width <= 0 or height <= 0:
            width = captured_image.width
            height = captured_image.height

        try:
            import pyautogui
        except Exception:
            raise RuntimeError("pyautogui is required for screen recognition commands. Install it with: pip install pyautogui")

        while True:
            if runtime is not None and getattr(runtime, "stopped", False):
                return None

            screenshot = pyautogui.screenshot(region=(x, y, width, height)).convert("RGB")

            if images_match(captured_image, screenshot, confidence):
                result = {
                    "x": x,
                    "y": y,
                }
                return save_result_to_variable(runtime, values.get("save_to_variable"), result)

            time.sleep(0.03)


def register_macro(registry):
    registry.register(WaitCapturedImageAtPositionCommand)
