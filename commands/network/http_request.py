import json

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import (
    USER_AGENT_OPTIONS,
    apply_user_agent,
    build_request_body,
    http_request,
    parse_header_lines,
    resolve_source,
)


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")


class HttpRequestCommand(MacroCommand):
    id = "network.http_request"
    title = "HTTP Request"
    category = NetworkCategory
    icon = "m:language"
    description = "Send an HTTP request and save the status, body, and headers into variables."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "method",
            "title": "Method",
            "value_type": "choice",
            "default_value": "GET",
            "options": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        },
        {
            "name": "url_source",
            "title": "URL Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "url",
            "title": "URL",
            "place_holder": "https://api.example.com/data",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "url_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "url_variable",
            "title": "URL Variable",
            "place_holder": "request_url",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "url_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "headers",
            "title": "Headers (One Per Line)",
            "place_holder": "Accept: application/json",
            "value_type": "textarea",
            "default_value": "",
            "required": False,
        },
        {
            "name": "user_agent",
            "title": "User Agent",
            "value_type": "choice",
            "default_value": "default",
            "options": USER_AGENT_OPTIONS,
        },
        {
            "name": "custom_user_agent",
            "title": "Custom User Agent",
            "place_holder": "MyApp/1.0",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "visible_if": {
                "field": "user_agent",
                "operator": "==",
                "value": "custom",
            },
        },
        {
            "name": "auth_type",
            "title": "Auth Type",
            "value_type": "choice",
            "default_value": "none",
            "options": [
                {
                    "value": "none",
                    "title": "None",
                },
                {
                    "value": "bearer",
                    "title": "Bearer Token",
                },
                {
                    "value": "basic",
                    "title": "Basic Auth",
                },
            ],
        },
        {
            "name": "auth_token",
            "title": "Bearer Token",
            "place_holder": "token value",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "visible_if": {
                "field": "auth_type",
                "operator": "==",
                "value": "bearer",
            },
        },
        {
            "name": "auth_username",
            "title": "Username",
            "place_holder": "basic auth username",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "visible_if": {
                "field": "auth_type",
                "operator": "==",
                "value": "basic",
            },
        },
        {
            "name": "auth_password",
            "title": "Password",
            "place_holder": "basic auth password",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "visible_if": {
                "field": "auth_type",
                "operator": "==",
                "value": "basic",
            },
        },
        {
            "name": "body_source",
            "title": "Body Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
            "visible_if": {
                "field": "method",
                "operator": "in",
                "value": ["POST", "PUT", "PATCH"],
            },
        },
        {
            "name": "body_type",
            "title": "Body Type",
            "value_type": "choice",
            "default_value": "text",
            "options": [
                {
                    "value": "text",
                    "title": "Text",
                },
                {
                    "value": "json",
                    "title": "JSON",
                },
                {
                    "value": "form",
                    "title": "Form",
                },
            ],
            "visible_if": {
                "field": "method",
                "operator": "in",
                "value": ["POST", "PUT", "PATCH"],
            },
        },
        {
            "name": "body_value",
            "title": "Body",
            "place_holder": '{"name": "value"}',
            "value_type": "textarea",
            "default_value": "",
            "required": False,
            "visible_if_all": [
                {
                    "field": "method",
                    "operator": "in",
                    "value": ["POST", "PUT", "PATCH"],
                },
                {
                    "field": "body_source",
                    "operator": "==",
                    "value": "value",
                },
            ],
        },
        {
            "name": "body_variable",
            "title": "Body Variable",
            "place_holder": "request_body",
            "value_type": "variable",
            "default_value": "",
            "required": False,
            "visible_if_all": [
                {
                    "field": "method",
                    "operator": "in",
                    "value": ["POST", "PUT", "PATCH"],
                },
                {
                    "field": "body_source",
                    "operator": "==",
                    "value": "variable",
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
        },
        {
            "name": "save_status_to",
            "title": "Save Status To Variable",
            "place_holder": "http_status",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "save_body_to",
            "title": "Save Body To Variable",
            "place_holder": "http_body",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "save_headers_to",
            "title": "Save Headers To Variable",
            "place_holder": "http_headers",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        url = values.get("url_variable") if values.get("url_source") == "variable" else values.get("url")
        variable_name = values.get("save_body_to")

        if variable_name:
            return f"http {values.get('method')} {url} -> {variable_name}"

        return f"http {values.get('method')} {url}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        url = resolve_source(values, runtime, "url", "URL")
        headers = apply_user_agent(values, parse_header_lines(values.get("headers")))
        body = build_request_body(values, runtime)

        auth_type = values.get("auth_type", "none")
        basic_auth = None
        if auth_type == "bearer":
            token = str(values.get("auth_token", "") or "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            basic_auth = (
                str(values.get("auth_username", "") or ""),
                str(values.get("auth_password", "") or ""),
            )

        result = http_request(
            values.get("method", "GET"),
            url,
            headers=headers,
            body=body,
            timeout=values.get("timeout", 10),
            basic_auth=basic_auth,
        )

        status_variable = str(values.get("save_status_to", "") or "")
        body_variable = str(values.get("save_body_to", "") or "")
        headers_variable = str(values.get("save_headers_to", "") or "")
        if runtime is not None:
            if status_variable:
                runtime.vars.set(status_variable, result["status"])
            if body_variable:
                runtime.vars.set(body_variable, result["body"])
            if headers_variable:
                runtime.vars.set(headers_variable, json.dumps(result["headers"]))

        return result


def register_macro(registry):
    registry.register(HttpRequestCommand)
