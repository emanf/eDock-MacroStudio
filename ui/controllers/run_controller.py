from PySide6.QtCore import QObject, Signal

from ...core.macro_recorder import MacroRecorder
from ...core.engine.macro_runner import MacroRunner


class RunController(QObject):
    mode_changed = Signal(str)

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.project = window.project
        self.messages = window.messages
        self.runner = MacroRunner(registry=window.registry, context=window.app_ref.context, parent=window)
        self.recorder = MacroRecorder(parent=window)
        self.execution_stack = []
        self.current_macro_index = -1
        self.tab_switch_in_progress = False
        self.runner.finished.connect(self.on_run_finished)
        self.runner.failed.connect(self.on_run_failed)
        self.runner.step_changed.connect(self.macro_step_changed)
        self.runner.message.connect(self.show_runner_message)
        self.runner.macro_group_started.connect(self.on_runner_macro_group_started)
        self.runner.macro_group_finished.connect(self.on_runner_macro_group_finished)
        self.recorder.recorded.connect(self.on_recorded_item)
        self.recorder.started.connect(self.on_record_started)
        self.recorder.stopped.connect(self.on_record_stopped)
        self.recorder.failed.connect(self.on_record_failed)
        self.runner.set_macros_provider(lambda: self.project.macros)

    def is_busy(self):
        return self.runner.is_running()

    def reset_session(self):
        self.execution_stack = []
        self.current_macro_index = -1
        self.tab_switch_in_progress = False

    def sync_execution_from_ui(self):
        self.project.execution = self.project.normalize_execution(self.window.control_bar.execution_data())
        return self.project.execution

    def set_running_state(self, mode="idle"):
        if mode is True:
            mode = "running"
        elif mode is False or mode is None:
            mode = "idle"
        is_macro_running = mode in ("main_running", "selected_running", "running")
        is_play_mode = is_macro_running or mode == "recording"
        self.window.macro_list.set_play_mode(is_play_mode)
        self.window.macro_tabs.set_play_mode(is_macro_running)
        self.window.control_bar.set_mode(mode)
        self.mode_changed.emit(mode)

    def set_active_macro_index_from_runner(self, index):
        if index < 0 or index >= len(self.project.macros):
            return
        self.tab_switch_in_progress = True
        try:
            self.project.active_index = index
            self.window.refresh_macro_tabs()
            self.window.load_active_macro_to_ui()
        finally:
            self.tab_switch_in_progress = False

    def run_macro(self):
        if self.runner.is_running():
            self.stop_entire_run()
            return
        if self.recorder.is_recording:
            self.recorder.stop()
        if self.project.active_index < 0 or self.project.active_index >= len(self.project.macros):
            self.messages.show_information("Empty Macro", "There is no active macro to run.")
            return
        if not self.window.macro_list.items_data:
            self.messages.show_information("Empty Macro", "There is no macro item to run.")
            return
        self.window.sync_active_macro_from_ui()
        self.project.variables = self.window.collect_defined_variables()
        execution = self.sync_execution_from_ui()
        self.execution_stack = [self.project.active_index]
        self.current_macro_index = self.project.active_index
        started = self.runner.start(
            items=self.window.macro_list.items_data,
            loop_count=execution["loop_count"],
            speed=execution["speed"],
            delay_ms=execution["delay_ms"],
            max_depth=execution["max_depth"],
            initial_variables=self.project.variables,
        )
        if started:
            self.set_running_state("selected_running")
            self.window.refresh_macro_tabs()
            self.window.load_active_macro_to_ui()
        else:
            self.execution_stack = []
            self.current_macro_index = -1

    def run_main_macro(self):
        if self.runner.is_running():
            self.stop_entire_run()
            return
        if self.recorder.is_recording:
            self.recorder.stop()
        self.window.sync_active_macro_from_ui()
        self.project.ensure_main_macro()
        if not self.project.macros:
            self.messages.show_information("Empty Macro", "There is no main macro to run.")
            return
        main_macro = self.project.macros[0]
        if not main_macro.items:
            self.messages.show_information("Empty Macro", "There is no macro item in Main to run.")
            return
        self.project.variables = self.window.collect_defined_variables()
        execution = self.sync_execution_from_ui()
        self.execution_stack = [0]
        self.current_macro_index = 0
        started = self.runner.start(
            items=main_macro.items,
            loop_count=execution["loop_count"],
            speed=execution["speed"],
            delay_ms=execution["delay_ms"],
            max_depth=execution["max_depth"],
            initial_variables=self.project.variables,
        )
        if started:
            self.set_running_state("main_running")
            self.set_active_macro_index_from_runner(0)
            self.window.refresh_macro_tabs()
            self.window.load_active_macro_to_ui()
        else:
            self.execution_stack = []
            self.current_macro_index = -1

    def toggle_pause(self):
        if not self.runner.is_running():
            return
        if self.runner.is_paused():
            self.runner.resume()
            self.window.control_bar.set_pause_text("Pause")
            return
        self.runner.pause()
        self.window.control_bar.set_pause_text("Resume")

    def exit_current_macro(self):
        if self.runner.is_running():
            self.runner.exit_current_macro()

    def stop_entire_run(self):
        if self.runner.is_running():
            self.runner.stop()
        self.set_running_state("idle")

    def toggle_recording(self):
        if self.recorder.is_recording:
            self.recorder.stop()
            return
        if self.runner.is_running():
            self.messages.show_warning("Macro Running", "Stop the running macro before recording.")
            return
        if self.project.active_index < 0:
            self.project.ensure_main_macro()
            self.project.active_index = 0
            self.window.refresh_macro_tabs()
            self.window.load_active_macro_to_ui()
        self.recorder.start()

    def on_record_started(self):
        self.set_running_state("recording")

    def on_record_stopped(self):
        self.set_running_state("idle")

    def on_record_failed(self, message):
        self.messages.show_critical("Recording Failed", message)

    def on_recorded_item(self, item):
        if self.project.active_index < 0:
            self.project.ensure_main_macro()
            self.project.active_index = 0
            self.window.refresh_macro_tabs()
            self.window.load_active_macro_to_ui()
        self.window.macro_list.add_macro_item(item, self.window.registry)
        current_group = self.project.active_group()
        if current_group is not None:
            current_group.items = self.window.macro_list.items_data

    def on_run_finished(self):
        self.set_running_state("idle")
        self.reset_session()
        self.window.macro_list.clear_highlight()
        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()

    def on_run_failed(self, message):
        self.set_running_state("idle")
        self.reset_session()
        self.window.macro_list.clear_highlight()
        self.window.refresh_macro_tabs()
        self.window.load_active_macro_to_ui()
        self.messages.show_critical("Run Failed", message)

    def macro_step_changed(self, index):
        self.window.macro_list.highlight_step(index)

    def on_runner_macro_group_started(self, title):
        target_index = self.project.find_macro_index_by_title(title)
        if target_index < 0:
            return
        self.execution_stack.append(target_index)
        self.current_macro_index = target_index
        self.set_active_macro_index_from_runner(target_index)

    def on_runner_macro_group_finished(self, title):
        if len(self.execution_stack) > 1:
            self.execution_stack.pop()
        if self.execution_stack:
            self.current_macro_index = self.execution_stack[-1]
            self.set_active_macro_index_from_runner(self.current_macro_index)
            return
        target_index = self.project.find_macro_index_by_title(title)
        if target_index >= 0:
            self.current_macro_index = target_index
            self.set_active_macro_index_from_runner(target_index)

    def show_runner_message(self, title, message, wait):
        on_closed = self.runner.notify_message_closed if wait else None
        self.messages.show_information(title, message, on_closed=on_closed)
