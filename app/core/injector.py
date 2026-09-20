import ctypes
from ctypes import wintypes
import time
import threading
import win32clipboard
import win32con
from ..config import config

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1
WM_PASTE = 0x0302

# HWND پنجره هدف که درست قبل از شروع ضبط ذخیره می‌شود
_target_hwnd: int = 0
_injection_lock = threading.Lock()


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


def save_target_window():
    """
    ذخیره HWND پنجره فعال فعلی به عنوان هدف تزریق متن.
    باید درست قبل از شروع ضبط صدا فراخوانی شود.
    """
    global _target_hwnd
    hwnd = user32.GetForegroundWindow()
    if hwnd:
        _target_hwnd = hwnd
    print(f"[Injector] Target window saved: HWND={_target_hwnd}")


def _is_valid_target() -> bool:
    """بررسی معتبر بودن پنجره هدف."""
    global _target_hwnd
    if not _target_hwnd:
        return False
    if not user32.IsWindow(_target_hwnd):
        _target_hwnd = 0
        return False
    return True


def _get_focused_control() -> int:
    """
    پیدا کردن کنترل متنی فعال از طریق AttachThreadInput.
    این کار ضروری است چون GetFocus() فقط در thread پنجره هدف کار می‌کند.
    """
    global _target_hwnd
    if not _is_valid_target():
        return 0

    focused = _target_hwnd
    tid = ctypes.c_ulong(0)
    target_tid = user32.GetWindowThreadProcessId(_target_hwnd, ctypes.byref(tid))
    current_tid = kernel32.GetCurrentThreadId()

    if target_tid and target_tid != current_tid:
        try:
            user32.AttachThreadInput(current_tid, target_tid, True)
            child = user32.GetFocus()
            if child and user32.IsWindow(child):
                focused = child
        except Exception:
            pass
        finally:
            try:
                user32.AttachThreadInput(current_tid, target_tid, False)
            except Exception:
                pass

    return focused


def _focus_target_window() -> tuple[bool, int]:
    """
    بازگردانی فوکوس به پنجره هدف با استفاده از تکنیک AttachThreadInput.
    این تکنیک محدودیت Windows Foreground Lock رو دور می‌زند.
    مقدار بازگشتی: (موفقیت, target_thread_id)
    """
    global _target_hwnd
    if not _is_valid_target():
        return False, 0

    try:
        tid = ctypes.c_ulong(0)
        target_tid = user32.GetWindowThreadProcessId(_target_hwnd, ctypes.byref(tid))
        current_tid = kernel32.GetCurrentThreadId()

        if target_tid and target_tid != current_tid:
            user32.AttachThreadInput(current_tid, target_tid, True)

        user32.SetForegroundWindow(_target_hwnd)
        user32.BringWindowToTop(_target_hwnd)
        time.sleep(0.07)  # کمی صبر تا پنجره فوکوس بگیرد
        return True, target_tid
    except Exception as e:
        print(f"[Injector] Focus restore failed: {e}")
        return False, 0


def _detach_from_target(target_tid: int):
    """جدا کردن thread از پنجره هدف بعد از تزریق متن."""
    if not target_tid:
        return
    try:
        current_tid = kernel32.GetCurrentThreadId()
        if target_tid != current_tid:
            user32.AttachThreadInput(current_tid, target_tid, False)
    except Exception:
        pass


def _get_clipboard_text():
    """دریافت محتوای فعلی متنی کلیپ‌بورد."""
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


def _set_clipboard_text(text: str) -> bool:
    """تنظیم متن در کلیپ‌بورد با تلاش مجدد."""
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
    تزریق متن از طریق کلیپ‌بورد.
    از دو روش به صورت ترکیبی استفاده می‌کند:
    ۱. WM_PASTE مستقیم به کنترل فعال (برای برنامه‌های Win32 استاندارد)
    ۲. AttachThreadInput + Ctrl+V (برای مرورگرها و برنامه‌های مدرن)
    """
    if not text:
        return

    with _injection_lock:
        previous_text = _get_clipboard_text()

        if not _set_clipboard_text(text):
            type_via_unicode(text)
            return

        target_tid = 0
        try:
            # روش ۱: WM_PASTE به کنترل فعال درون پنجره هدف
            # این روش نیازی به تغییر فوکوس ندارد و برای Win32 عالی است
            focused_ctrl = _get_focused_control()
            if focused_ctrl:
                user32.SendMessage(focused_ctrl, WM_PASTE, 0, 0)
                time.sleep(0.02)

            # روش ۲: AttachThreadInput + Ctrl+V
            # برای Chrome، Firefox، Electron، اپ‌های مدرن
            ok, target_tid = _focus_target_window()
            if ok:
                # ارسال Ctrl+V به پنجره هدف
                inputs = (INPUT * 4)(
                    INPUT(type=INPUT_KEYBOARD,
                          _input=INPUT._INPUT(ki=KEYBDINPUT(wVk=VK_CONTROL, wScan=0, dwFlags=0, time=0, dwExtraInfo=0))),
                    INPUT(type=INPUT_KEYBOARD,
                          _input=INPUT._INPUT(ki=KEYBDINPUT(wVk=VK_V, wScan=0, dwFlags=0, time=0, dwExtraInfo=0))),
                    INPUT(type=INPUT_KEYBOARD,
                          _input=INPUT._INPUT(ki=KEYBDINPUT(wVk=VK_V, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=0))),
                    INPUT(type=INPUT_KEYBOARD,
                          _input=INPUT._INPUT(ki=KEYBDINPUT(wVk=VK_CONTROL, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=0))),
                )
                user32.SendInput(4, inputs, ctypes.sizeof(INPUT))
                time.sleep(0.02)

        except Exception as e:
            print(f"[Injector] Clipboard paste error: {e}")
        finally:
            _detach_from_target(target_tid)

        # بازگردانی کلیپ‌بورد قبلی بعد از اندکی تاخیر
        if previous_text is not None:
            def restore():
                time.sleep(0.2)
                _set_clipboard_text(previous_text)
            threading.Thread(target=restore, daemon=True).start()


def type_via_unicode(text: str):
    """
    تایپ مستقیم کاراکترهای یونیکد با SendInput.
    از AttachThreadInput برای تغییر ایمن فوکوس استفاده می‌کند.
    """
    if not text:
        return

    with _injection_lock:
        target_tid = 0
        try:
            ok, target_tid = _focus_target_window()

            for char in text:
                if char == "\n":
                    user32.keybd_event(0x0D, 0, 0, 0)
                    user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)
                    time.sleep(0.005)
                    continue

                code = ord(char)
                inp_down = INPUT(type=INPUT_KEYBOARD)
                inp_down.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0)
                user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))

                inp_up = INPUT(type=INPUT_KEYBOARD)
                inp_up.ki = KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)
                user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))

                time.sleep(0.003)

        except Exception as e:
            print(f"[Injector] Unicode injection error: {e}")
        finally:
            _detach_from_target(target_tid)


def inject_text(text: str):
    """تزریق هوشمند متن بر اساس تنظیمات انتخابی کاربر."""
    if not text:
        return

    method = config.get("injection_method", "clipboard")
    if method == "unicode":
        type_via_unicode(text)
    else:
        paste_via_clipboard(text)
