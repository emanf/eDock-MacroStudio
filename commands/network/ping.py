import platform
import re
import subprocess

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import resolve_source


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")


WINDOWS_LATENCY_PATTERN = re.compile(r"Average\s*=\s*(\d+)\s*ms", re.IGNORECASE)
UNIX_LATENCY_PATTERN = re.compile(r"=\s*[\d.]+/([\d.]+)/")


def build_ping_arguments(host, count, timeout):
    system = platform.system().lower()
    if system == "windows":
        return ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), host]
    if system == "darwin":
        return ["ping", "-c", str(count), "-W", str(int(timeout * 1000)), host]
    return ["ping", "-c", str(count), "-W", str(int(timeout)), host]


def parse_ping_latency(output):
    match = WINDOWS_LATENCY_PATTERN.search(output) or UNIX_LATENCY_PATTERN.search(output)
    return float(match.group(1)) if match else None


class PingCommand(MacroCommand):
    id = "network.ping"
    title = "Ping"
    category = NetworkCategory
    icon = "m:wifi"
    description = "Ping a host and save the success and average latency into variables."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "host_source",
            "title": "Host Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "host",
            "title": "Host",
            "place_holder": "example.com",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "host_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "host_variable",
            "title": "Host Variable",
            "place_holder": "ping_host",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "host_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "count",
            "title": "Ping Count",
            "place_holder": "4",
            "value_type": "int",
            "default_value": 4,
            "min_value": 1,
            "max_value": 10,
        },
        {
            "name": "timeout",
            "title": "Timeout Per Ping (Seconds)",
            "value_type": "float",
            "default_value": 2,
            "min_value": 0.5,
            "max_value": 30,
        },
        {
            "name": "success_variable",
            "title": "Save Success To Variable",
            "place_holder": "ping_success",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "latency_variable",
            "title": "Save Latency To Variable",
            "place_holder": "ping_latency_ms",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        host = values.get("host_variable") if values.get("host_source") == "variable" else values.get("host")
        return f"ping {host} x{values.get('count')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        host = resolve_source(values, runtime, "host", "Host")
        count = int(values.get("count", 4) or 4)
        timeout = float(values.get("timeout", 2) or 2)
        arguments = build_ping_arguments(host, count, timeout)

        run_kwargs = {
            "capture_output": True,
            "timeout": count * timeout + 10,
            "text": True,
            "encoding": "utf-8",
            "errors": "ignore",
        }
        if platform.system().lower() == "windows":
            run_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            completed = subprocess.run(arguments, **run_kwargs)
            output = completed.stdout or ""
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            output = ""
            return_code = 1

        if platform.system().lower() == "windows":
            success = return_code == 0 and "ttl=" in output.lower()
        else:
            success = return_code == 0
        latency = parse_ping_latency(output) if success else None

        success_variable = str(values.get("success_variable", "") or "")
        latency_variable = str(values.get("latency_variable", "") or "")
        if runtime is not None:
            if success_variable:
                runtime.vars.set(success_variable, success)
            if latency_variable and latency is not None:
                runtime.vars.set(latency_variable, latency)

        return {"host": host, "success": success, "latency_ms": latency}


def register_macro(registry):
    registry.register(PingCommand)
