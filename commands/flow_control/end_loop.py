from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


FlowControlCategory = MacroCommandCategory("flow_control", "Flow Control", "mc:eb92")


class EndLoopCommand(MacroCommand):
    id = "flow_control.end_loop"
    title = "End Loop"
    category = FlowControlCategory
    section = "Loop"
    sort = -99
    hidden = True
    icon = "mc:e5c4"
    description = "End a loop block."
    fields = [
        {
            "name": "loop_id",
            "title": "Loop ID",
            "value_type": "string",
            "default_value": "",
            "required": False,
            "hidden": True,
        }
    ]

    def display_text(self, values=None):
        return "end loop"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        return {
            "action": "end_loop",
            "values": values,
        }


def register_macro(registry):
    registry.register(EndLoopCommand)
