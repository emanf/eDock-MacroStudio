from .model.macro_category import CategoryRegistry, MacroCommandCategory


class MacroRegistry:
    LOOP_END_COMMAND_ID = "flow_control.end_loop"
    LOOP_START_COMMAND_IDS = {
        "flow_control.start_loop",
        "flow_control.repeat",
        "flow_control.repeat_while",
        "flow_control.for_each",
    }

    def __init__(self):
        self._commands = {}
        self._categories = {}
        self._category_registry = CategoryRegistry()
        self.macros_provider = None

    def set_macros_provider(self, callback):
        self.macros_provider = callback if callable(callback) else None

    def macro_group_title(self, name):
        target = str(name or "").strip()
        if not target or not callable(self.macros_provider):
            return ""

        for macro in self.macros_provider() or []:
            if str(getattr(macro, "name", "") or "").strip() == target:
                return str(getattr(macro, "title", "") or "").strip()

        return ""

    def register_category(self, category):
        if isinstance(category, MacroCommandCategory):
            return self._category_registry.register(category)

        text = str(category or "").strip()
        if not text:
            return None

        return self._category_registry.register(
            MacroCommandCategory(text, text, "m:extension")
        )

    def command_category(self, command):
        category = getattr(command, "category", None)

        if isinstance(category, MacroCommandCategory):
            self._category_registry.register(category)
            return self._category_registry.get(category.id)

        text = str(category or "").strip()
        if not text:
            return None

        self._category_registry.register(
            MacroCommandCategory(text, text, "m:extension")
        )
        return self._category_registry.get(text)

    def register(self, command):
        if isinstance(command, type):
            command = command()

        command_id = str(getattr(command, "id", "") or "").strip()
        category = self.command_category(command)

        if not command_id:
            raise ValueError("Macro command id is required")

        if category is None or not category.id:
            raise ValueError("Macro command category is required")

        category_id = str(category.id or "").strip().lower()

        command.registry = self
        self._commands[command_id] = command
        self._categories.setdefault(category_id, [])
        if command_id not in self._categories[category_id]:
            self._categories[category_id].append(command_id)

        return command

    def unregister(self, command_id):
        command_id = str(command_id or "").strip()
        if not command_id:
            return False

        command = self._commands.pop(command_id, None)
        if command is None:
            return False

        for category, items in self._categories.items():
            if command_id in items:
                items.remove(command_id)

        return True

    def get(self, command_id):
        return self._commands.get(str(command_id or "").strip())

    def has(self, command_id):
        return self.get(command_id) is not None

    def all(self):
        return list(self._commands.values())

    def categories(self):
        category_ids = [c for c in self._categories.keys() if c and self._categories.get(c)]
        category_ids.sort(key=lambda cid: self.category_title(cid).lower())
        return [self.category_info(cid) for cid in category_ids if self.category_info(cid) is not None]

    def category_info(self, category):
        return self._category_registry.get(category)

    def category_title(self, category):
        return self.category_info(category).title

    def category_icon(self, category):
        return self.category_info(category).icon

    def category_commands(self, category):
        category_info = self.category_info(category)
        category_id = str(category_info.id or "").strip().lower()
        ids = self._categories.get(category_id, [])
        return [self._commands[i] for i in ids if i in self._commands]

    def item_command_id(self, item):
        if isinstance(item, dict):
            return str(item.get("command_id", "") or "").strip()
        return str(getattr(item, "command_id", "") or "").strip()

    def item_values(self, item):
        if isinstance(item, dict):
            values = item.get("values", {})
        else:
            values = getattr(item, "values", {})

        if isinstance(values, dict):
            return values

        return {}

    def command_display_text(self, item):
        command = self.get(self.item_command_id(item))
        if command is None:
            return "Unknown macro"

        values = self.item_values(item)

        try:
            text = command.display_text(values)
        except Exception:
            text = ""

        text = str(text if text is not None else "").strip()

        if text:
            return text

        return command.title

    def command_icon(self, command_id):
        command = self.get(command_id)
        if command is None:
            return ""
        return str(getattr(command, "icon", "") or "")

    def is_loop_start_command(self, command_id):
        return str(command_id or "").strip() in self.LOOP_START_COMMAND_IDS

    def is_loop_end_command(self, command_id):
        return str(command_id or "").strip() == self.LOOP_END_COMMAND_ID

    def create_loop_end_item(self, loop_id=""):
        command = self.get(self.LOOP_END_COMMAND_ID)
        if command is None:
            return None
        return command.create_item({"loop_id": str(loop_id or "").strip()})
