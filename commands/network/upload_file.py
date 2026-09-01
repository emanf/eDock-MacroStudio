import json

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import (
    USER_AGENT_OPTIONS,
    apply_user_agent,
    build_multipart_body,
    http_request,
    parse_header_lines,
    resolve_source,
)


NetworkCategory = MacroCommandCategory("network", "Network", "m:upload")


class UploadFileCommand(MacroCommand):
    id = "network.upload_file"
    title = "Upload File"
    category = NetworkCategory
    icon = "m:upload"
    description = "Upload a file with multipart form-data, like Postman's form-data body."
    result_policy = ResultPolicy.VARIABLE
    fields = [
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
            "place_holder": "https://api.example.com/upload",
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
            "place_holder": "upload_url",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "url_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "file_source",
            "title": "File Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "file_path",
            "title": "File",
            "place_holder": "C:\\Files\\report.pdf",
            "value_type": "file",
            "default_value": "",
            "visible_if": {
                "field": "file_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "file_path_variable",
            "title": "File Path Variable",
            "place_holder": "upload_file_path",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "file_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "file_field_name",
            "title": "File Field Name",
            "place_holder": "file",
            "value_type": "string",
            "default_value": "file",
        },
        {
            "name": "form_fields",
            "title": "Form Fields (One Per Line)",
            "place_holder": "name=value",
            "value_type": "textarea",
            "default_value": "",
            "required": False,
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
            "name": "timeout",
            "title": "Timeout (Seconds)",
            "value_type": "float",
            "default_value": 30,
            "min_value": 1,
            "max_value": 3600,
        },
        {
            "name": "save_status_to",
            "title": "Save Status To Variable",
            "place_holder": "upload_status",
            "value_type": "variable",
            "default_value": "",
        },
        {
            "name": "save_body_to",
            "title": "Save Body To Variable",
            "place_holder": "upload_body",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        url = values.get("url_variable") if values.get("url_source") == "variable" else values.get("url")
        file_path = values.get("file_path_variable") if values.get("file_source") == "variable" else values.get("file_path")
        return f"upload {file_path} -> {url}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        url = resolve_source(values, runtime, "url", "URL")
        file_path = resolve_source(values, runtime, "file_path", "File path")
        headers = apply_user_agent(values, parse_header_lines(values.get("headers")))
        boundary, body = build_multipart_body(
            values.get("form_fields"),
            file_path,
            str(values.get("file_field_name", "file") or "file"),
        )
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

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
            "POST",
            url,
            headers=headers,
            body=body,
            timeout=values.get("timeout", 30),
            basic_auth=basic_auth,
        )

        status_variable = str(values.get("save_status_to", "") or "")
        body_variable = str(values.get("save_body_to", "") or "")
        if runtime is not None:
            if status_variable:
                runtime.vars.set(status_variable, result["status"])
            if body_variable:
                runtime.vars.set(body_variable, result["body"])

        return result


def register_macro(registry):
    registry.register(UploadFileCommand)
