import os
import sys
import traceback
import importlib
import importlib.util

from ..commands import __path__ as commands_path
from ..commands import __name__ as commands_package_name


class MacroLoader:
    def __init__(self, app):
        self.app = app

    def load_all(self, registry):
        self.load_builtin_modules(registry)
        self.load_user_modules(registry)

    def load_builtin_modules(self, registry):
        for root_path in commands_path:
            for current_root, dirnames, filenames in os.walk(root_path):
                dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith("__") and dirname != "__pycache__"]

                for filename in filenames:
                    if not filename.endswith(".py"):
                        continue
                    if filename.startswith("__"):
                        continue

                    file_path = os.path.join(current_root, filename)
                    relative_path = os.path.relpath(file_path, root_path)
                    module_parts = relative_path[:-3].split(os.sep)
                    full_module_name = ".".join([commands_package_name] + module_parts)
                    try:
                        module = importlib.import_module(full_module_name)
                        self.register_module_macros(module, registry)
                    except Exception:
                        traceback.print_exc()

    def load_user_modules(self, registry):
        user_commands_path = os.path.join(self.app.get_app_data_dir(), "commands")

        if not os.path.exists(user_commands_path):
            return

        for current_root, dirnames, filenames in os.walk(user_commands_path):
            dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith("__") and dirname != "__pycache__"]

            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                if filename.startswith("__"):
                    continue

                file_path = os.path.join(current_root, filename)
                self.load_user_module(file_path, user_commands_path, registry)

    def load_user_module(self, file_path, base_path, registry):
        try:
            relative_path = os.path.relpath(file_path, base_path)
            module_parts = relative_path[:-3].split(os.sep)
            safe_parts = [
                "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in part)
                for part in module_parts
            ]
            module_name = ".".join([commands_package_name, "user_data"] + safe_parts)

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return

            module = importlib.util.module_from_spec(spec)
            module.__package__ = module_name.rpartition(".")[0]
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            self.register_module_macros(module, registry)
        except Exception:
            traceback.print_exc()

    def register_module_macros(self, module, registry):
        register_func = getattr(module, "register_macro", None)

        if not callable(register_func):
            return

        try:
            register_func(registry)
        except Exception:
            traceback.print_exc()
