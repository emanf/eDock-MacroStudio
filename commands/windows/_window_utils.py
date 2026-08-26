import ctypes
import os
import platform
import re
from ctypes import wintypes


def ensure_windows():
    if platform.system().lower() != "windows":
        raise RuntimeError("Window commands are only supported on Windows.")


user32 = ctypes.windll.user32 if platform.system().lower() == "windows" else None
kernel32 = ctypes.windll.kernel32 if platform.system().lower() == "windows" else None

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
WM_CLOSE = 0x0010
SW_RESTORE = 9
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
GWL_STYLE = -16
GWL_EXSTYLE = -20
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_SYSMENU = 0x00080000
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
LWA_ALPHA = 0x00000002
MONITOR_DEFAULTTONEAREST = 2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOOWNERZORDER = 0x0200
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
HWND_TOP = 0
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2

_fullscreen_states = {}


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


if user32 is not None:
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.MonitorFromWindow.restype = wintypes.HMONITOR
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, ctypes.c_byte, wintypes.DWORD]
    user32.SetLayeredWindowAttributes.restype = wintypes.BOOL
    user32.EnumWindows.restype = wintypes.BOOL

if kernel32 is not None:
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL


def get_window_long(hwnd, index):
    if hasattr(user32, "GetWindowLongPtrW"):
        user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetWindowLongPtrW.restype = ctypes.c_void_p
        value = user32.GetWindowLongPtrW(wintypes.HWND(hwnd), index)
        return int(value or 0)

    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    return int(user32.GetWindowLongW(wintypes.HWND(hwnd), index))


def set_window_long(hwnd, index, value):
    if hasattr(user32, "SetWindowLongPtrW"):
        user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        user32.SetWindowLongPtrW.restype = ctypes.c_void_p
        result = user32.SetWindowLongPtrW(wintypes.HWND(hwnd), index, ctypes.c_void_p(value))
        return int(result or 0)

    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    user32.SetWindowLongW.restype = ctypes.c_long
    return int(user32.SetWindowLongW(wintypes.HWND(hwnd), index, value))


def parse_handle(value):
    text = str(value or "").strip()
    if not text:
        return 0

    try:
        return int(text, 0)
    except Exception:
        return 0


def get_window_text(hwnd):
    hwnd = wintypes.HWND(hwnd)
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def get_window_class(hwnd):
    hwnd = wintypes.HWND(hwnd)
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def get_window_rect(hwnd):
    rect = RECT()
    user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect))
    return rect


def rect_to_dict(rect):
    return {
        "left": int(rect.left),
        "top": int(rect.top),
        "right": int(rect.right),
        "bottom": int(rect.bottom),
        "x": int(rect.left),
        "y": int(rect.top),
        "width": int(rect.right - rect.left),
        "height": int(rect.bottom - rect.top),
    }


def get_monitor_rect(hwnd):
    monitor = user32.MonitorFromWindow(wintypes.HWND(hwnd), MONITOR_DEFAULTTONEAREST)
    if not monitor:
        return None

    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)

    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return None

    return info.rcMonitor


def get_process_id(hwnd):
    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(process_id))
    return int(process_id.value or 0)


def get_process_path(process_id):
    if not process_id:
        return ""

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
    if not handle:
        return ""

    try:
        size = wintypes.DWORD(4096)
        buffer = ctypes.create_unicode_buffer(size.value)
        success = kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
        if not success:
            return ""
        return buffer.value
    finally:
        kernel32.CloseHandle(handle)


def get_window_info(hwnd):
    ensure_windows()

    hwnd = int(hwnd or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return {}

    rect = get_window_rect(hwnd)
    process_id = get_process_id(hwnd)
    process_path = get_process_path(process_id)
    process_name = os.path.basename(process_path) if process_path else ""

    return {
        "handle": int(hwnd),
        "title": get_window_text(hwnd),
        "class_name": get_window_class(hwnd),
        "process_id": process_id,
        "process_path": process_path,
        "process_name": process_name,
        "left": int(rect.left),
        "top": int(rect.top),
        "right": int(rect.right),
        "bottom": int(rect.bottom),
        "x": int(rect.left),
        "y": int(rect.top),
        "width": int(rect.right - rect.left),
        "height": int(rect.bottom - rect.top),
        "visible": bool(user32.IsWindowVisible(wintypes.HWND(hwnd))),
        "minimized": bool(user32.IsIconic(wintypes.HWND(hwnd))),
        "active": int(user32.GetForegroundWindow() or 0) == int(hwnd),
        "fullscreen": int(hwnd) in _fullscreen_states,
        "always_on_top": bool(get_window_long(hwnd, GWL_EXSTYLE) & WS_EX_TOPMOST),
    }


def normalize_match_mode(value):
    mode = str(value or "contains").strip().lower()
    if mode not in ("contains", "exact", "regex"):
        return "contains"
    return mode


def text_matches(source, needle, mode):
    source_text = str(source or "")
    needle_text = str(needle or "").strip()

    if not needle_text:
        return True

    if mode == "exact":
        return source_text.lower() == needle_text.lower()

    if mode == "regex":
        try:
            return re.search(needle_text, source_text, re.IGNORECASE) is not None
        except Exception:
            return False

    return needle_text.lower() in source_text.lower()


def process_matches(process_name, process_path, needle, mode):
    needle_text = str(needle or "").strip()

    if not needle_text:
        return True

    return text_matches(process_name, needle_text, mode) or text_matches(process_path, needle_text, mode)


def window_matches(info, filters):
    match_mode = normalize_match_mode(filters.get("match_mode", "contains"))
    handle = parse_handle(filters.get("handle", ""))

    if handle and int(info.get("handle", 0) or 0) != handle:
        return False

    if not text_matches(info.get("title", ""), filters.get("title", ""), match_mode):
        return False

    if not text_matches(info.get("class_name", ""), filters.get("class_name", ""), match_mode):
        return False

    if not process_matches(
        info.get("process_name", ""),
        info.get("process_path", ""),
        filters.get("process_name", ""),
        match_mode,
    ):
        return False

    if filters.get("visible_only", True) and not info.get("visible", False):
        return False

    return True


def list_windows(filters=None):
    ensure_windows()

    filters = dict(filters or {})
    results = []

    enum_windows_proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, lparam):
        info = get_window_info(int(hwnd or 0))
        if info and window_matches(info, filters):
            results.append(info)
        return True

    user32.EnumWindows(enum_windows_proc(callback), 0)
    return results


def find_window(filters=None):
    windows = list_windows(filters)
    if not windows:
        return {}
    return windows[0]


def activate_window(handle):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    if user32.IsIconic(wintypes.HWND(hwnd)):
        user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)

    return bool(user32.SetForegroundWindow(wintypes.HWND(hwnd)))


def close_window(handle):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    return bool(user32.PostMessageW(wintypes.HWND(hwnd), WM_CLOSE, 0, 0))


def minimize_window(handle):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    return bool(user32.ShowWindow(wintypes.HWND(hwnd), SW_MINIMIZE))


def maximize_window(handle):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    return bool(user32.ShowWindow(wintypes.HWND(hwnd), SW_MAXIMIZE))


def restore_window(handle):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    if hwnd in _fullscreen_states:
        return restore_fullscreen_window(hwnd)

    return bool(user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE))


def fullscreen_window(handle):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    monitor_rect = get_monitor_rect(hwnd)
    if monitor_rect is None:
        return False

    if hwnd not in _fullscreen_states:
        rect = get_window_rect(hwnd)
        _fullscreen_states[hwnd] = {
            "style": get_window_long(hwnd, GWL_STYLE),
            "exstyle": get_window_long(hwnd, GWL_EXSTYLE),
            "rect": rect_to_dict(rect),
        }

    style = get_window_long(hwnd, GWL_STYLE)
    style = style & ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
    set_window_long(hwnd, GWL_STYLE, style)

    user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)

    return bool(
        user32.SetWindowPos(
            wintypes.HWND(hwnd),
            wintypes.HWND(HWND_TOP),
            int(monitor_rect.left),
            int(monitor_rect.top),
            int(monitor_rect.right - monitor_rect.left),
            int(monitor_rect.bottom - monitor_rect.top),
            SWP_NOOWNERZORDER | SWP_FRAMECHANGED | SWP_SHOWWINDOW,
        )
    )


def restore_fullscreen_window(handle):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    state = _fullscreen_states.pop(hwnd, None)
    if not state:
        return bool(user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE))

    rect = state.get("rect", {})

    set_window_long(hwnd, GWL_STYLE, int(state.get("style", 0)))
    set_window_long(hwnd, GWL_EXSTYLE, int(state.get("exstyle", 0)))

    return bool(
        user32.SetWindowPos(
            wintypes.HWND(hwnd),
            wintypes.HWND(HWND_TOP),
            int(rect.get("x", 0)),
            int(rect.get("y", 0)),
            int(rect.get("width", 800)),
            int(rect.get("height", 600)),
            SWP_NOOWNERZORDER | SWP_FRAMECHANGED | SWP_SHOWWINDOW,
        )
    )


def set_window_position(handle, x, y):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    return bool(
        user32.SetWindowPos(
            wintypes.HWND(hwnd),
            wintypes.HWND(HWND_TOP),
            int(x),
            int(y),
            0,
            0,
            SWP_NOSIZE | SWP_NOZORDER | SWP_NOOWNERZORDER | SWP_SHOWWINDOW,
        )
    )


def resize_window(handle, width, height):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    width = max(1, int(width))
    height = max(1, int(height))

    return bool(
        user32.SetWindowPos(
            wintypes.HWND(hwnd),
            wintypes.HWND(HWND_TOP),
            0,
            0,
            width,
            height,
            SWP_NOMOVE | SWP_NOZORDER | SWP_NOOWNERZORDER | SWP_SHOWWINDOW,
        )
    )


def set_window_opacity(handle, opacity):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    try:
        opacity_value = float(opacity)
    except Exception:
        opacity_value = 1.0

    opacity_value = max(0.0, min(1.0, opacity_value))
    alpha = int(round(opacity_value * 255))

    exstyle = get_window_long(hwnd, GWL_EXSTYLE)
    if not exstyle & WS_EX_LAYERED:
        set_window_long(hwnd, GWL_EXSTYLE, exstyle | WS_EX_LAYERED)

    return bool(user32.SetLayeredWindowAttributes(wintypes.HWND(hwnd), 0, alpha, LWA_ALPHA))


def set_window_topmost(handle, enabled=True):
    ensure_windows()

    hwnd = int(handle or 0)
    if not hwnd or not user32.IsWindow(wintypes.HWND(hwnd)):
        return False

    if user32.IsIconic(wintypes.HWND(hwnd)):
        user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)

    insert_after = wintypes.HWND(HWND_TOPMOST if enabled else HWND_NOTOPMOST)

    success = user32.SetWindowPos(
        wintypes.HWND(hwnd),
        insert_after,
        0,
        0,
        0,
        0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOOWNERZORDER,
    )

    if not success:
        return False

    return bool(
        user32.SetWindowPos(
            wintypes.HWND(hwnd),
            insert_after,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOOWNERZORDER | SWP_SHOWWINDOW,
        )
    )


def set_window_state(handle, state):
    action = str(state or "restore").strip().lower()

    if action == "activate":
        return activate_window(handle)

    if action == "minimize":
        return minimize_window(handle)

    if action == "maximize":
        return maximize_window(handle)

    if action == "fullscreen":
        return fullscreen_window(handle)

    if action == "restore_fullscreen":
        return restore_fullscreen_window(handle)

    if action == "always_on_top":
        return set_window_topmost(handle, True)

    if action == "not_always_on_top":
        return set_window_topmost(handle, False)

    return restore_window(handle)
