from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


FlowControlCategory = MacroCommandCategory("flow_control", "Flow Control", "mc:eb92")


class StopEntireRunCommand(MacroCommand):
    id = "flow_control.stop_entire_run"
    title = "Stop Entire Run"
    category = FlowControlCategory
    icon = "m:stop"
    description = "Stop the entire macro run immediately, including parent and nested macros."
    fields = []

    def display_text(self, values=None):
        return "stop entire run"

    def execute(self, values=None, runtime=None):
        return {"action": "stop_entire_run"}


def register_macro(registry):
    registry.register(StopEntireRunCommand)
