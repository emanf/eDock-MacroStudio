import time

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import http_request, resolve_source


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")

CHECK_URL = "https://www.gstatic.com/generate_204"


class WaitForInternetCommand(MacroCommand):
    id = "network.wait_for_internet"
    title = "Wait For Internet"
    category = NetworkCategory
    icon = "m:sync"
    description = "Wait until an internet connection is available, then continue or stop with an error."
    result_policy = ResultPolicy.CONDITION
    fields = [
        {
            "name": "check_url_source",
            "title": "Check URL Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "check_url",
            "title": "Check URL",
            "place_holder": CHECK_URL,
            "value_type": "string",
            "default_value": CHECK_URL,
            "visible_if": {
                "field": "check_url_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "check_url_variable",
            "title": "Check URL Variable",
            "place_holder": "check_url",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "check_url_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "interval",
            "title": "Check Interval (Seconds)",
            "value_type": "float",
            "default_value": 5,
            "min_value": 0.5,
            "max_value": 3600,
        },
        {
            "name": "timeout",
            "title": "Timeout (Seconds, 0 = Forever)",
            "value_type": "float",
            "default_value": 60,
            "min_value": 0,
            "max_value": 86400,
        },
        {
            "name": "variable_name",
            "title": "Save Success To Variable",
            "place_holder": "internet_ready",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        check_url = values.get("check_url_variable") if values.get("check_url_source") == "variable" else values.get("check_url")
        return f"wait for internet (check every {float(values.get('interval', 5) or 5):g} secs)"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        check_url = resolve_source(values, runtime, "check_url") or CHECK_URL
        interval = float(values.get("interval", 5) or 5)
        timeout = float(values.get("timeout", 60) or 0)
        deadline = time.time() + timeout if timeout > 0 else None
        connected = False

        while not connected:
            if runtime is not None and getattr(runtime, "stopped", False):
                return {"connected": False, "stopped": True}

            try:
                result = http_request("GET", check_url, timeout=min(5.0, max(1.0, interval)))
                connected = bool(result["ok"])
            except ValueError:
                connected = False

            if connected:
                break

            if deadline is not None and time.time() >= deadline:
                raise RuntimeError(
                    f"Internet connection was not restored within {timeout:g} seconds"
                )

            if runtime is not None and hasattr(runtime, "sleep"):
                runtime.sleep(interval)
            else:
                time.sleep(interval)

        variable_name = str(values.get("variable_name", "") or "")
        if variable_name and runtime is not None:
            runtime.vars.set(variable_name, True)

        return {"connected": True}


def register_macro(registry):
    registry.register(WaitForInternetCommand)
