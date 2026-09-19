from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon
from .theme import create_app_icon
from .fonts import load_fonts, get_font, FONT_FAMILY
from ..config import config
from ..core.autostart import is_autostart_enabled, set_autostart


class SystemTrayManager(QSystemTrayIcon):
    """
    مدیریت آیکون سیستم‌تری ویندوز با منوی دسترسی سریع.
    """

    toggle_listening_requested = pyqtSignal()
    toggle_language_requested = pyqtSignal()
    open_settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(create_app_icon(), parent)
        self.setToolTip("تبدیل گفتار به متن ویندوز ۱۱ (Voice-to-Text)")
        load_fonts()

        self._init_menu()
        self.activated.connect(self._on_tray_activated)

    def _init_menu(self):
        self.menu = QMenu()

        # اکشن شروع / توقف
        hotkey_str = config.get("hotkey", "ctrl+alt+v").upper()
        self.toggle_action = QAction(f"🎤 شروع / توقف تایپ صوتی ({hotkey_str})", self.menu)
        self.toggle_action.triggered.connect(self.toggle_listening_requested.emit)
        self.menu.addAction(self.toggle_action)

        self.menu.addSeparator()

        # زبان فعلی
        cur_lang = config.get("language", "fa-IR")
        lang_text = "🌐 زبان: فارسی" if cur_lang.startswith("fa") else "🌐 Language: English"
        self.lang_action = QAction(lang_text, self.menu)
        self.lang_action.triggered.connect(self.toggle_language_requested.emit)
        self.menu.addAction(self.lang_action)

        # تنظیمات
        self.settings_action = QAction("⚙️ تنظیمات...", self.menu)
        self.settings_action.triggered.connect(self.open_settings_requested.emit)
        self.menu.addAction(self.settings_action)

        # اجرای خودکار با ویندوز
        self.autostart_action = QAction("🚀 اجرای خودکار با ویندوز", self.menu)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(is_autostart_enabled())
        self.autostart_action.triggered.connect(self._on_autostart_toggled)
        self.menu.addAction(self.autostart_action)

        self.menu.addSeparator()

        # خروج
        self.quit_action = QAction("❌ خروج از برنامه", self.menu)
        self.quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)

    def refresh_menu(self):
        hotkey_str = config.get("hotkey", "ctrl+alt+v").upper()
        self.toggle_action.setText(f"🎤 شروع / توقف تایپ صوتی ({hotkey_str})")
        cur_lang = config.get("language", "fa-IR")
        lang_text = "🌐 زبان: فارسی" if cur_lang.startswith("fa") else "🌐 Language: English"
        self.lang_action.setText(lang_text)
        self.autostart_action.setChecked(is_autostart_enabled())

    def _on_autostart_toggled(self, checked: bool):
        set_autostart(checked)
        config.set("autostart", checked)

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick
        ):
            self.toggle_listening_requested.emit()
