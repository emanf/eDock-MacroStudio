import json
import time
from collections.abc import Iterable


LOOP_OPERATOR_VALUES = {
    "Equals (==)": "==",
    "Not Equals (!=)": "!=",
    "Greater Than (>)": ">",
    "Less Than (<)": "<",
    "Greater Than or Equal (>=)": ">=",
    "Less Than or Equal (<=)": "<=",
    "Contains": "contains",
    "Does Not Contain": "not contains",
    "Starts With": "starts with",
    "Ends With": "ends with",
    "Is True": "is true",
    "Is False": "is false",
}


def normalize_loop_operator(operator):
    return LOOP_OPERATOR_VALUES.get(operator, operator)


class MacroExecutor:
    def __init__(
        self,
        items,
        registry,
        runtime,
        group_library=None,
        group_titles=None,
        loop_count=1,
        delay_ms=0,
        max_depth=10,
        on_step=None,
        on_group_started=None,
        on_group_finished=None,
    ):
        self.items = list(items or [])
        self.registry = registry
        self.runtime = runtime
        self.group_library = group_library or {}
        self.group_titles = group_titles or {}
        self.loop_count = max(1, int(loop_count or 1))
        self.delay_ms = max(0, int(delay_ms or 0))
        self.max_depth = max(1, int(max_depth or 10))
        self.on_step = on_step if callable(on_step) else lambda index: None
        self.on_group_started = (
            on_group_started
            if callable(on_group_started)
            else lambda title: None
        )
        self.on_group_finished = (
            on_group_finished
            if callable(on_group_finished)
            else lambda title: None
        )
        self.stopped = False
        self.paused = False
        self.exit_current_macro_requested = False
        self.hotkey_events = []
        self.timer_events = []
        self.registered_hotkeys = set()
        self.registered_timers = set()

    def stop(self):
        self.stopped = True
        self.paused = False

    def pause(self):
        if not self.stopped:
            self.paused = True

    def resume(self):
        self.paused = False

    def is_paused(self):
        return self.paused

    def exit_current_macro(self):
        if not self.stopped:
            self.exit_current_macro_requested = True
            self.paused = False

    def wait_if_paused(self):
        while self.paused and not self.stopped:
            time.sleep(0.03)

    def sleep(self, seconds):
        end = time.time() + max(0, float(seconds or 0))

        while time.time() < end:
            if self.stopped:
                return

            self.wait_if_paused()
            self.poll_timer_events()
            time.sleep(0.03)

    def sleep_line_delay(self):
        if self.delay_ms > 0:
            self.sleep(self.delay_ms / 1000)

    def get_comment_position(self, items, name):
        comment_name = str(name or "").strip()

        if not comment_name:
            return None

        for index, item in enumerate(items):
            if getattr(item, "command_id", "") == "flow_control.comment":
                values = getattr(item, "values", {}) or {}

                if str(values.get("name", "") or "").strip() == comment_name:
                    return index

        return None

    def resolve_group_target(self, target_name):
        target = str(target_name or "").strip()

        if not target:
            return ""

        if target in self.group_library:
            return target

        for key, title in self.group_titles.items():
            if str(title or "").strip() == target:
                return key

        return ""

    def get_group_display_title(self, target_name):
        target = str(target_name or "").strip()

        if not target:
            return ""

        resolved_target = self.resolve_group_target(target)

        if resolved_target:
            return str(
                self.group_titles.get(resolved_target, resolved_target)
                or resolved_target
            )

        return target

    def finish_current_frame(self, call_stack):
        if not call_stack:
            return None

        frame = call_stack.pop()
        finished_title = str(frame.get("display_title", "") or "").strip()

        if frame.get("emit_finish") and finished_title:
            self.on_group_finished(finished_title)

        return frame

    def handle_exit_current_macro_request(self, call_stack, recursion_depth):
        if not self.exit_current_macro_requested:
            return recursion_depth

        self.exit_current_macro_requested = False
        finished_frame = self.finish_current_frame(call_stack)

        if finished_frame and finished_frame.get("emit_finish"):
            recursion_depth -= 1

        if not call_stack:
            self.stopped = True

        return recursion_depth

    def execute_command(self, command, values):
        return command.execute(values=values, runtime=self.runtime)

    def register_hotkey(self, registration):
        hotkey_id = str(registration.get("id", "") or "").strip()

        if not hotkey_id or hotkey_id in self.registered_hotkeys:
            return

        register = getattr(self.runtime, "register_global_hotkey", None)

        if not callable(register):
            raise RuntimeError("Runtime does not support global hotkeys")

        register(registration)
        self.registered_hotkeys.add(hotkey_id)

    def register_timer(self, registration):
        timer_id = str(registration.get("id", "") or "").strip()

        if not timer_id or timer_id in self.registered_timers:
            return

        register = getattr(self.runtime, "register_global_timer", None)

        if not callable(register):
            raise RuntimeError("Runtime does not support global timers")

        register(registration)
        self.registered_timers.add(timer_id)

    def queue_hotkey_event(self, event):
        if isinstance(event, dict):
            self.hotkey_events.append(dict(event))

    def queue_timer_event(self, event):
        if isinstance(event, dict):
            self.timer_events.append(dict(event))

    def pop_event(self):
        if self.hotkey_events:
            return self.hotkey_events.pop(0)

        if self.timer_events:
            return self.timer_events.pop(0)

        return None

    def set_runtime_variable(self, name, value):
        variable_name = str(name or "").strip()

        if not variable_name:
            return

        variables = getattr(self.runtime, "vars", None)
        setter = getattr(variables, "set", None)

        if callable(setter):
            setter(variable_name, value)

    def get_runtime_variable(self, name):
        variables = getattr(self.runtime, "vars", None)
        getter = getattr(variables, "get", None)

        if callable(getter):
            return getter(name)

        return None

    def get_runtime_variable_type(self, name):
        variables = getattr(self.runtime, "vars", None)
        type_of = getattr(variables, "type_of", None)

        if callable(type_of):
            return type_of(name)

        return "string"

    def convert_runtime_value(self, value, value_type):
        helper = getattr(self.runtime, "helper", None)
        converter = getattr(helper, "convert_variable_value", None)

        if callable(converter):
            return converter(value, value_type)

        return value

    def compare_runtime_values(self, left, operator, right):
        helper = getattr(self.runtime, "helper", None)
        comparer = getattr(helper, "compare_values", None)

        if callable(comparer):
            return comparer(left, operator, right)

        normalized_operator = normalize_loop_operator(operator)

        if normalized_operator == "==":
            return left == right

        if normalized_operator == "!=":
            return left != right

        if normalized_operator == ">":
            return left > right

        if normalized_operator == "<":
            return left < right

        if normalized_operator == ">=":
            return left >= right

        if normalized_operator == "<=":
            return left <= right

        if normalized_operator == "contains":
            return str(right) in str(left)

        if normalized_operator == "not contains":
            return str(right) not in str(left)

        if normalized_operator == "starts with":
            return str(left).startswith(str(right))

        if normalized_operator == "ends with":
            return str(left).endswith(str(right))

        if normalized_operator == "is true":
            return bool(left) is True

        if normalized_operator == "is false":
            return bool(left) is False

        return False

    def normalize_loop_dict_items(self, value):
        if (
            "items" in value
            and isinstance(value.get("items"), Iterable)
            and not isinstance(
                value.get("items"),
                (str, bytes, bytearray, dict),
            )
        ):
            return list(value.get("items"))

        if "items" in value and isinstance(value.get("items"), dict):
            return list(value.get("items").values())

        return list(value.values())

    def normalize_loop_text_items(self, value, delimiter):
        text = str(value or "").strip()

        if not text:
            return []

        try:
            parsed_value = json.loads(text)
        except Exception:
            parsed_value = None

        if parsed_value is not None:
            return self.normalize_loop_items(parsed_value, delimiter)

        separator = str(delimiter or ",") or ","
        return [item.strip() for item in text.split(separator) if item.strip()]

    def normalize_loop_items(self, value, delimiter):
        if value is None:
            return []

        if isinstance(value, dict):
            return self.normalize_loop_dict_items(value)

        if isinstance(value, str):
            return self.normalize_loop_text_items(value, delimiter)

        if isinstance(value, (bytes, bytearray)):
            try:
                return self.normalize_loop_text_items(
                    value.decode("utf-8"),
                    delimiter,
                )
            except Exception:
                return [value]

        if isinstance(value, Iterable):
            return list(value)

        return [value]

    def should_use_zero_based_index(self, values):
        helper = getattr(self.runtime, "helper", None)
        parser = getattr(helper, "parse_bool", None)
        flag = (values or {}).get("zero_based_index")

        if callable(parser):
            return parser(flag)

        return bool(flag)

    def loop_state_key(self, values, index):
        loop_id = str((values or {}).get("loop_id", "") or "").strip()

        if loop_id:
            return f"id:{loop_id}"

        return f"index:{index}"

    def build_loop_maps(self, items):
        start_to_end = {}
        end_to_start = {}
        stack = []

        for index, item in enumerate(items):
            command_id = getattr(item, "command_id", "")

            if command_id == "flow_control.start_loop":
                stack.append(index)
                continue

            if command_id != "flow_control.end_loop":
                continue

            if not stack:
                raise RuntimeError(
                    f"End Loop has no matching Start Loop at line {index + 1}"
                )

            start_index = stack.pop()
            start_to_end[start_index] = index
            end_to_start[index] = start_index

        if stack:
            start_index = stack[-1]
            raise RuntimeError(
                f"Start Loop has no matching End Loop at line {start_index + 1}"
            )

        return {
            "start_to_end": start_to_end,
            "end_to_start": end_to_start,
        }

    def get_loop_maps(self, frame):
        maps = frame.get("loop_maps")

        if isinstance(maps, dict):
            return maps

        maps = self.build_loop_maps(frame.get("items", []))
        frame["loop_maps"] = maps
        return maps

    def evaluate_while_loop_condition(self, values):
        variable_name = values.get("variable_name")
        operator = normalize_loop_operator(values.get("operator"))
        compare_source = values.get("compare_source")
        compare_value = values.get("compare_value")
        compare_variable = values.get("compare_variable")
        current_value = self.get_runtime_variable(variable_name)

        if operator in ["is true", "is false"]:
            return self.compare_runtime_values(current_value, operator, None)

        compare_type = self.get_runtime_variable_type(variable_name)

        if compare_source == "variable":
            source_compare_value = self.get_runtime_variable(compare_variable)
        else:
            source_compare_value = compare_value

        final_compare_value = self.convert_runtime_value(
            source_compare_value,
            compare_type,
        )
        return self.compare_runtime_values(
            current_value,
            operator,
            final_compare_value,
        )

    def handle_start_loop(self, frame, start_index, values):
        maps = self.get_loop_maps(frame)
        end_index = maps.get("start_to_end", {}).get(start_index)

        if end_index is None:
            raise RuntimeError(
                f"Start Loop has no matching End Loop at line {start_index + 1}"
            )

        loop_states = frame.setdefault("loop_states", {})
        state_key = self.loop_state_key(values, start_index)
        mode = str(values.get("mode", "Repeat Count") or "Repeat Count")
        use_zero_based_index = self.should_use_zero_based_index(values)

        if mode == "While Condition":
            if self.evaluate_while_loop_condition(values):
                return

            loop_states.pop(state_key, None)
            frame["index"] = end_index + 1
            return

        if mode == "For Each Item":
            state = loop_states.get(state_key)

            if not isinstance(state, dict):
                if values.get("list_source") == "variable":
                    source_value = self.get_runtime_variable(
                        values.get("list_variable")
                    )
                else:
                    source_value = values.get("list_value")

                state = {
                    "mode": mode,
                    "items": self.normalize_loop_items(
                        source_value,
                        values.get("delimiter"),
                    ),
                    "index": 0,
                }
                loop_states[state_key] = state

            items = state.get("items", [])
            item_index = int(state.get("index", 0) or 0)

            if item_index >= len(items):
                loop_states.pop(state_key, None)
                frame["index"] = end_index + 1
                return

            display_index = (
                item_index if use_zero_based_index else item_index + 1
            )
            self.set_runtime_variable(
                values.get("index_variable"),
                display_index,
            )
            self.set_runtime_variable(
                values.get("item_variable"),
                items[item_index],
            )
            state["index"] = item_index + 1
            return

        state = loop_states.get(state_key)

        if not isinstance(state, dict):
            try:
                repeat_count = int(values.get("repeat_count", 0) or 0)
            except Exception:
                repeat_count = 0

            state = {
                "mode": mode,
                "count": 0,
                "total": max(0, repeat_count),
            }
            loop_states[state_key] = state

        count = int(state.get("count", 0) or 0)
        total = int(state.get("total", 0) or 0)

        if count >= total:
            loop_states.pop(state_key, None)
            frame["index"] = end_index + 1
            return

        display_index = count if use_zero_based_index else count + 1
        self.set_runtime_variable(values.get("index_variable"), display_index)
        state["count"] = count + 1

    def handle_end_loop(self, frame, end_index):
        maps = self.get_loop_maps(frame)
        start_index = maps.get("end_to_start", {}).get(end_index)

        if start_index is None:
            raise RuntimeError(
                f"End Loop has no matching End Loop at line {end_index + 1}"
            )

        items = frame.get("items", [])

        if start_index < 0 or start_index >= len(items):
            raise RuntimeError(
                f"End Loop has invalid matching Start Loop at line {end_index + 1}"
            )

        start_item = items[start_index]
        values = getattr(start_item, "values", {}) or {}
        state_key = self.loop_state_key(values, start_index)
        loop_states = frame.setdefault("loop_states", {})
        mode = str(values.get("mode", "Repeat Count") or "Repeat Count")

        if mode == "While Condition":
            frame["index"] = start_index
            return

        state = loop_states.get(state_key)

        if not isinstance(state, dict):
            return

        if mode == "For Each Item":
            item_index = int(state.get("index", 0) or 0)
            items_value = state.get("items", [])

            if item_index < len(items_value):
                frame["index"] = start_index
                return

            loop_states.pop(state_key, None)
            return

        count = int(state.get("count", 0) or 0)
        total = int(state.get("total", 0) or 0)

        if count < total:
            frame["index"] = start_index
            return

        loop_states.pop(state_key, None)

    def execute_python_event(self, event):
        command = self.registry.get("system.run_python")

        if command is None:
            raise RuntimeError("Run Python command is not registered.")

        return command.execute(
            values={
                "python_code": event.get("python_code", ""),
                "target_variable": event.get("target_variable", ""),
            },
            runtime=self.runtime,
        )

    def start_macro_group_frame(
        self,
        call_stack,
        recursion_depth,
        max_depth,
        target_name,
    ):
        resolved_target = self.resolve_group_target(target_name)

        if not resolved_target:
            return recursion_depth, False

        if recursion_depth >= max_depth:
            raise RuntimeError("Max recursion depth exceeded")

        target_items = self.group_library.get(resolved_target, [])

        if not target_items:
            return recursion_depth, False

        display_title = self.get_group_display_title(target_name)

        if display_title:
            self.on_group_started(display_title)

        recursion_depth += 1
        call_stack.append(
            {
                "items": target_items,
                "index": 0,
                "group_name": resolved_target,
                "display_title": display_title,
                "emit_finish": True,
                "loop_states": {},
                "loop_maps": None,
            }
        )
        return recursion_depth, True

    def apply_event(self, event, call_stack, recursion_depth, max_depth):
        if not isinstance(event, dict) or not call_stack:
            return recursion_depth, False

        action_type = str(event.get("action_type", "") or "").strip()

        if action_type == "run_python":
            self.execute_python_event(event)
            return recursion_depth, False

        if action_type == "jump_to_comment":
            comment_name = event.get("comment", "")
            frame = call_stack[-1]
            target_index = self.get_comment_position(
                frame.get("items", []),
                comment_name,
            )

            if target_index is None:
                return recursion_depth, False

            frame["index"] = target_index
            return recursion_depth, True

        if action_type == "run_macro_group":
            if event.get("run_in_background"):
                starter = getattr(
                    self.runtime,
                    "start_background_macro_group",
                    None,
                )

                if callable(starter):
                    started = starter(event.get("target", ""))

                    if started:
                        return recursion_depth, False

            return self.start_macro_group_frame(
                call_stack,
                recursion_depth,
                max_depth,
                event.get("target", ""),
            )

        return recursion_depth, False

    def poll_timer_events(self):
        poller = getattr(self.runtime, "poll_global_timers", None)

        if callable(poller):
            poller()

    def process_events(self, call_stack, recursion_depth, max_depth):
        changed = False
        self.poll_timer_events()

        while not self.stopped:
            event = self.pop_event()

            if event is None:
                break

            recursion_depth, event_changed = self.apply_event(
                event,
                call_stack,
                recursion_depth,
                max_depth,
            )
            changed = changed or event_changed

            if event_changed:
                break

        return recursion_depth, changed

    def wait_forever(self, call_stack, frame, recursion_depth, max_depth):
        while not self.stopped:
            self.wait_if_paused()
            recursion_depth = self.handle_exit_current_macro_request(
                call_stack,
                recursion_depth,
            )

            if self.stopped or not call_stack:
                return recursion_depth

            recursion_depth, changed = self.process_events(
                call_stack,
                recursion_depth,
                max_depth,
            )

            if changed:
                if call_stack and call_stack[-1] is not frame:
                    frame["resume_wait_forever"] = True

                return recursion_depth

            time.sleep(0.03)

        return recursion_depth

    def run(self):
        current_loop = 0

        while current_loop < self.loop_count and not self.stopped:
            call_stack = [
                {
                    "items": self.items,
                    "index": 0,
                    "group_name": "",
                    "display_title": "",
                    "emit_finish": False,
                    "loop_states": {},
                    "loop_maps": None,
                }
            ]

            recursion_depth = 0
            max_depth = self.max_depth

            while call_stack and not self.stopped:
                self.wait_if_paused()
                recursion_depth = self.handle_exit_current_macro_request(
                    call_stack,
                    recursion_depth,
                )

                if self.stopped or not call_stack:
                    break

                recursion_depth, event_changed = self.process_events(
                    call_stack,
                    recursion_depth,
                    max_depth,
                )

                if event_changed:
                    continue

                frame = call_stack[-1]

                if frame.pop("resume_wait_forever", False):
                    recursion_depth = self.wait_forever(
                        call_stack,
                        frame,
                        recursion_depth,
                        max_depth,
                    )
                    continue

                items = frame["items"]
                index = frame["index"]

                if index >= len(items):
                    finished_frame = self.finish_current_frame(call_stack)

                    if finished_frame and finished_frame.get("emit_finish"):
                        recursion_depth -= 1

                    continue

                item = items[index]
                frame["index"] += 1

                if not getattr(item, "enabled", True):
                    continue

                command = self.registry.get(getattr(item, "command_id", ""))

                if command is None:
                    continue

                if hasattr(command, "is_supported_os") and not command.is_supported_os():
                    continue

                self.on_step(index)
                result = self.execute_command(
                    command,
                    getattr(item, "values", {}) or {},
                )

                self.wait_if_paused()
                recursion_depth = self.handle_exit_current_macro_request(
                    call_stack,
                    recursion_depth,
                )

                if self.stopped or not call_stack:
                    break

                if isinstance(result, dict):
                    action = result.get("action", "")

                    if action == "start_loop":
                        self.handle_start_loop(
                            frame,
                            index,
                            result.get("values", {}) or {},
                        )
                        continue

                    if action == "end_loop":
                        self.handle_end_loop(frame, index)
                        self.sleep_line_delay()
                        continue

                    if action == "register_global_hotkey":
                        self.register_hotkey(result)
                        self.sleep_line_delay()
                        continue

                    if action == "register_global_timer":
                        self.register_timer(result)
                        self.sleep_line_delay()
                        continue

                    if action == "wait_forever":
                        recursion_depth = self.wait_forever(
                            call_stack,
                            frame,
                            recursion_depth,
                            max_depth,
                        )
                        continue

                    if action == "jump_to_comment":
                        self.sleep_line_delay()
                        comment_name = result.get("comment", "")
                        target_index = self.get_comment_position(
                            items,
                            comment_name,
                        )

                        if target_index is None:
                            raise RuntimeError(
                                f"Comment not found: {comment_name}"
                            )

                        frame["index"] = target_index
                        continue

                    if action == "run_macro_group":
                        if result.get("run_in_background"):
                            starter = getattr(
                                self.runtime,
                                "start_background_macro_group",
                                None,
                            )

                            if callable(starter):
                                started = starter(result.get("target", ""))

                                if started:
                                    self.sleep_line_delay()
                                    continue

                        recursion_depth, started = (
                            self.start_macro_group_frame(
                                call_stack,
                                recursion_depth,
                                max_depth,
                                result.get("target", ""),
                            )
                        )

                        if started:
                            continue

                    if action in (
                        "exit_current_macro",
                        "return_from_macro",
                        "stop",
                    ):
                        finished_frame = self.finish_current_frame(
                            call_stack,
                        )

                        if finished_frame and finished_frame.get("emit_finish"):
                            recursion_depth -= 1

                        if not call_stack:
                            self.stopped = True

                        continue

                    if action in ("stop_entire_run", "stop_run"):
                        self.stopped = True
                        call_stack.clear()
                        break

                self.sleep_line_delay()

            current_loop += 1
