import os
import sys
import winreg

APP_NAME = "VoiceToTextWindows"
RUN_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_autostart_enabled() -> bool:
    """بررسی فعال بودن اجرای خودکار برنامه با شروع ویندوز."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_PATH, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[Autostart] Error checking registry: {e}")
        return False


def set_autostart(enabled: bool) -> bool:
    """فعال یا غیرفعال کردن اجرای خودکار در رجیستری ویندوز."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                # اگر فایل exe کامپایل شده باشد
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}"'
                else:
                    # اسکریپت پایتون
                    main_py = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "main.py"))
                    python_exe = sys.executable
                    # اگر pythonw.exe وجود دارد از آن استفاده کن تا پنجره سیاه کنسول باز نشود
                    pythonw = python_exe.replace("python.exe", "pythonw.exe")
                    if os.path.exists(pythonw):
                        cmd = f'"{pythonw}" "{main_py}"'
                    else:
                        cmd = f'"{python_exe}" "{main_py}"'

                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                print(f"[Autostart] Enabled: {cmd}")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    print("[Autostart] Disabled")
                except FileNotFoundError:
                    pass
        return True
    except Exception as e:
        print(f"[Autostart] Error setting registry: {e}")
        return False
