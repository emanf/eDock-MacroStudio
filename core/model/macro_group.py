from .macro_item import MacroItem


class MacroGroup:
    def __init__(self, name="", title="", items=None, variables=None):
        self.name = str(name or "").strip()
        self.title = str(title or "").strip() or self.name or "Untitled Macro"
        self.items = items if isinstance(items, list) else []
        self.variables = variables if isinstance(variables, list) else []

    def to_json(self):
        return {
            "name": self.name,
            "title": self.title,
            "variables": [
                {
                    "name": str(variable.get("name", "") or "").strip(),
                    "type": str(variable.get("type", "auto") or "auto").strip() or "auto",
                    "value": variable.get("value", ""),
                }
                for variable in self.variables
                if isinstance(variable, dict) and str(variable.get("name", "") or "").strip()
            ],
            "items": [
                item.to_json()
                for item in self.items
                if hasattr(item, "to_json")
            ],
        }

    @classmethod
    def from_json(cls, data):
        if not isinstance(data, dict):
            return cls()

        items = []
        for raw in data.get("items", []) or []:
            item = MacroItem.from_json(raw)
            if item is not None:
                items.append(item)

        variables = []
        for raw in data.get("variables", []) or []:
            if not isinstance(raw, dict):
                continue

            variable_name = str(raw.get("name", "") or "").strip()
            variable_type = str(raw.get("type", "auto") or "auto").strip() or "auto"
            variable_value = raw.get("value", "")

            if not variable_name:
                continue

            variables.append({
                "name": variable_name,
                "type": variable_type,
                "value": variable_value,
            })

        return cls(
            name=data.get("name", ""),
            title=data.get("title", ""),
            items=items,
            variables=variables,
        )
