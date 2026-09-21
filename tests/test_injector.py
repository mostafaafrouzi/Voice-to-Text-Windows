import unittest
from unittest.mock import patch, MagicMock
from app.core.injector import (
    _get_clipboard_text, _set_clipboard_text,
    _is_desktop_or_taskbar, update_target_window, _focus_target_window
)
import app.core.injector as inj_mod


class TestInjector(unittest.TestCase):
    def test_clipboard_backup_and_restore(self):
        original = "متن تستی قبلی کاربر"
        _set_clipboard_text(original)
        self.assertEqual(_get_clipboard_text(), original)

        new_text = "متن جدید تایپ صوتی"
        _set_clipboard_text(new_text)
        self.assertEqual(_get_clipboard_text(), new_text)

        _set_clipboard_text(original)
        self.assertEqual(_get_clipboard_text(), original)

    def test_desktop_filter(self):
        self.assertTrue(_is_desktop_or_taskbar(0))

    def test_update_target_window_ignores_our_process(self):
        # تست اینکه پنجره‌های متعلق به خود برنامه، پنجره هدف را خراب نمی‌کنند
        with patch.object(inj_mod.user32, "GetForegroundWindow", return_value=1111), \
             patch.object(inj_mod.user32, "IsWindow", return_value=True), \
             patch.object(inj_mod.kernel32, "GetCurrentProcessId", return_value=9999), \
             patch("app.core.injector._is_desktop_or_taskbar", return_value=False):

            # شبیه‌سازی پنجره خارجی (مثلاً نوت‌پد با PID=5555)
            def mock_get_pid_notepad(hwnd, byref_pid):
                byref_pid._obj.value = 5555
                return 1

            with patch.object(inj_mod.user32, "GetWindowThreadProcessId", side_effect=mock_get_pid_notepad):
                target = update_target_window()
                self.assertEqual(target, 1111)

            # حالا فوکوس به ویجت خود برنامه تغییر می‌کند (PID=9999)
            def mock_get_pid_our_app(hwnd, byref_pid):
                byref_pid._obj.value = 9999
                return 1

            with patch.object(inj_mod.user32, "GetWindowThreadProcessId", side_effect=mock_get_pid_our_app), \
                 patch.object(inj_mod.user32, "GetForegroundWindow", return_value=2222):
                target = update_target_window()
                # هدف باید همچنان همان پنجره خارجی نوت‌پد (1111) باقی بماند
                self.assertEqual(target, 1111)

    def test_update_target_window_switches_between_external_apps(self):
        # تست سناریوی کاربر: سوئیچ از نوت‌پد به تلگرام بدون بستن برنامه
        with patch.object(inj_mod.user32, "IsWindow", return_value=True), \
             patch.object(inj_mod.kernel32, "GetCurrentProcessId", return_value=9999), \
             patch("app.core.injector._is_desktop_or_taskbar", return_value=False):

            # 1. کاربر در نوت‌پد است (HWND=1001, PID=1100)
            def mock_notepad(hwnd, byref_pid):
                byref_pid._obj.value = 1100
                return 1

            with patch.object(inj_mod.user32, "GetForegroundWindow", return_value=1001), \
                 patch.object(inj_mod.user32, "GetWindowThreadProcessId", side_effect=mock_notepad):
                target1 = update_target_window()
                self.assertEqual(target1, 1001)

            # 2. کاربر بدون توقف به تلگرام می‌رود (HWND=2002, PID=2200)
            def mock_telegram(hwnd, byref_pid):
                byref_pid._obj.value = 2200
                return 1

            with patch.object(inj_mod.user32, "GetForegroundWindow", return_value=2002), \
                 patch.object(inj_mod.user32, "GetWindowThreadProcessId", side_effect=mock_telegram):
                target2 = update_target_window()
                # هدف بلافاصله به تلگرام سوئیچ می‌کند
                self.assertEqual(target2, 2002)


if __name__ == "__main__":
    unittest.main()
