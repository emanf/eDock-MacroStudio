class BaseOSHelper:
    def __init__(self, runtime):
        self.runtime = runtime

    def click_at_position(self, x, y, button="left", clicks=1, no_move=False, interval=0.1):
        raise NotImplementedError()

    def get_screen_size(self):
        import pyautogui
        return pyautogui.size()
