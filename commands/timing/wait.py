import random
import time

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


TimingCategory = MacroCommandCategory("timing", "Timing", "m:timer")


class WaitCommand(MacroCommand):
    id = "timing.wait"
    title = "Wait"
    category = TimingCategory
    icon = "m:timer"
    description = "Wait for a fixed or random number of seconds."
    fields = [
        {
            "name": "wait_type",
            "title": "Wait Type",
            "value_type": "choice",
            "default_value": "value",
            "options": [
                {
                    "value": "value",
                    "title": "Value",
                },
                {
                    "value": "random",
                    "title": "Random",
                },
            ],
        },
        {
            "name": "seconds",
            "title": "Seconds",
            "place_holder": "1",
            "value_type": "float",
            "default_value": 1,
            "min_value": 0,
            "max_value": 86400,
            "visible_if": {
                "field": "wait_type",
                "operator": "==",
                "equals": "value",
            },
        },
        {
            "name": "random_seconds",
            "title": "Random Seconds",
            "value_type": "min_max",
            "number_type": "float",
            "min_value": 0,
            "max_value": 86400,
            "decimals": 2,
            "default_value": {
                "min_value": 0.5,
                "max_value": 2,
            },
            "visible_if": {
                "field": "wait_type",
                "operator": "==",
                "equals": "random",
            },
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        wait_type = str(
            values.get("wait_type", "value") or "value"
        ).strip().lower()

        if wait_type == "random":
            random_seconds = values.get("random_seconds") or {}
            minimum = float(random_seconds.get("min_value", 1) or 0)
            maximum = float(random_seconds.get("max_value", 3) or 0)

            if minimum > maximum:
                minimum, maximum = maximum, minimum

            return f"wait randomly from {minimum:g} to {maximum:g} secs!"

        seconds = float(values.get("seconds", 1) or 0)
        return f"wait for {seconds:g} secs!"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        wait_type = str(
            values.get("wait_type", "value") or "value"
        ).strip().lower()

        if wait_type == "random":
            random_seconds = values.get("random_seconds") or {}

            try:
                minimum = float(random_seconds.get("min", 1))
            except Exception:
                minimum = 1.0

            try:
                maximum = float(random_seconds.get("max", 3))
            except Exception:
                maximum = 3.0

            minimum = max(0.0, min(86400.0, minimum))
            maximum = max(0.0, min(86400.0, maximum))

            if minimum > maximum:
                minimum, maximum = maximum, minimum

            seconds = random.uniform(minimum, maximum)
        else:
            try:
                seconds = float(values.get("seconds", 1))
            except Exception:
                seconds = 1.0

            seconds = max(0.0, min(86400.0, seconds))

        speed = 1.0

        if runtime is not None:
            speed = max(
                0.05,
                float(getattr(runtime, "speed", 1.0) or 1.0),
            )

        if runtime is not None and hasattr(runtime, "sleep"):
            runtime.sleep(seconds / speed)
            return None

        time.sleep(seconds / speed)
        return None


def register_macro(registry):
    registry.register(WaitCommand)
