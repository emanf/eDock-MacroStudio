import webbrowser

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


SystemCategory = MacroCommandCategory("system", "System", "m:computer")


class OpenUrlCommand(MacroCommand):
    id = "system.open_url"
    title = "Open URL"
    category = SystemCategory
    icon = "m:public"
    description = "Open a URL in the default browser."
    fields = [
        {
            "name": "url",
            "title": "URL",
            "place_holder": "https://example.com",
            "value_type": "string",
            "default_value": "https://",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"open url: {values.get('url')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        url = str(values.get("url", "") or "")
        context = getattr(runtime, "context", None) if runtime is not None else None
        if context is not None and hasattr(context, "open_url"):
            context.open_url(url)
            return None
        if url:
            webbrowser.open(url)
        return None


def register_macro(registry):
    registry.register(OpenUrlCommand)
