import os
import unittest
from app.version import __version__, __app_name__
from app.config import config
from app.ui.theme_manager import AppTheme, resolve_theme, get_colors
from app.core.autostart import is_autostart_enabled
from app.core.updater import UpdateResult


class TestSmokeIntegration(unittest.TestCase):
    def test_version_metadata(self):
        self.assertEqual(__version__, "2.1.0")
        self.assertTrue(len(__version__.split(".")) == 3)
        self.assertTrue(len(__app_name__) > 0)

    def test_theme_system_resolution(self):
        # تست تم سیستم
        resolved_sys = resolve_theme(AppTheme.SYSTEM)
        self.assertIn(resolved_sys, [AppTheme.DARK, AppTheme.LIGHT])
        colors = get_colors(resolved_sys)
        self.assertIn("bg", colors)
        self.assertIn("accent", colors)

        # تست تم تاریک
        resolved_dark = resolve_theme(AppTheme.DARK)
        self.assertEqual(resolved_dark, AppTheme.DARK)
        colors_dark = get_colors(resolved_dark)
        self.assertEqual(colors_dark["bg"], "#0d1117")

        # تست تم روشن
        resolved_light = resolve_theme(AppTheme.LIGHT)
        self.assertEqual(resolved_light, AppTheme.LIGHT)
        colors_light = get_colors(resolved_light)
        self.assertEqual(colors_light["bg"], "#ffffff")

    def test_autostart_query(self):
        # بررسی اینکه تابع بدون خطای دسترسی اجرا می‌شود
        status = is_autostart_enabled()
        self.assertIsInstance(status, bool)

    def test_update_result_structure(self):
        res = UpdateResult(has_update=True, latest_version="v2.1.0", download_url="http://test.exe")
        self.assertTrue(res.has_update)
        self.assertEqual(res.latest_version, "v2.1.0")
        self.assertEqual(res.download_url, "http://test.exe")

    def test_installer_files_exist(self):
        self.assertTrue(os.path.isfile(os.path.join("installer", "setup.iss")))
        self.assertTrue(os.path.isfile(os.path.join(".github", "workflows", "release.yml")))
        self.assertTrue(os.path.isfile("build_exe.py"))
        self.assertTrue(os.path.isfile("build_installer.py"))
        self.assertTrue(os.path.isfile("main.py"))
        self.assertTrue(os.path.isfile("README.md"))
        self.assertTrue(os.path.isfile("README_EN.md"))


if __name__ == "__main__":
    unittest.main()
