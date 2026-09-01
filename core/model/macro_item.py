class MacroItem:
    def __init__(self, command_id, values=None, enabled=True):
        self.command_id = str(command_id or "").strip()
        self.values = values if isinstance(values, dict) else {}
        self.enabled = bool(enabled)

    def to_json(self):
        return {
            "command_id": self.command_id,
            "values": dict(self.values or {}),
            "enabled": self.enabled,
        }

    @classmethod
    def from_json(cls, data):
        if not isinstance(data, dict):
            return None

        command_id = str(data.get("command_id", "") or "").strip()
        if not command_id:
            return None

        return cls(
            command_id=command_id,
            values=data.get("values", {}) if isinstance(data.get("values"), dict) else {},
            enabled=bool(data.get("enabled", True)),
        )
