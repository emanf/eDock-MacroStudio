import socket

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import http_request


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")

PUBLIC_IP_URL = "https://api.ipify.org"


def get_local_ip():
    probe = None
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return ""
    finally:
        if probe is not None:
            probe.close()


class GetIpCommand(MacroCommand):
    id = "network.get_ip"
    title = "Get IP"
    category = NetworkCategory
    icon = "m:public"
    description = "Save the local or public IP address into a variable."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "mode",
            "title": "Mode",
            "value_type": "choice",
            "default_value": "local",
            "options": [
                {
                    "value": "local",
                    "title": "Local IP",
                },
                {
                    "value": "public",
                    "title": "Public IP",
                },
            ],
        },
        {
            "name": "variable_name",
            "title": "Save To Variable",
            "place_holder": "ip_address",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        variable_name = values.get("variable_name")

        if variable_name:
            return f"get {values.get('mode')} ip -> {variable_name}"

        return f"get {values.get('mode')} ip"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        if values.get("mode", "local") == "public":
            result = http_request("GET", PUBLIC_IP_URL, timeout=10)
            ip = str(result["body"] or "").strip()
        else:
            ip = get_local_ip()

        if not ip:
            raise ValueError("Could not determine the IP address")

        variable_name = str(values.get("variable_name", "") or "")
        if variable_name and runtime is not None:
            runtime.vars.set(variable_name, ip)

        return ip


def register_macro(registry):
    registry.register(GetIpCommand)
