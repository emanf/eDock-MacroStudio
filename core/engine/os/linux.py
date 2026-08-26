from .base import BaseOSHelper

class LinuxOSHelper(BaseOSHelper):
    def click_at_position(self, x, y, button="left", clicks=1, no_move=False, interval=0.1):
        self.runtime.pyautogui_call("click", x, y, clicks=clicks, interval=interval, button=button)
