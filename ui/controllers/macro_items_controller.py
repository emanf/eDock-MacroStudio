from copy import deepcopy

from PySide6.QtCore import QObject

from ...core import refactor
from ..forms.form_builder import FormBuilder

COMMENT_COMMAND_ID = "flow_control.comment"


class MacroItemsController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.project = window.project
        self.messages = window.messages
        self.clipboard_item = None
        self.history_map = {}
        self.max_history = 50

    def is_busy(self):
        return self.window.run_controller.is_busy()

    def _active_macro(self):
        active_index = self.project.active_index
        if 0 <= active_index < len(self.project.macros):
            return self.project.macros[active_index]
        return None

    def _get_history_key(self):
        macro = self._active_macro()
        if macro is None:
            return None
        return id(macro)

    def _get_current_history(self):
        key = self._get_history_key()
        if not key:
            return {"snapshots": [], "index": -1}

        if key not in self.history_map:
            self.history_map[key] = {"snapshots": [], "index": -1}

        return self.history_map[key]

    def _same_items_state(self, first, second):
        if not first or not second:
            return False
        return first.get("items_data", []) == second.get("items_data", [])

    def initialize_baseline_state(self):
        key = self._get_history_key()
        if not key:
            return

        state = self.window.macro_list.capture_state()
        if key not in self.history_map:
            self.history_map[key] = {
                "snapshots": [deepcopy(state)],
                "index": 0
            }
        else:
            hist = self.history_map[key]
            if not hist["snapshots"]:
                hist["snapshots"] = [deepcopy(state)]
                hist["index"] = 0

    def begin_history_transaction(self):
        return self.window.macro_list.capture_state()

    def commit_history_transaction(self, before_state):
        if not before_state:
            return False

        after_state = self.window.macro_list.capture_state()
        if self._same_items_state(before_state, after_state):
            return False

        hist = self._get_current_history()
        idx = hist["index"]

        if idx >= 0 and idx < len(hist["snapshots"]):
            hist["snapshots"] = hist["snapshots"][:idx + 1]

        hist["snapshots"].append(deepcopy(after_state))
        hist["index"] = len(hist["snapshots"]) - 1

        while len(hist["snapshots"]) > self.max_history:
            hist["snapshots"].pop(0)
            hist["index"] -= 1

        return True

    def get_history_availability(self):
        hist = self._get_current_history()
        snapshots = hist["snapshots"]
        idx = hist["index"]
        return idx > 0, idx < len(snapshots) - 1

    def record_state(self):
        state = self.window.macro_list.capture_state()
        hist = self._get_current_history()
        idx = hist["index"]

        if idx >= 0 and idx < len(hist["snapshots"]):
            if self._same_items_state(hist["snapshots"][idx], state):
                return False
            hist["snapshots"] = hist["snapshots"][:idx + 1]

        hist["snapshots"].append(deepcopy(state))
        hist["index"] = len(hist["snapshots"]) - 1

        while len(hist["snapshots"]) > self.max_history:
            hist["snapshots"].pop(0)
            hist["index"] -= 1

        return True

    def sync_history_before_switch(self):
        pass

    def undo(self):
        hist = self._get_current_history()
        idx = hist["index"]

        if idx <= 0:
            return

        hist["index"] = idx - 1
        previous_state = hist["snapshots"][hist["index"]]
        self.window.macro_list.apply_state(previous_state)
        self.sync_items_to_group()

    def redo(self):
        hist = self._get_current_history()
        idx = hist["index"]
        snapshots = hist["snapshots"]

        if idx >= len(snapshots) - 1:
            return

        hist["index"] = idx + 1
        next_state = snapshots[hist["index"]]
        self.window.macro_list.apply_state(next_state)
        self.sync_items_to_group()

    def sync_items_to_group(self):
        group = self.project.active_group()
        if group is not None:
            group.items = self.window.macro_list.items_data

    def command_requires_dialog(self, command):
        if command is None:
            return False
        if hasattr(command, "is_supported_os") and not command.is_supported_os():
            return False
        return len(list(command.fields or [])) > 0

    def is_loop_start_command(self, command_id):
        return self.window.registry.is_loop_start_command(command_id)

    def is_loop_end_command(self, command_id):
        return self.window.registry.is_loop_end_command(command_id)

    def create_loop_end_item(self, loop_id=""):
        return self.window.registry.create_loop_end_item(loop_id)

    def add_macro_item_from_command(self, command, data=None, index=None):
        if self.project.active_index < 0:
            self.project.ensure_main_macro()
            self.project.active_index = 0
            self.window.refresh_macro_tabs()
            self.window.load_active_macro_to_ui()

        before_state = self.begin_history_transaction()

        values = command.normalize_values(data or {})
        item = command.create_item(values)

        if index is None:
            insert_index = len(self.window.macro_list.items_data)
        else:
            insert_index = max(0, min(int(index), len(self.window.macro_list.items_data)))

        if index is None:
            self.window.macro_list.add_macro_item(item, self.window.registry)
        else:
            self.window.macro_list.insert_macro_item(insert_index, item, self.window.registry)

        if self.is_loop_start_command(getattr(command, "id", "")):
            end_item = self.create_loop_end_item(str((values or {}).get("loop_id", "") or "").strip())
            if end_item is not None:
                self.window.macro_list.insert_macro_item(insert_index + 1, end_item, self.window.registry)

        self.sync_items_to_group()
        self.commit_history_transaction(before_state)

    def add_macro_by_id(self, command_id):
        self.add_macro_by_id_at(command_id, None)

    def add_macro_by_id_at(self, command_id, index=None):
        command = self.window.registry.get(command_id)
        if command is None:
            self.messages.show_warning("Unknown Macro", "This macro command is not registered.")
            return

        if hasattr(command, "is_supported_os") and not command.is_supported_os():
            self.messages.show_warning("Unsupported Macro", "This macro command does not support the current operating system.")
            return

        if not self.command_requires_dialog(command):
            self.add_macro_item_from_command(command, command.default_values(), index=index)
            return

        data = FormBuilder.get_data(
            schema={
                "title": command.title,
                "submit_text": "Add",
                "fields": command.fields,
            },
            values=command.default_values(),
            parent=self.window,
            runtime_variables=self.window.collect_defined_variables(),
            runtime_comments=self.collect_defined_comments(),
        )

        if data is None:
            return

        self.add_macro_item_from_command(command, data, index=index)

    def edit_macro_item(self, index):
        if self.is_busy():
            return

        if index < 0 or index >= len(self.window.macro_list.items_data):
            return

        item = self.window.macro_list.items_data[index]
        command = self.window.registry.get(item.command_id)
        if command is None:
            self.messages.show_warning("Unknown Macro", "This command does not exist.")
            return

        if hasattr(command, "is_supported_os") and not command.is_supported_os():
            self.messages.show_warning("Unsupported Macro", "This command is not supported on your operating system.")
            return

        if not self.command_requires_dialog(command):
            return

        before_state = self.begin_history_transaction()

        data = FormBuilder.get_data(
            schema={
                "title": command.title,
                "submit_text": "Save",
                "fields": command.fields,
            },
            values=item.values,
            parent=self.window,
            runtime_variables=self.window.collect_defined_variables(),
            runtime_comments=self.collect_defined_comments(exclude_index=index),
        )

        if data is None:
            return

        old_comment_name = ""
        if item.command_id == COMMENT_COMMAND_ID:
            old_comment_name = str((item.values or {}).get("name", "") or "").strip()

        old_loop_id = ""
        if self.is_loop_start_command(item.command_id):
            old_loop_id = str((item.values or {}).get("loop_id", "") or "").strip()

        item.values = data
        self.window.macro_list.update_macro_item(index, item, self.window.registry)

        if self.is_loop_start_command(item.command_id):
            new_loop_id = str((data or {}).get("loop_id", "") or "").strip()
            if old_loop_id != new_loop_id:
                end_index = self.find_paired_loop_end_index(index)
                if end_index is not None:
                    end_item = self.window.macro_list.items_data[end_index]
                    end_values = dict(getattr(end_item, "values", {}) or {})
                    end_values["loop_id"] = new_loop_id
                    end_item.values = end_values
                    self.window.macro_list.update_macro_item(end_index, end_item, self.window.registry)

        self.sync_items_to_group()

        if item.command_id == COMMENT_COMMAND_ID:
            new_comment_name = str(data.get("name", "") or "").strip()
            if old_comment_name and new_comment_name and old_comment_name != new_comment_name:
                count = refactor.rename_comment_references(
                    self.window.macro_list.items_data,
                    self.window.registry,
                    old_comment_name,
                    new_comment_name,
                )
                if count:
                    self.window.macro_list.refresh(restore_scroll=True)
                    self.sync_items_to_group()
                    self.messages.show_information(
                        "Comment Renamed",
                        f"Updated {count} jump reference(s) to '{old_comment_name}' in this macro.",
                    )

        self.commit_history_transaction(before_state)

    def toggle_item_enabled(self, index):
        if self.is_busy():
            return

        if index < 0 or index >= len(self.window.macro_list.items_data):
            return

        before_state = self.begin_history_transaction()
        item = self.window.macro_list.items_data[index]
        item.enabled = not bool(getattr(item, "enabled", True))
        self.window.macro_list.refresh(restore_scroll=True)
        self.window.macro_list.setCurrentRow(index)
        self.sync_items_to_group()
        self.commit_history_transaction(before_state)

    def normalize_item_rows(self, rows):
        if isinstance(rows, int):
            rows = [rows]
        elif rows is None:
            rows = []
        else:
            rows = list(rows)

        normalized = []

        for row in rows:
            try:
                row = int(row)
            except Exception:
                continue

            if row < 0 or row >= len(self.window.macro_list.items_data):
                continue

            normalized.append(row)

        return sorted(set(normalized))

    def find_paired_loop_end_index(self, start_index):
        items = self.window.macro_list.items_data

        if start_index < 0 or start_index >= len(items):
            return None

        start_item = items[start_index]
        if not self.is_loop_start_command(getattr(start_item, "command_id", "")):
            return None

        depth = 0

        for index in range(start_index + 1, len(items)):
            item = items[index]
            command_id = getattr(item, "command_id", "")

            if self.is_loop_start_command(command_id):
                depth += 1
                continue

            if self.is_loop_end_command(command_id):
                if depth == 0:
                    return index
                depth -= 1

        return None

    def find_paired_loop_start_index(self, end_index):
        items = self.window.macro_list.items_data

        if end_index < 0 or end_index >= len(items):
            return None

        end_item = items[end_index]
        if not self.is_loop_end_command(getattr(end_item, "command_id", "")):
            return None

        depth = 0

        for index in range(end_index - 1, -1, -1):
            item = items[index]
            command_id = getattr(item, "command_id", "")

            if self.is_loop_end_command(command_id):
                depth += 1
                continue

            if self.is_loop_start_command(command_id):
                if depth == 0:
                    return index
                depth -= 1

        return None

    def expand_rows_with_loop_pairs(self, rows):
        rows = self.normalize_item_rows(rows)
        if not rows:
            return []

        expanded = set(rows)

        changed = True
        while changed:
            changed = False
            current_rows = sorted(expanded)

            for row in current_rows:
                item = self.window.macro_list.items_data[row]
                command_id = getattr(item, "command_id", "")

                if self.is_loop_start_command(command_id):
                    pair_index = self.find_paired_loop_end_index(row)
                    if pair_index is not None and pair_index not in expanded:
                        expanded.add(pair_index)
                        changed = True

                elif self.is_loop_end_command(command_id):
                    pair_index = self.find_paired_loop_start_index(row)
                    if pair_index is not None and pair_index not in expanded:
                        expanded.add(pair_index)
                        changed = True

        return sorted(expanded)

    def delete_item(self):
        if self.is_busy():
            return

        current_row = self.window.macro_list.currentRow()
        if current_row < 0:
            return

        before_state = self.begin_history_transaction()
        rows = self.expand_rows_with_loop_pairs([current_row])
        if not rows:
            return

        self.window.macro_list.remove_rows_at(rows, self.window.registry)
        self.sync_items_to_group()
        self.commit_history_transaction(before_state)

    def delete_item_at(self, rows):
        if self.is_busy():
            return

        before_state = self.begin_history_transaction()
        rows = self.expand_rows_with_loop_pairs(rows)
        if not rows:
            return

        self.window.macro_list.remove_rows_at(rows, self.window.registry)
        self.sync_items_to_group()
        self.commit_history_transaction(before_state)

    def copy_item_at(self, rows):
        rows = self.normalize_item_rows(rows)
        if not rows:
            return

        items = self.window.macro_list.get_items_at(rows)
        if not items:
            return

        if len(items) == 1:
            self.clipboard_item = deepcopy(items[0])
            return

        self.clipboard_item = deepcopy(items)

    def cut_item_at(self, rows):
        if self.is_busy():
            return

        before_state = self.begin_history_transaction()
        rows = self.expand_rows_with_loop_pairs(rows)
        if not rows:
            return

        items = self.window.macro_list.get_items_at(rows)
        if not items:
            return

        if len(items) == 1:
            self.clipboard_item = deepcopy(items[0])
        else:
            self.clipboard_item = deepcopy(items)

        self.window.macro_list.remove_rows_at(rows, self.window.registry)
        self.sync_items_to_group()
        self.commit_history_transaction(before_state)

    def paste_item_at(self, row):
        if self.is_busy():
            return

        if self.clipboard_item is None:
            return

        before_state = self.begin_history_transaction()

        if row >= 0:
            insert_index = row + 1
        else:
            insert_index = len(self.window.macro_list.items_data)

        if isinstance(self.clipboard_item, list):
            for item in self.clipboard_item:
                self.window.macro_list.insert_macro_item(insert_index, deepcopy(item), self.window.registry)
                insert_index += 1
        else:
            self.window.macro_list.insert_macro_item(
                insert_index,
                deepcopy(self.clipboard_item),
                self.window.registry,
            )

        self.sync_items_to_group()
        self.commit_history_transaction(before_state)

    def move_item_up(self):
        if self.is_busy():
            return

        before_state = self.begin_history_transaction()
        changed = self.window.macro_list.move_current_up(self.window.registry)

        if changed:
            self.sync_items_to_group()
            self.commit_history_transaction(before_state)

    def move_item_down(self):
        if self.is_busy():
            return

        before_state = self.begin_history_transaction()
        changed = self.window.macro_list.move_current_down(self.window.registry)

        if changed:
            self.sync_items_to_group()
            self.commit_history_transaction(before_state)

    def collect_defined_comments(self, exclude_index=None):
        comments = []

        for index, item in enumerate(self.window.macro_list.items_data):
            if exclude_index is not None and index == exclude_index:
                continue

            if getattr(item, "command_id", "") != "flow_control.comment":
                continue

            values = getattr(item, "values", {}) or {}
            comment_name = str(values.get("name", "") or "").strip()
            if comment_name and comment_name not in comments:
                comments.append(comment_name)

        return comments
