import platform

def get_os_helper(runtime):
    sys_platform = platform.system()
    if sys_platform == "Windows":
        from .os.windows import WindowsOSHelper
        return WindowsOSHelper(runtime)
    elif sys_platform == "Darwin":
        from .os.macos import MacOSHelper
        return MacOSHelper(runtime)
    else:
        from .os.linux import LinuxOSHelper
        return LinuxOSHelper(runtime)
