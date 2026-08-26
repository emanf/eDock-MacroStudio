import subprocess

from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


SystemCategory = MacroCommandCategory("system", "System", "m:computer")


class RunCommandCommand(MacroCommand):
    id = "system.run_command"
    title = "Run Command"
    category = SystemCategory
    icon = "m:terminal"
    description = "Run a system command."
    fields = [
        {
            "name": "command",
            "title": "Command",
            "place_holder": "Command to run",
            "value_type": "string",
            "default_value": "",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"run command: {values.get('command')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        command = str(values.get("command", "") or "")
        context = getattr(runtime, "context", None) if runtime is not None else None
        if context is not None and hasattr(context, "run_command"):
            context.run_command(command)
            return None
        if command:
            subprocess.Popen(command, shell=True)
        return None


def register_macro(registry):
    registry.register(RunCommandCommand)
