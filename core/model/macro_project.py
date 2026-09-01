import re

from .macro_group import MacroGroup


class MacroProject:
    DEFAULT_EXECUTION = {
        "loop_count": 1,
        "speed": 1.0,
        "delay_ms": 0,
        "max_depth": 10,
    }

    def __init__(self, safe_name=None):
        self.safe_name = safe_name if callable(safe_name) else self.default_safe_name
        self.title = "Untitled Project"
        self.name = "untitled_project"
        self.path = None
        self.macros = []
        self.variables = []
        self.execution = self.default_execution()
        self.active_index = -1
        self.saved_data = None

    @staticmethod
    def default_safe_name(value):
        value = str(value or "").strip().lower()
        value = re.sub(r"[^a-z0-9_\-]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value or "untitled_macro"

    @classmethod
    def default_execution(cls):
        return dict(cls.DEFAULT_EXECUTION)

    @classmethod
    def normalize_execution(cls, execution):
        result = cls.default_execution()

        if not isinstance(execution, dict):
            return result

        try:
            result["loop_count"] = max(
                1,
                int(execution.get("loop_count", result["loop_count"])),
            )
        except (TypeError, ValueError):
            pass

        try:
            result["speed"] = max(
                0.05,
                float(execution.get("speed", result["speed"])),
            )
        except (TypeError, ValueError):
            pass

        try:
            result["delay_ms"] = max(
                0,
                int(execution.get("delay_ms", result["delay_ms"])),
            )
        except (TypeError, ValueError):
            pass

        try:
            result["max_depth"] = max(
                1,
                int(execution.get("max_depth", result["max_depth"])),
            )
        except (TypeError, ValueError):
            pass

        return result

    def reset(self):
        self.title = "Untitled Project"
        self.name = "untitled_project"
        self.path = None
        self.variables = []
        self.execution = self.default_execution()
        self.macros = [MacroGroup(name="main", title="Main", items=[], variables=[])]
        self.active_index = 0

    def ensure_main_macro(self):
        if not self.macros:
            self.macros = [
                MacroGroup(name="main", title="Main", items=[], variables=[])
            ]
            return

        self.macros[0].name = "main"
        self.macros[0].title = "Main"

    def active_group(self):
        if 0 <= self.active_index < len(self.macros):
            return self.macros[self.active_index]
        return None

    def unique_macro_title(self, title, exclude_index=None):
        base_title = str(title or "Macro1").strip() or "Macro1"
        existing = set()

        for index, macro in enumerate(self.macros):
            if exclude_index is not None and index == exclude_index:
                continue
            existing.add(
                self.safe_name(
                    getattr(macro, "title", "")
                    or getattr(macro, "name", "")
                )
            )

        base_name = self.safe_name(base_title)
        if base_name not in existing:
            return base_title

        match = re.match(r"^(.*?)(\d+)$", base_title)
        if match:
            prefix = match.group(1)
            number = int(match.group(2)) + 1
        else:
            prefix = base_title
            number = 2

        while True:
            candidate_title = f"{prefix}{number}"
            if self.safe_name(candidate_title) not in existing:
                return candidate_title
            number += 1

    def unique_macro_name(self, title, exclude_index=None):
        safe = self.safe_name(title)
        existing = set()

        for index, macro in enumerate(self.macros):
            if exclude_index is not None and index == exclude_index:
                continue
            existing.add(str(getattr(macro, "name", "") or "").strip())

        if safe not in existing:
            return safe

        match = re.match(
            r"^(.*?)(\d+)$",
            str(title or "Macro1").strip() or "Macro1",
        )
        if match:
            prefix = match.group(1)
            number = int(match.group(2)) + 1
        else:
            prefix = str(title or "Macro").strip() or "Macro"
            number = 2

        while True:
            candidate = self.safe_name(f"{prefix}{number}")
            if candidate not in existing:
                return candidate
            number += 1

    def find_macro_index_by_title(self, title):
        target = str(title or "").strip()
        if not target:
            return -1

        for index, macro in enumerate(self.macros):
            macro_title = str(getattr(macro, "title", "") or "").strip()
            macro_name = str(getattr(macro, "name", "") or "").strip()
            if macro_title == target or macro_name == target:
                return index

        return -1

    def mark_saved(self, data=None):
        self.saved_data = data if data is not None else self.to_data()

    def has_unsaved_changes(self, data=None):
        current = data if data is not None else self.to_data()
        return current != self.saved_data

    def to_data(self, variables=None, execution=None):
        self.ensure_main_macro()

        active_macro = ""
        if 0 <= self.active_index < len(self.macros):
            active_macro = self.macros[self.active_index].name

        return {
            "name": self.name,
            "title": self.title,
            "variables": list(
                variables if variables is not None else self.variables or []
            ),
            "execution": self.normalize_execution(
                execution if execution is not None else self.execution
            ),
            "active_macro": active_macro,
            "macros": [
                {
                    "name": macro.name,
                    "title": macro.title,
                    "items": [
                        item.to_json()
                        for item in macro.items
                        if hasattr(item, "to_json")
                    ],
                }
                for macro in self.macros
            ],
        }
