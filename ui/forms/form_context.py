class FormContext:
    def __init__(self, main_window=None):
        self._source = main_window

    @property
    def main_window(self):
        # The widget handed in may be a child dialog rather than the main
        # window — climb the parent chain until we find the window that
        # actually owns the project.
        widget = self._source
        while widget is not None:
            if hasattr(widget, "project_macros") and hasattr(widget, "registry"):
                return widget
            parent = getattr(widget, "parent", None)
            widget = parent() if callable(parent) else None
        return self._source

    def getMainWindow(self):
        return self.main_window

    def get_project_macros(self):
        if self.main_window is None:
            return []

        sync = getattr(self.main_window, "sync_active_macro_from_ui", None)
        if callable(sync):
            sync()

        project_macros = getattr(self.main_window, "project_macros", None)
        if isinstance(project_macros, list):
            return project_macros

        return []

    def get_macro_group_options(self):
        options = []

        for macro in self.get_project_macros():
            title = str(getattr(macro, "title", "") or "").strip()
            name = str(getattr(macro, "name", "") or "").strip()

            if not name:
                continue

            options.append({
                "label": title or name,
                "value": name,
            })

        return options

    def get_commands(self):
        if self.main_window is None:
            return []

        registry = getattr(self.main_window, "registry", None)
        if registry is None:
            return []

        commands = getattr(registry, "commands", None)
        if isinstance(commands, dict):
            return list(commands.values())

        getter = getattr(registry, "all_commands", None)
        if callable(getter):
            result = getter()
            if isinstance(result, list):
                return result

        getter = getattr(registry, "get_all_commands", None)
        if callable(getter):
            result = getter()
            if isinstance(result, list):
                return result

        return []

    def get_sync_variables_dialog(self):
        if self.main_window is not None:
            sync = getattr(self.main_window, "sync_variables_dialog", None)
            if callable(sync):
                return sync()

        try:
            from ...ui.dialogs.variables_dialog import VariablesDialog
        except ImportError:
            return None

        return VariablesDialog.instance()

    def get_defined_variables(self):
        if self.main_window is None:
            return []

        collector = getattr(self.main_window, "collect_defined_variables", None)
        if callable(collector):
            variables = collector()
            if isinstance(variables, list):
                return variables

        project_variables = getattr(self.main_window, "project_variables", None)
        if isinstance(project_variables, list):
            return project_variables

        return []

    def set_defined_variables(self, variables):
        if self.main_window is None:
            return

        if isinstance(variables, list):
            self.main_window.project_variables = list(variables)
