from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


FlowControlCategory = MacroCommandCategory("flow_control", "Flow Control", "mc:eb92")


class CommentCommand(MacroCommand):
    id = "flow_control.comment"
    title = "Comment"
    category = FlowControlCategory
    icon = "mc:e867"
    description = "Add a comment."
    fields = [
        {
            "name": "name",
            "title": "Name",
            "place_holder": "Comment text",
            "value_type": "string",
            "default_value": "",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"// {values.get('name')}"

    def execute(self, values=None, runtime=None):
        return None


def register_macro(registry):
    registry.register(CommentCommand)
