import math
import random
import threading
import time

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


MouseCategory = MacroCommandCategory("mouse", "Mouse", "m:mouse")


class MouseMoveCommand(MacroCommand):
    id = "mouse.move"
    title = "Move Mouse"
    category = MouseCategory
    icon = "mc:f0fd"
    description = "Move mouse pointer into position X, Y."
    fields = [
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
            "name": "ignore_negative_position",
            "title": "Ignore Negative Position",
            "value_type": "boolean",
            "default_value": True,
        },
        {
            "name": "wait_until_done",
            "title": "Wait Until Move Is Done",
            "value_type": "boolean",
            "default_value": True,
        },
        {
            "name": "random_offset_min",
            "title": "Random Additional Min",
            "value_type": "integer",
            "default_value": -10,
            "min_value": -1000,
            "max_value": 1000,
        },
        {
            "name": "random_offset_max",
            "title": "Random Additional Max",
            "value_type": "integer",
            "default_value": 10,
            "min_value": -1000,
            "max_value": 1000,
        },
        {
            "name": "randomness_mode",
            "title": "Path Mode",
            "value_type": "choice",
            "default_value": "smooth",
            "options": [
                "smooth",
                "linear",
                "parabolic",
                "bezier",
                "perlin",
                "sinusoidal",
                "zigzag",
                "randomized",
                "random",
                "none",
            ],
        },
        {
            "name": "randomness_radius",
            "title": "Path Randomness Radius",
            "value_type": "min_max",
            "number_type": "integer",
            "min_value": 0,
            "max_value": 1000,
            "default_value": {
                "min_value": 0,
                "max_value": 10,
            },
            "visible_if": {
                "field": "randomness_mode",
                "operator": "not",
                "value": "none",
            },
        },
        {
            "name": "noise_frequency",
            "title": "Noise Frequency",
            "value_type": "min_max",
            "number_type": "float",
            "min_value": 0.10,
            "max_value": 30.00,
            "decimals": 2,
            "default_value": {
                "min_value": 1.50,
                "max_value": 4.00,
            },
            "visible_if": {
                "field": "randomness_mode",
                "operator": "not",
                "value": "none",
            },
        },
        {
            "name": "duration",
            "title": "Duration",
            "place_holder": "Seconds",
            "value_type": "min_max",
            "number_type": "float",
            "min_value": 0.0,
            "max_value": 60.0,
            "decimals": 2,
            "default_value": {
                "min_value": 0.01,
                "max_value": 0.03,
            },
            "visible_if": {
                "field": "randomness_mode",
                "operator": "not",
                "value": "none",
            },
        },
    ]

    def get_base_position(self, values, runtime=None):
        position_type = str(values.get("position_type", "value") or "value")
        if position_type == "variable":
            if runtime is None or not hasattr(runtime, "vars"):
                raise RuntimeError("Runtime variables are required for mouse.move")
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            x = int(runtime.vars.get(x_variable) or 0)
            y = int(runtime.vars.get(y_variable) or 0)
        else:
            position = values.get("position") or {}
            if not isinstance(position, dict):
                position = {}
            x = int(position.get("x", values.get("x", 0)) or 0)
            y = int(position.get("y", values.get("y", 0)) or 0)

        return x, y

    def get_position(self, values, runtime=None):
        x, y = self.get_base_position(values, runtime)

        random_offset_min = int(values.get("random_offset_min", -10) or 0)
        random_offset_max = int(values.get("random_offset_max", 10) or 0)
        if random_offset_min > random_offset_max:
            random_offset_min, random_offset_max = random_offset_max, random_offset_min

        x += random.randint(random_offset_min, random_offset_max)
        y += random.randint(random_offset_min, random_offset_max)

        return x, y

    def get_range(self, value, default_min, default_max, value_type=float):
        if isinstance(value, dict):
            minimum = value.get("min_value", value.get("min", default_min))
            maximum = value.get("max_value", value.get("max", default_max))
        else:
            minimum = value
            maximum = value

        try:
            minimum = value_type(minimum)
        except Exception:
            minimum = value_type(default_min)

        try:
            maximum = value_type(maximum)
        except Exception:
            maximum = value_type(default_max)

        if minimum > maximum:
            minimum, maximum = maximum, minimum

        return minimum, maximum

    def random_float_range(self, value, default_min, default_max):
        minimum, maximum = self.get_range(
            value,
            default_min,
            default_max,
            float,
        )
        return random.uniform(minimum, maximum)

    def random_integer_range(self, value, default_min, default_max):
        minimum, maximum = self.get_range(
            value,
            default_min,
            default_max,
            int,
        )
        return random.randint(minimum, maximum)

    def smoothstep(self, value):
        value = max(0.0, min(1.0, float(value)))
        return value * value * (3.0 - (2.0 * value))

    def fade(self, value):
        value = max(0.0, min(1.0, float(value)))
        return value * value * value * (value * (value * 6.0 - 15.0) + 10.0)

    def interpolate_noise(self, samples, position):
        if not samples:
            return 0.0

        if len(samples) == 1:
            return samples[0]

        position = max(0.0, min(float(len(samples) - 1), position))
        left_index = int(math.floor(position))
        right_index = min(len(samples) - 1, left_index + 1)
        fraction = self.fade(position - left_index)

        return (
            samples[left_index] * (1.0 - fraction)
            + samples[right_index] * fraction
        )

    def generate_path(
        self,
        start_x,
        start_y,
        end_x,
        end_y,
        mode,
        radius,
        duration,
        frequency,
    ):
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        distance = math.hypot(delta_x, delta_y)

        if distance <= 0:
            return [(end_x, end_y)]

        perpendicular_x = -delta_y / distance
        perpendicular_y = delta_x / distance
        direction_x = delta_x / distance
        direction_y = delta_y / distance

        available_modes = [
            "smooth",
            "linear",
            "parabolic",
            "bezier",
            "perlin",
            "sinusoidal",
            "zigzag",
            "randomized",
        ]

        if mode == "random":
            mode = random.choice(available_modes)

        steps = max(2, int(math.ceil(max(0.0, float(duration)) * 120.0)))
        radius = max(0.0, float(radius))
        frequency = max(0.1, float(frequency))
        phase = random.uniform(0.0, math.tau)
        direction = random.choice([-1.0, 1.0])
        amplitude = random.uniform(0.35, 1.0) * radius
        longitudinal_amplitude = random.uniform(0.0, radius * 0.25)

        control_one_t = random.uniform(0.2, 0.45)
        control_two_t = random.uniform(0.55, 0.8)
        control_one_offset = random.uniform(-radius, radius)
        control_two_offset = random.uniform(-radius, radius)

        control_one_x = (
            start_x
            + delta_x * control_one_t
            + perpendicular_x * control_one_offset
        )
        control_one_y = (
            start_y
            + delta_y * control_one_t
            + perpendicular_y * control_one_offset
        )
        control_two_x = (
            start_x
            + delta_x * control_two_t
            + perpendicular_x * control_two_offset
        )
        control_two_y = (
            start_y
            + delta_y * control_two_t
            + perpendicular_y * control_two_offset
        )

        noise_count = max(3, int(math.ceil(frequency)) + 2)
        perpendicular_noise = [
            random.uniform(-1.0, 1.0)
            for _ in range(noise_count)
        ]
        longitudinal_noise = [
            random.uniform(-1.0, 1.0)
            for _ in range(noise_count)
        ]

        path = []

        for index in range(1, steps + 1):
            t = index / steps
            envelope = math.sin(math.pi * t)
            path_t = t
            offset = 0.0
            longitudinal_offset = 0.0

            if mode == "smooth":
                path_t = self.smoothstep(t)
                offset = (
                    math.sin((t * frequency * math.tau) + phase)
                    * amplitude
                    * 0.12
                    * envelope
                )
            elif mode == "parabolic":
                path_t = self.smoothstep(t)
                offset = (
                    4.0
                    * t
                    * (1.0 - t)
                    * amplitude
                    * direction
                )
            elif mode == "sinusoidal":
                path_t = self.smoothstep(t)
                offset = (
                    math.sin((t * frequency * math.tau) + phase)
                    * amplitude
                    * envelope
                )
            elif mode == "zigzag":
                path_t = t
                cycle = t * frequency
                triangle = 1.0 - 4.0 * abs(
                    round(cycle - 0.25) - (cycle - 0.25)
                )
                offset = triangle * amplitude * envelope
            elif mode == "randomized":
                path_t = self.smoothstep(t)
                offset = random.uniform(-radius, radius) * envelope
                longitudinal_offset = (
                    random.uniform(
                        -longitudinal_amplitude,
                        longitudinal_amplitude,
                    )
                    * envelope
                )
            elif mode == "perlin":
                path_t = self.smoothstep(t)
                noise_position = t * (noise_count - 1)
                offset = (
                    self.interpolate_noise(
                        perpendicular_noise,
                        noise_position,
                    )
                    * amplitude
                    * envelope
                )
                longitudinal_offset = (
                    self.interpolate_noise(
                        longitudinal_noise,
                        noise_position,
                    )
                    * longitudinal_amplitude
                    * envelope
                )
            elif mode == "bezier":
                inverse_t = 1.0 - t
                x = (
                    inverse_t * inverse_t * inverse_t * start_x
                    + 3.0
                    * inverse_t
                    * inverse_t
                    * t
                    * control_one_x
                    + 3.0
                    * inverse_t
                    * t
                    * t
                    * control_two_x
                    + t * t * t * end_x
                )
                y = (
                    inverse_t * inverse_t * inverse_t * start_y
                    + 3.0
                    * inverse_t
                    * inverse_t
                    * t
                    * control_one_y
                    + 3.0
                    * inverse_t
                    * t
                    * t
                    * control_two_y
                    + t * t * t * end_y
                )
                organic_noise = (
                    math.sin((t * frequency * math.tau) + phase)
                    * radius
                    * 0.08
                    * envelope
                )
                x += perpendicular_x * organic_noise
                y += perpendicular_y * organic_noise
                path.append((round(x), round(y)))
                continue

            x = (
                start_x
                + delta_x * path_t
                + perpendicular_x * offset
                + direction_x * longitudinal_offset
            )
            y = (
                start_y
                + delta_y * path_t
                + perpendicular_y * offset
                + direction_y * longitudinal_offset
            )

            path.append((round(x), round(y)))

        path[-1] = (end_x, end_y)
        return path

    def move_path(self, path, duration, runtime):
        if not path:
            return None

        duration = max(0.0, float(duration))

        if duration <= 0:
            point_x, point_y = path[-1]
            runtime.pyautogui_call(
                "moveTo",
                point_x,
                point_y,
                duration=0,
                _pause=False,
            )
            return None

        started_at = time.perf_counter()
        path_length = len(path)

        for index, (point_x, point_y) in enumerate(path, start=1):
            if getattr(runtime, "stopped", False):
                return None

            target_time = started_at + (duration * index / path_length)
            remaining = target_time - time.perf_counter()

            if remaining > 0:
                time.sleep(remaining)

            runtime.pyautogui_call(
                "moveTo",
                point_x,
                point_y,
                duration=0,
                _pause=False,
            )

        return None

    def display_text(self, values=None):
        values = self.normalize_values(values)
        position_type = str(values.get("position_type", "value") or "value")
        randomness_mode = str(
            values.get("randomness_mode", "smooth") or "smooth"
        )

        if position_type == "variable":
            x_variable = str(values.get("x_variable", "") or "").strip()
            y_variable = str(values.get("y_variable", "") or "").strip()
            position_text = f"{x_variable}, {y_variable}"
        else:
            position = values.get("position") or {}
            if not isinstance(position, dict):
                position = {}
            x = int(position.get("x", values.get("x", 0)) or 0)
            y = int(position.get("y", values.get("y", 0)) or 0)
            position_text = f"{x}, {y}"

        return f"move mouse into position {position_text} using {randomness_mode} path"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)

        if runtime is None or not hasattr(runtime, "pyautogui_call"):
            raise RuntimeError("Runtime is required for mouse.move")

        ignore_negative_position = bool(values.get("ignore_negative_position", True))
        wait_until_done = bool(values.get("wait_until_done", True))

        base_x, base_y = self.get_base_position(values, runtime)
        if ignore_negative_position and (base_x < 0 or base_y < 0):
            return None

        x, y = self.get_position(values, runtime)
        randomness_mode = str(
            values.get("randomness_mode", "smooth") or "smooth"
        ).strip().lower()

        valid_modes = {
            "smooth",
            "linear",
            "parabolic",
            "bezier",
            "perlin",
            "sinusoidal",
            "zigzag",
            "randomized",
            "random",
            "none",
        }

        if randomness_mode not in valid_modes:
            randomness_mode = "smooth"

        if randomness_mode == "none":
            runtime.pyautogui_call("moveTo", x, y, duration=0, _pause=False)
            return None

        duration = max(
            0.0,
            self.random_float_range(
                values.get("duration"),
                0.1,
                0.5,
            ),
        )
        radius = max(
            0,
            self.random_integer_range(
                values.get("randomness_radius"),
                0,
                10,
            ),
        )
        frequency = max(
            0.1,
            self.random_float_range(
                values.get("noise_frequency"),
                1.5,
                4.0,
            ),
        )

        start_position = runtime.pyautogui_call("position")
        start_x = int(getattr(start_position, "x", start_position[0]))
        start_y = int(getattr(start_position, "y", start_position[1]))

        if duration <= 0:
            runtime.pyautogui_call("moveTo", x, y, duration=0, _pause=False)
            return None

        path = self.generate_path(
            start_x,
            start_y,
            x,
            y,
            randomness_mode,
            radius,
            duration,
            frequency,
        )

        if wait_until_done:
            return self.move_path(path, duration, runtime)

        thread = threading.Thread(
            target=self.move_path,
            args=(path, duration, runtime),
            daemon=True,
        )
        thread.start()

        return None


def register_macro(registry):
    registry.register(MouseMoveCommand)
