from ...core.model.macro_command import MacroCommand
from ...core.model.macro_category import MacroCommandCategory


FlowControlCategory = MacroCommandCategory("flow_control", "Flow Control", "mc:eb92")


class JumpToCommentCommand(MacroCommand):
    id = "flow_control.jump_to_comment"
    title = "Jump To Comment"
    category = FlowControlCategory
    icon = "mc:e5da"
    description = "Jump macro execution to a comment."
    fields = [
        {
            "name": "comment",
            "title": "Comment",
            "place_holder": "Select a comment",
            "value_type": "comment",
            "default_value": "",
        }
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"jump to comment {values.get('comment')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        return {
            "action": "jump_to_comment",
            "comment": values.get("comment", ""),
        }


def register_macro(registry):
    registry.register(JumpToCommentCommand)
