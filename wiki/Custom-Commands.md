# Custom Commands

Macro Studio can load user commands from:

```text
<eDock app data>/emanf.macro-studio/commands/
```

Each Python module must define `register_macro(registry)` and use the supplied registry to register command classes. A command normally provides an id, title, category, icon, description, fields, and an `execute` method.

A minimal outline looks like this:

```python
from ...core.model.macro_command import MacroCommand


class SayHello(MacroCommand):
    id = "custom.say_hello"
    title = "Say Hello"
    category = "custom"
    description = "Show a small greeting."

    def execute(self, values=None, runtime=None):
        runtime.ui.message("Hello from a custom command")


def register_macro(registry):
    registry.register(SayHello())
```

The exact import path depends on how the module is installed. Use an existing built-in command as the authoritative example for your eDock checkout.

Custom modules execute as application code. Only install commands you trust, and keep a broken module out of the commands directory until it has been tested.
