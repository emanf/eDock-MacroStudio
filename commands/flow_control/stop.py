from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


FlowControlCategory = MacroCommandCategory("flow_control", "Flow Control", "mc:eb92")


class StopCommand(MacroCommand):
    id = "flow_control.stop"
    title = "Exit Current Macro"
    category = FlowControlCategory
    icon = "mc:e14b"
    description = "Exit the current macro group and continue in the macro that called it."
    fields = []

    def display_text(self, values=None):
        return "exit current macro"

    def execute(self, values=None, runtime=None):
        return {"action": "exit_current_macro"}


def register_macro(registry):
    registry.register(StopCommand)
