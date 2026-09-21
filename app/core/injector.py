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
VK_MENU = 0x12     # Alt
VK_SHIFT = 0x10
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1

# HWND پنجره هدف که درست قبل از شروع ضبط ذخیره می‌شود
_target_hwnd: int = 0
_injection_lock = threading.Lock()

# لیست تجمیعی متون دیکته‌شده در نشست جاری (برای حالت فقط کلیپ‌بورد)
_session_clipboard_parts: list[str] = []


def _safe_print(msg: str):
    """چاپ ایمن لاگ بدون خطای انکودینگ در کنسول‌های مختلف ویندوز."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode("ascii", errors="backslashreplace").decode("ascii"))
        except Exception:
            pass


# ساختارهای استاندارد ۴۰-بایتی SendInput برای ویندوز ۶۴-بیتی
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


LPINPUT = INPUT * 2


def start_new_session():
    """شروع نشست جدید: بافر تجمیعی کلیپ‌بورد را پاکسازی می‌کند."""
    global _session_clipboard_parts
    with _injection_lock:
        _session_clipboard_parts.clear()


def save_target_window():
    """
    ذخیره HWND پنجره فعال کاربر به عنوان مقصد تایپ و تزریق متن.
    پنجره‌های متعلق به پردازه خود برنامه نادیده گرفته می‌شوند تا فوکوس کاربر حفظ شود.
    """
    global _target_hwnd
    hwnd = user32.GetForegroundWindow()
    if hwnd:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value != kernel32.GetCurrentProcessId():
            _target_hwnd = hwnd
            print(f"[Injector] Target window saved: HWND={_target_hwnd}")
        else:
            print(f"[Injector] Foreground window is our own process, keeping previous target HWND={_target_hwnd}")


def _focus_target_window() -> bool:
    """بازگردانی هوشمند فوکوس به پنجره هدف کاربر بدون پرش بیهوده."""
    global _target_hwnd
    if not _target_hwnd or not user32.IsWindow(_target_hwnd):
        return False

    fg = user32.GetForegroundWindow()
    if fg == _target_hwnd:
        return True

    try:
        tid_buf = ctypes.c_ulong(0)
        target_tid = user32.GetWindowThreadProcessId(_target_hwnd, ctypes.byref(tid_buf))
        current_tid = kernel32.GetCurrentThreadId()

        attached = False
        if target_tid and target_tid != current_tid:
            attached = bool(user32.AttachThreadInput(current_tid, target_tid, True))

        user32.SetForegroundWindow(_target_hwnd)
        user32.BringWindowToTop(_target_hwnd)
        time.sleep(0.04)

        if attached:
            user32.AttachThreadInput(current_tid, target_tid, False)

        return True
    except Exception as e:
        print(f"[Injector] Focus restore failed: {e}")
        return False


def _ensure_modifiers_released():
    """اطمینان از رها بودن کلیدهای کنترل، الت و شیفت قبل از درج متن."""
    for vk in (VK_CONTROL, VK_MENU, VK_SHIFT):
        if user32.GetAsyncKeyState(vk) & 0x8000:
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def _send_ctrl_v():
    """ارسال تمیز کلیدهای میانبر Ctrl+V برای پیست در پنجره فعال."""
    _ensure_modifiers_released()
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.03)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def _get_clipboard_text() -> str | None:
    """دریافت متن فعلی کلیپ‌بورد با چند بار تلاش."""
    for _ in range(5):
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return None
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            time.sleep(0.02)
    return None


def _set_clipboard_text(text: str) -> bool:
    """قرار دادن متن در کلیپ‌بورد با قفل‌گشایی ایمن و تلاش مجدد."""
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
            time.sleep(0.02)
    return False


def copy_to_clipboard_only(text: str):
    """
    حالت اختصاصی «فقط کلیپ‌بورد»:
    متن گفتار را فقط در کلیپ‌بورد ذخیره و تجمیع می‌کند و هیچ کلیدی به پنجره کاربر نمی‌فرستد.
    """
    global _session_clipboard_parts
    if not text:
        return

    with _injection_lock:
        _session_clipboard_parts.append(text)
        full_session_text = "".join(_session_clipboard_parts).strip()
        if _set_clipboard_text(full_session_text):
            _safe_print(f"[Injector] Copied to clipboard ONLY (session length: {len(full_session_text)}): '{full_session_text[:35]}...'")
        else:
            _safe_print("[Injector] Failed to set clipboard in copy_to_clipboard_only")


def paste_via_clipboard(text: str):
    """
    تزریق فوق‌سریع، هوشمند و ۱۰۰٪ بدون خطای متن به محل نشانگر در پنجره فعال کاربر.
    این روش کامل‌ترین سازگاری را با نگارش فارسی (RTL)، حروف چسبان، نیم‌فاصله‌ها
    و ادیتورهای مدرن (VSCode, Notepad Win11, Office, Telegram, Chrome) دارد
    و از به هم ریختگی، تکرار حروف یا تداخل با AutoComplete جلوگیری می‌کند.
    """
    if not text:
        return

    with _injection_lock:
        if not _set_clipboard_text(text):
            _safe_print("[Injector] Failed to set clipboard text, falling back to SendInput")
            type_via_sendinput(text)
            return

        _focus_target_window()
        _send_ctrl_v()
        time.sleep(0.04)
        _safe_print(f"[Injector] Successfully injected into active window: '{text[:30]}...'")


def type_via_sendinput(text: str):
    """
    تایپ کاراکتر به کاراکتر با SendInput اتمیک (KeyDown + KeyUp در یک فراخوانی).
    دارای وقفه ۱۵ میلی‌ثانیه‌ای برای پردازش صحیح اتصالات فارسی در ادیتورها.
    """
    if not text:
        return

    _ensure_modifiers_released()
    _focus_target_window()

    for char in text:
        if char == "\n":
            user32.keybd_event(0x0D, 0, 0, 0)
            time.sleep(0.01)
            user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)
            continue

        code = ord(char)
        if code <= 0xFFFF:
            inp = LPINPUT(
                INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=None))),
                INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)))
            )
            user32.SendInput(2, inp, ctypes.sizeof(INPUT))
        else:
            surrogates = char.encode("utf-16le")
            for i in range(0, len(surrogates), 2):
                scan = surrogates[i] | (surrogates[i + 1] << 8)
                inp = LPINPUT(
                    INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(wVk=0, wScan=scan, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=None))),
                    INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(wVk=0, wScan=scan, dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=None)))
                )
                user32.SendInput(2, inp, ctypes.sizeof(INPUT))

        time.sleep(0.015)

    _safe_print(f"[Injector] SendInput typed: '{text[:30]}...'")


def type_direct(text: str):
    """سازگاری با فراخوانی‌های مستقیم."""
    paste_via_clipboard(text)


def inject_text(text: str):
    """
    تزریق هوشمند متن بر اساس تنظیمات انتخابی کاربر:
    - direct / auto / paste: تایپ آنی و بی‌نقص در برنامه فعال (مانند Gboard)
    - clipboard / clipboard_only: فقط ذخیره در کلیپ‌بورد بدون هیچ‌گونه تایپ در پنجره
    - unicode / sendinput: شبیه‌سازی صفحه‌کلید با SendInput
    """
    if not text:
        return

    method = config.get("injection_method", "direct")
    _safe_print(f"[Injector] inject_text called: method={method}, text='{text[:30]}...'")

    if method in ("clipboard", "clipboard_only"):
        copy_to_clipboard_only(text)
    elif method in ("unicode", "sendinput"):
        type_via_sendinput(text)
    else:
        paste_via_clipboard(text)
