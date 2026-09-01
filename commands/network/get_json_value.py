import json

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import (
    USER_AGENT_OPTIONS,
    apply_user_agent,
    extract_json_value,
    http_request,
    parse_header_lines,
    resolve_source,
)


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")


class GetJsonValueCommand(MacroCommand):
    id = "network.get_json_value"
    title = "Get JSON Value"
    category = NetworkCategory
    icon = "m:code"
    description = "Read JSON from a variable or URL and save one value into a variable."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "json_source",
            "title": "JSON Source",
            "value_type": "choice",
            "default_value": "variable",
            "options": [
                {
                    "value": "variable",
                    "title": "Variable",
                },
                {
                    "value": "url",
                    "title": "URL",
                },
            ],
        },
        {
            "name": "json_variable",
            "title": "JSON Variable",
            "place_holder": "http_body",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "json_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "url_source",
            "title": "URL Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
            "visible_if": {
                "field": "json_source",
                "operator": "==",
                "value": "url",
            },
        },
        {
            "name": "url",
            "title": "URL",
            "place_holder": "https://api.example.com/data",
            "value_type": "string",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "json_source",
                    "operator": "==",
                    "value": "url",
                },
                {
                    "field": "url_source",
                    "operator": "==",
                    "value": "value",
                },
            ],
        },
        {
            "name": "url_variable",
            "title": "URL Variable",
            "place_holder": "json_url",
            "value_type": "variable",
            "default_value": "",
            "visible_if_all": [
                {
                    "field": "json_source",
                    "operator": "==",
                    "value": "url",
                },
                {
                    "field": "url_source",
                    "operator": "==",
                    "value": "variable",
                },
            ],
        },
        {
            "name": "headers",
            "title": "Headers (One Per Line)",
            "place_holder": "Authorization: Bearer token",
            "value_type": "textarea",
            "default_value": "",
            "required": False,
            "visible_if": {
                "field": "json_source",
                "operator": "==",
                "value": "url",
            },
        },
        {
            "name": "user_agent",
            "title": "User Agent",
            "value_type": "choice",
            "default_value": "default",
            "options": USER_AGENT_OPTIONS,
            "visible_if": {
                "field": "json_source",
                "operator": "==",
                "value": "url",
            },
        },
        {
            "name": "custom_user_agent",
            "title": "Custom User Agent",
            "place_holder": "MyApp/1.0",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "visible_if_all": [
                {
                    "field": "json_source",
                    "operator": "==",
                    "value": "url",
                },
                {
                    "field": "user_agent",
                    "operator": "==",
                    "value": "custom",
                },
            ],
        },
        {
            "name": "timeout",
            "title": "Timeout (Seconds)",
            "value_type": "float",
            "default_value": 10,
            "min_value": 0.5,
            "max_value": 3600,
            "visible_if": {
                "field": "json_source",
                "operator": "==",
                "value": "url",
            },
        },
        {
            "name": "data_path",
            "title": "Data Path",
            "place_holder": "data.items.0.name",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "default_value",
            "title": "Default Value",
            "place_holder": "Value used when the path is not found",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "variable_name",
            "title": "Save To Variable",
            "place_holder": "json_value",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        path = values.get("data_path") or "(root)"
        variable_name = values.get("variable_name")

        if variable_name:
            return f"get json {path} -> {variable_name}"

        return f"get json {path}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        data_path = str(values.get("data_path", "") or "")

        if values.get("json_source", "variable") == "url":
            url = resolve_source(values, runtime, "url", "URL")
            headers = apply_user_agent(values, parse_header_lines(values.get("headers")))
            result = http_request("GET", url, headers=headers, timeout=values.get("timeout", 10))
            if not result["ok"]:
                raise ValueError(f"HTTP request failed with status {result['status']}")
            payload = result["body"]
        else:
            if runtime is None or not hasattr(runtime, "vars"):
                raise RuntimeError("Runtime variables are required for network.get_json_value")
            payload = runtime.vars.get(values.get("json_variable"))

        if isinstance(payload, (dict, list)):
            data = payload
        else:
            data = json.loads(str(payload or ""))

        value = extract_json_value(data, data_path, values.get("default_value", ""))

        variable_name = str(values.get("variable_name", "") or "")
        if variable_name and runtime is not None:
            runtime.vars.set(variable_name, value)

        return value


def register_macro(registry):
    registry.register(GetJsonValueCommand)
