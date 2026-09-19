import threading
import keyboard
from ..config import config


class HotkeyManager:
    """
    مدیریت کلیدهای میانبر سراسری ویندوز با قابلیت تغییر پویا در زمان اجرا.
    """

    def __init__(self, on_triggered_callback=None):
        self.on_triggered = on_triggered_callback
        self._current_hotkey = None
        self._lock = threading.Lock()

    def start(self):
        hotkey_str = config.get("hotkey", "ctrl+alt+v")
        self.register(hotkey_str)

    def register(self, hotkey_str: str) -> bool:
        with self._lock:
            if not hotkey_str:
                return False

            if self._current_hotkey:
                try:
                    keyboard.remove_hotkey(self._current_hotkey)
                except Exception:
                    pass
                self._current_hotkey = None

            try:
                # ثبت کلید میانبر جدید
                keyboard.add_hotkey(
                    hotkey_str,
                    self._on_hotkey_pressed,
                    suppress=False,
                    trigger_on_release=False
                )
                self._current_hotkey = hotkey_str
                print(f"[Hotkey] Successfully registered global hotkey: {hotkey_str}")
                return True
            except Exception as e:
                print(f"[Hotkey] Failed to register hotkey '{hotkey_str}': {e}")
                return False

    def unregister(self):
        with self._lock:
            if self._current_hotkey:
                try:
                    keyboard.remove_hotkey(self._current_hotkey)
                except Exception:
                    pass
                self._current_hotkey = None

    def _on_hotkey_pressed(self):
        if self.on_triggered:
            try:
                self.on_triggered()
            except Exception as e:
                print(f"[Hotkey] Callback error: {e}")
