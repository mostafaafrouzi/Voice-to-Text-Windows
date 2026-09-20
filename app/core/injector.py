import ctypes
from ctypes import wintypes
import time
import threading
import win32clipboard
import win32con
from ..config import config

user32 = ctypes.windll.user32

VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1

# HWND پنجره هدف که قبل از شروع ضبط ذخیره می‌شود
_target_hwnd: int = 0


def save_target_window():
    """
    ذخیره HWND پنجره فعال فعلی به عنوان هدف تزریق متن.
    باید درست قبل از شروع ضبط صدا فراخوانی شود.
    """
    global _target_hwnd
    hwnd = user32.GetForegroundWindow()
    if hwnd:
        _target_hwnd = hwnd
    print(f"[Injector] Target window saved: {_target_hwnd}")


def _restore_focus_to_target():
    """
    بازگرداندن فوکوس به پنجره هدف ذخیره‌شده.
    قبل از تزریق متن فراخوانی می‌شود.
    """
    global _target_hwnd
    if not _target_hwnd:
        return False
    try:
        # بررسی معتبر بودن HWND
        if not user32.IsWindow(_target_hwnd):
            _target_hwnd = 0
            return False
        # تغییر فوکوس به پنجره هدف
        user32.SetForegroundWindow(_target_hwnd)
        time.sleep(0.06)  # انتظار برای پردازش پیام فوکوس
        return True
    except Exception as e:
        print(f"[Injector] Focus restore failed: {e}")
        return False


# ساختارهای Ctypes برای SendInput
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT)
    ]


def _get_clipboard_text():
    """دریافت محتوای فعلی متنی کلیپ‌بورد با مدیریت خطای قفل بودن کلیپ‌بورد."""
    for _ in range(5):
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    return data
            finally:
                win32clipboard.CloseClipboard()
            break
        except Exception:
            time.sleep(0.01)
    return None


def _set_clipboard_text(text: str):
    """تنظیم متن در کلیپ‌بورد با تلاش مجدد در صورت درگیری پردازه‌ها."""
    for _ in range(10):
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            finally:
                win32clipboard.CloseClipboard()
            return True
        except Exception:
            time.sleep(0.01)
    return False


def paste_via_clipboard(text: str):
    """
    تزریق فوق‌سریع و ایمن متن از طریق کلیپ‌بورد.
    قبل از Ctrl+V فوکوس را به پنجره هدف بازمی‌گرداند.
    """
    if not text:
        return

    previous_text = _get_clipboard_text()

    if not _set_clipboard_text(text):
        # اگر کلیپ‌بورد باز نشد، روش یونیکد را امتحان کن
        type_via_unicode(text)
        return

    # بازگردانی فوکوس به پنجره هدف قبل از ارسال کلید
    _restore_focus_to_target()

    # ارسال Ctrl + V
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.025)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    # بازگردانی کلیپ‌بورد قبلی پس از چند میلی‌ثانیه
    if previous_text is not None:
        def restore():
            time.sleep(0.12)
            _set_clipboard_text(previous_text)

        threading.Thread(target=restore, daemon=True).start()


def type_via_unicode(text: str):
    """تایپ مستقیم کاراکترهای یونیکد از طریق SendInput با بازگردانی فوکوس."""
    # بازگردانی فوکوس قبل از تایپ
    _restore_focus_to_target()

    for char in text:
        if char == "\n":
            # Enter key
            user32.keybd_event(0x0D, 0, 0, 0)
            user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.005)
            continue

        code = ord(char)
        # Key down
        inp_down = INPUT(type=INPUT_KEYBOARD)
        inp_down.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0)
        user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))

        # Key up
        inp_up = INPUT(type=INPUT_KEYBOARD)
        inp_up.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
        user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))

        time.sleep(0.003)


def inject_text(text: str):
    """تزریق هوشمند متن بر اساس تنظیمات انتخابی کاربر."""
    if not text:
        return

    method = config.get("injection_method", "clipboard")
    if method == "unicode":
        type_via_unicode(text)
    else:
        paste_via_clipboard(text)
