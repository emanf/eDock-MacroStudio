import ctypes
import time
import random
from .base import BaseOSHelper

class WindowsOSHelper(BaseOSHelper):
    def click_at_position(self, x, y, button="left", clicks=1, no_move=False, interval=0.1):
        if not no_move:
            self.runtime.pyautogui_call("click", x, y, clicks=clicks, interval=interval, button=button)
            return

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        WM_LBUTTONDOWN = 0x0201
        WM_LBUTTONUP = 0x0202
        WM_RBUTTONDOWN = 0x0204
        WM_RBUTTONUP = 0x0205
        WM_MBUTTONDOWN = 0x0207
        WM_MBUTTONUP = 0x0208

        button_map = {
            "left": (WM_LBUTTONDOWN, WM_LBUTTONUP),
            "right": (WM_RBUTTONDOWN, WM_RBUTTONUP),
            "middle": (WM_MBUTTONDOWN, WM_MBUTTONUP)
        }
        down_msg, up_msg = button_map.get(button, (WM_LBUTTONDOWN, WM_LBUTTONUP))

        hwnd = ctypes.windll.user32.WindowFromPoint(POINT(x, y))
        if hwnd:
            screen_point = POINT(x, y)
            ctypes.windll.user32.ScreenToClient(hwnd, ctypes.byref(screen_point))
            lparam = (screen_point.y << 16) | (screen_point.x & 0xFFFF)
            
            for _ in range(clicks):
                ctypes.windll.user32.PostMessageW(hwnd, down_msg, 0x0001, lparam)
                time.sleep(0.01)
                ctypes.windll.user32.PostMessageW(hwnd, up_msg, 0, lparam)
                if clicks > 1:
                    time.sleep(interval)
