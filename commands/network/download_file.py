import os
import threading

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import (
    USER_AGENT_OPTIONS,
    apply_user_agent,
    download_file,
    parse_header_lines,
    resolve_source,
)


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")


def build_result(state, file_path="", error=""):
    file_name = os.path.basename(file_path)
    result = {
        "state": state,
        "file_path": file_path,
        "file_size": 0,
        "file_name": file_name,
        "extension": os.path.splitext(file_name)[1].lstrip(".").lower(),
    }
    if error:
        result["error"] = str(error)
    return result


def finish_download(url, save_path, timeout, headers, conflict_rule, runtime, variable_name):
    try:
        result = download_file(
            url,
            save_path,
            timeout=timeout,
            headers=headers,
            conflict_rule=conflict_rule,
        )
    except Exception as error:
        result = build_result("failed", save_path, error)

    if variable_name and runtime is not None and hasattr(runtime, "vars"):
        runtime.vars.set(variable_name, result)

    return result


class DownloadFileCommand(MacroCommand):
    id = "network.download_file"
    title = "Download File"
    category = NetworkCategory
    icon = "m:download"
    description = "Download a file from a URL, in the foreground or background, and save the result into a variable."
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
            "place_holder": "https://example.com/file.zip",
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
            "place_holder": "download_url",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "url_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "save_path_source",
            "title": "Save To Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "save_path",
            "title": "Save To Path",
            "place_holder": "C:\\Downloads\\file.zip",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "save_path_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "save_path_variable",
            "title": "Save Path Variable",
            "place_holder": "download_path",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "save_path_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "conflict_rule",
            "title": "If File Exists",
            "value_type": "choice",
            "default_value": "overwrite",
            "options": [
                {
                    "value": "overwrite",
                    "title": "Overwrite",
                },
                {
                    "value": "auto_rename",
                    "title": "Add Number To Name",
                },
            ],
        },
        {
            "name": "download_mode",
            "title": "Download Mode",
            "value_type": "choice",
            "default_value": "wait",
            "options": [
                {
                    "value": "wait",
                    "title": "Wait For Download",
                },
                {
                    "value": "background",
                    "title": "Download In Background",
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
            "name": "timeout_type",
            "title": "Timeout Type",
            "value_type": "choice",
            "default_value": "seconds",
            "options": [
                {
                    "value": "seconds",
                    "title": "Timeout (Seconds)",
                },
                {
                    "value": "never",
                    "title": "Never Timeout",
                },
            ],
        },
        {
            "name": "timeout",
            "title": "Timeout (Seconds)",
            "value_type": "float",
            "default_value": 30,
            "min_value": 1,
            "max_value": 3600,
            "visible_if": {
                "field": "timeout_type",
                "operator": "==",
                "value": "seconds",
            },
        },
        {
            "name": "variable_name",
            "title": "Save Result To Variable",
            "place_holder": "download_result",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        mode = "download in background" if values.get("download_mode") == "background" else "download"
        return f"{mode} {values.get('url')} -> {values.get('save_path')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        url = resolve_source(values, runtime, "url", "URL")
        save_path = resolve_source(values, runtime, "save_path", "Save path")
        headers = apply_user_agent(values, parse_header_lines(values.get("headers")))
        conflict_rule = values.get("conflict_rule", "overwrite")
        variable_name = str(values.get("variable_name", "") or "")

        if values.get("timeout_type", "seconds") == "never":
            timeout = None
        else:
            timeout = values.get("timeout", 30)

        if values.get("download_mode", "wait") == "background":
            result = build_result("downloading", save_path)
            if variable_name and runtime is not None and hasattr(runtime, "vars"):
                runtime.vars.set(variable_name, result)
            thread = threading.Thread(
                target=finish_download,
                args=(url, save_path, timeout, headers, conflict_rule, runtime, variable_name),
                daemon=True,
            )
            thread.start()
            return result

        return finish_download(url, save_path, timeout, headers, conflict_rule, runtime, variable_name)


def register_macro(registry):
    registry.register(DownloadFileCommand)
