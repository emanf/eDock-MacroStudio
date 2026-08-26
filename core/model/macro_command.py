import platform
from enum import Enum

from .macro_category import MacroCommandCategory


class ResultPolicy(Enum):
    NONE = "none"
    DATA = "data"
    CONDITION = "condition"
    VARIABLE = "variable"
    CONTROL = "control"


class MacroCommand:
    id = ""
    title = ""
    category = None
    section = ""
    sort = 0
    hidden = False
    icon = ""
    description = ""
    fields = []
    result_policy = ResultPolicy.NONE
    os = None

    def __init__(self):
        if not self.id:
            raise ValueError("Macro command id is required")
        if not self.title:
            raise ValueError("Macro command title is required")
        if not self.category:
            raise ValueError("Macro command category is required")
        if not isinstance(self.category, MacroCommandCategory):
            text = str(self.category or "").strip()
            self.category = MacroCommandCategory(text, text, "m:extension")
        if not self.category.id:
            raise ValueError("Macro command category id is required")
        if not self.category.title:
            self.category.title = self.category.id
        if not self.category.icon:
            self.category.icon = "m:extension"
        if not self.icon:
            self.icon = "m:extension"

        self.section = str(self.section or "").strip()
        self.hidden = bool(self.hidden)

        if isinstance(self.sort, bool) or not isinstance(self.sort, (int, float)):
            raise ValueError("Macro command sort must be a number")

        if not isinstance(self.result_policy, ResultPolicy):
            raise ValueError("Macro command result_policy must be a ResultPolicy")

    def category_id(self):
        return self.category.normalized_id()

    def category_title(self):
        return self.category.title

    def category_icon(self):
        return self.category.icon

    def command_icon(self):
        return self.icon

    def section_title(self):
        return self.section

    def sort_order(self):
        return self.sort

    def is_hidden(self):
        return self.hidden

    def is_supported_os(self):
        if not self.os:
            return True

        current = platform.system().lower()
        allowed_os = self.os
        if isinstance(allowed_os, str):
            allowed_os = [allowed_os.lower()]
        elif isinstance(allowed_os, list):
            allowed_os = [str(o).lower() for o in allowed_os]
        else:
            return True

        mapping = {
            "windows": "windows", "win": "windows",
            "linux": "linux",
            "macos": "darwin", "mac": "darwin", "darwin": "darwin"
        }
        normalized_allowed = [mapping.get(o, o) for o in allowed_os]
        return current in normalized_allowed

    def schema(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category_id(),
            "category_title": self.category_title(),
            "category_icon": self.category_icon(),
            "section": self.section_title(),
            "sort": self.sort_order(),
            "hidden": self.is_hidden(),
            "icon": self.command_icon(),
            "description": self.description,
            "fields": list(self.fields or []),
            "result_policy": self.result_policy.value,
            "os": self.os,
        }

    def default_values(self):
        values = {}

        for field in self.fields or []:
            name = str(field.get("name", "")).strip()

            if not name:
                continue

            values[name] = field.get("default_value", "")

        return values

    def normalize_values(self, values):
        result = self.default_values()

        if isinstance(values, dict):
            result.update(values)

        return result

    def display_text(self, values=None):
        return self.title

    def create_item(self, values=None):
        from .macro_item import MacroItem

        return MacroItem(
            command_id=self.id,
            values=self.normalize_values(values or {}),
        )

    def execute(self, values=None, runtime=None):
        return None
