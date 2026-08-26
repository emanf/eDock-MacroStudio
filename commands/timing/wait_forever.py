from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


TimingCategory = MacroCommandCategory("timing", "Timing", "m:timer")


class WaitForeverCommand(MacroCommand):
    id = "timing.wait_forever"
    title = "Wait Forever"
    category = TimingCategory
    icon = "mc:e046"
    description = "Wait until the macro is stopped or a registered hotkey changes execution."
    result_policy = ResultPolicy.CONTROL
    fields = []

    def display_text(self, values=None):
        return "wait forever"

    def execute(self, values=None, runtime=None):
        return {
            "action": "wait_forever",
        }


def register_macro(registry):
    registry.register(WaitForeverCommand)
