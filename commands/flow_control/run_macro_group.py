from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory

FlowControlCategory = MacroCommandCategory("flow_control", "Flow Control", "mc:eb92")

class RunMacroGroupCommand(MacroCommand):
    id = "flow_control.run_macro_group"
    title = "Run Macro Group"
    category = FlowControlCategory
    icon = "mc:eae7"
    description = "Run another macro group as a subroutine and return here when finished."
    result_policy = ResultPolicy.CONTROL
    fields = [
        {
            "name": "target",
            "title": "Macro Group",
            "value_type": "macro_group",
            "default_value": "",
            "placeholder": "Select a macro group to run",
            "required": True,
        },
        {
            "name": "run_in_background",
            "title": "Run in Background",
            "value_type": "bool",
            "default_value": True,
            "required": False,
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target = values.get("target", "")
        run_in_background = bool(values.get("run_in_background", False))

        if isinstance(target, dict):
            title = target.get("title", "")
            value = target.get("value", "")
            target_text = title or value
        else:
            target_text = target

        if run_in_background:
            return f"run macro group '{target_text}' in background"

        return f"run macro group '{target_text}'"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target = values.get("target", "")
        run_in_background = bool(values.get("run_in_background", False))

        if isinstance(target, dict):
            target = target.get("value", "")

        if not target:
            raise ValueError("No macro group target specified.")

        return {
            "action": "run_macro_group",
            "target": target,
            "run_in_background": run_in_background,
        }


def register_macro(registry):
    registry.register(RunMacroGroupCommand)
