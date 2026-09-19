import sys
import ctypes
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from app.config import config
from app.version import __version__, __app_name__
from app.core.engine import StreamingSpeechEngine as SpeechEngine
from app.core.hotkey import HotkeyManager
from app.core.updater import check_updates_background, UpdateResult
from app.ui.fonts import load_fonts, FONT_FAMILY
from app.ui.pill_widget import FloatingPillWidget
from app.ui.settings_win import SettingsDialog
from app.ui.tray_icon import SystemTrayManager
from app.ui.theme import create_app_icon
from app.ui.theme_manager import resolve_theme, is_windows_dark_mode, get_colors

MUTEX_NAME = "VoiceToTextWindows_SingleInstance_v2"


def ensure_single_instance():
    k32 = ctypes.windll.kernel32
    mutex = k32.CreateMutexW(None, False, MUTEX_NAME)
    if k32.GetLastError() == 183:
        return None
    return mutex


def apply_global_theme(app: QApplication):
    """اعمال تم سراسری بر اساس تنظیمات کاربر."""
    setting = config.get("theme", "system")
    resolved = resolve_theme(setting)
    colors = get_colors(resolved)

    # تنظیم palette برای سازگاری بهتر
    from PyQt6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["bg"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text_primary"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["bg_card"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["bg_card2"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["text_primary"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text_primary"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)


def main():
    # شناسه یکتای نرم‌افزار برای شناسایی توسط تسک‌بار و تنظیمات ویندوز ۱۱
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MostafaAfrouzi.VoiceToTextWindows.App")
    except Exception:
        pass

    mutex = ensure_single_instance()
    if mutex is None:
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("MostafaAfrouzi")
    app.setQuitOnLastWindowClosed(False)

    # بارگذاری فونت Vazirmatn
    load_fonts()
    app.setFont(QFont(FONT_FAMILY, 12))
    app.setWindowIcon(create_app_icon())
    apply_global_theme(app)

    # موتور Streaming
    engine = SpeechEngine()

    # ویجت شناور
    pill = FloatingPillWidget(engine)
    pill.show()

    # سیستم‌تری با آیکون استاندارد
    tray = SystemTrayManager()
    tray.show()

    # مدیریت settings dialog
    settings_dialog_ref = [None]

    def _on_settings_finished(_):
        settings_dialog_ref[0] = None

    def open_settings():
        if settings_dialog_ref[0] is None:
            dlg = SettingsDialog()
            settings_dialog_ref[0] = dlg

            def on_saved():
                # به‌روزرسانی کلید میانبر
                new_hotkey = config.get("hotkey", "ctrl+alt+v")
                hotkey_mgr.register(new_hotkey)
                # به‌روزرسانی زبان در pill
                cur_lang = config.get("language", "fa-IR")
                pill.lang_btn.setText("FA" if cur_lang.startswith("fa") else "EN")
                # اعمال تم جدید
                apply_global_theme(app)
                tray.refresh_menu()

            dlg.settings_saved.connect(on_saved)
            dlg.finished.connect(_on_settings_finished)

        settings_dialog_ref[0].show()
        settings_dialog_ref[0].raise_()
        settings_dialog_ref[0].activateWindow()

    # کلید میانبر سراسری
    hotkey_mgr = HotkeyManager(on_triggered_callback=lambda: pill.bridge.hotkey_triggered.emit())
    hotkey_mgr.start()

    # اتصال سیگنال‌ها
    tray.toggle_listening_requested.connect(engine.toggle)
    tray.toggle_language_requested.connect(lambda: pill._on_toggle_language())
    tray.open_settings_requested.connect(open_settings)
    pill.open_settings_requested.connect(open_settings)

    def quit_app():
        hotkey_mgr.unregister()
        engine.cancel()
        tray.hide()
        pill.close()
        app.quit()

    tray.quit_requested.connect(quit_app)

    # بررسی بروزرسانی در پس‌زمینه (پس از ۸ ثانیه از اجرا)
    if config.get("check_updates_on_start", True):
        def on_update_found(result: UpdateResult):
            # نمایش اعلان در سیستم‌تری
            tray.showMessage(
                "بروزرسانی موجود است",
                f"نسخه {result.latest_version} در دسترس است. برای نصب روی تنظیمات کلیک کنید.",
                tray.MessageIcon.Information,
                5000
            )
            # اگر settings باز بود آن را نیز آگاه کن
            if settings_dialog_ref[0]:
                settings_dialog_ref[0].notify_update_available(result)

        check_updates_background(
            on_update_available=on_update_found,
            delay_seconds=8.0
        )

    exit_code = app.exec()
    hotkey_mgr.unregister()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
