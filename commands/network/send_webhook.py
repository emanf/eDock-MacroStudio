import json

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy

from ._net_utils import (
    USER_AGENT_OPTIONS,
    apply_user_agent,
    build_webhook_payload,
    http_request,
    parse_header_lines,
    resolve_source,
)


NetworkCategory = MacroCommandCategory("network", "Network", "m:hub")


class SendWebhookCommand(MacroCommand):
    id = "network.send_webhook"
    title = "Send Webhook"
    category = NetworkCategory
    icon = "m:bolt"
    description = "Send a webhook message with Discord, Slack, or Telegram formatting."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "style",
            "title": "Style",
            "value_type": "choice",
            "default_value": "generic",
            "options": [
                {
                    "value": "generic",
                    "title": "Generic",
                },
                {
                    "value": "discord",
                    "title": "Discord",
                },
                {
                    "value": "slack",
                    "title": "Slack",
                },
                {
                    "value": "telegram",
                    "title": "Telegram",
                },
            ],
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
            "title": "Webhook URL",
            "place_holder": "https://discord.com/api/webhooks/...",
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
            "title": "Webhook URL Variable",
            "place_holder": "webhook_url",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "url_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "message_source",
            "title": "Message Source",
            "value_type": "choice",
            "default_value": "value",
            "options": ["value", "variable"],
        },
        {
            "name": "message",
            "title": "Message",
            "place_holder": "Macro finished successfully",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "message_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "message_variable",
            "title": "Message Variable",
            "place_holder": "webhook_message",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "message_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "title",
            "title": "Title",
            "place_holder": "Macro Studio",
            "value_type": "string",
            "default_value": "",
            "required": False,
        },
        {
            "name": "username",
            "title": "Bot Username",
            "place_holder": "Macro Studio Bot",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "visible_if": {
                "field": "style",
                "operator": "==",
                "value": "discord",
            },
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
            "name": "timeout",
            "title": "Timeout (Seconds)",
            "value_type": "float",
            "default_value": 10,
            "min_value": 0.5,
            "max_value": 3600,
        },
        {
            "name": "variable_name",
            "title": "Save Status To Variable",
            "place_holder": "webhook_status",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        url = values.get("url_variable") if values.get("url_source") == "variable" else values.get("url")
        return f"send {values.get('style')} webhook to {url}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        url = resolve_source(values, runtime, "url", "URL")
        message = resolve_source(values, runtime, "message", "Message")
        headers = apply_user_agent(values, parse_header_lines(values.get("headers")))
        payload = build_webhook_payload(
            values.get("style"),
            message,
            values.get("title"),
            values.get("username"),
        )
        result = http_request(
            "POST",
            url,
            headers={"Content-Type": "application/json", **headers},
            body=json.dumps(payload),
            timeout=values.get("timeout", 10),
        )

        variable_name = str(values.get("variable_name", "") or "")
        if variable_name and runtime is not None:
            runtime.vars.set(variable_name, result["status"])

        return result


def register_macro(registry):
    registry.register(SendWebhookCommand)
