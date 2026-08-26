def pyautogui_call(method, *args, **kwargs):
    try:
        import pyautogui
    except Exception:
        raise RuntimeError("pyautogui is required for running mouse and keyboard macros.")

    fn = getattr(pyautogui, method, None)
    if not callable(fn):
        raise RuntimeError(f"pyautogui method not found: {method}")

    return fn(*args, **kwargs)
