import os
import traceback

from core.app.app_base import AppBase
from core.paths import get_app_data_dir

from .core.macro_registry import MacroRegistry
from .core.macro_storage import MacroStorage
from .core.engine.macro_runner import MacroRunner
from .core.macro_loader import MacroLoader
from .ui.windows.main_window import MacroStudioWindow


class MacroStudioApp(AppBase):
    def on_init(self):
        self.registry = MacroRegistry()
        self.storage = MacroStorage(self)
        self.runner = MacroRunner(self.registry)
        self.loader = MacroLoader(self)
        self.window = None

    def on_load(self):
        pass

    def on_unload(self):
        if self.window is not None:
            try:
                self.window.close()
            except Exception:
                pass
        self.window = None

    def run(self):
        if not self.window:
            try:
                self.loader.load_all(self.registry)

                self.window = MacroStudioWindow(
                    app_ref=self,
                    registry=self.registry,
                    storage=self.storage
                )
                self.register_main_window(self.window)
            except Exception as e:
                print(f"CRITICAL ERROR creating window: {e}")
                traceback.print_exc()
                return

        if self.window:
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
        else:
            print("Window does not exist - creation failed.")

    def get_app_data_dir(self):
        path = get_app_data_dir(self.id)
        os.makedirs(path, exist_ok=True)
        return path


App = MacroStudioApp
