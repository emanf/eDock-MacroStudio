import socket

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import resolve_source


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")


class CheckPortCommand(MacroCommand):
    id = "network.check_port"
    title = "Check Port"
    category = NetworkCategory
    icon = "m:dns"
    description = "Check if a TCP port is open and save the result into a variable."
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
            "place_holder": "server_host",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "host_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "port_source",
            "title": "Port Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "port",
            "title": "Port",
            "place_holder": "80",
            "value_type": "int",
            "default_value": 80,
            "visible_if": {
                "field": "port_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "port_variable",
            "title": "Port Variable",
            "place_holder": "server_port",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "port_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "timeout",
            "title": "Timeout (Seconds)",
            "value_type": "float",
            "default_value": 3,
            "min_value": 0.5,
            "max_value": 60,
        },
        {
            "name": "variable_name",
            "title": "Save To Variable",
            "place_holder": "port_open",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        host = values.get("host_variable") if values.get("host_source") == "variable" else values.get("host")
        port = values.get("port_variable") if values.get("port_source") == "variable" else values.get("port")
        return f"check port {host}:{port}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        host = resolve_source(values, runtime, "host", "Host")
        port = int(float(resolve_source(values, runtime, "port", "Port")))
        timeout = float(values.get("timeout", 3) or 3)
        opened = False
        try:
            with socket.create_connection((host, port), timeout=timeout):
                opened = True
        except OSError:
            opened = False

        variable_name = str(values.get("variable_name", "") or "")
        if variable_name and runtime is not None:
            runtime.vars.set(variable_name, opened)

        return {"host": host, "port": port, "open": opened}


def register_macro(registry):
    registry.register(CheckPortCommand)
