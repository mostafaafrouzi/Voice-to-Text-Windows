from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer
from PyQt6.QtGui import QFont, QColor, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QScrollArea,
    QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QSlider, QMessageBox, QWidget,
    QFrame, QProgressBar, QTabWidget
)
from .theme import create_app_icon
from .fonts import load_fonts, get_font, FONT_FAMILY
from .theme_manager import AppTheme, resolve_theme, is_windows_dark_mode, build_settings_style, get_colors
from ..config import config
from ..core.audio_meter import get_input_devices
from ..core.autostart import is_autostart_enabled, set_autostart
from ..core.updater import check_for_updates, download_and_install_update, UpdateResult
from ..version import __version__, __github_url__

# کلیدهای رزرو شده ویندوز که نمی‌توان override کرد
RESERVED_HOTKEYS = {
    "ctrl+alt+del", "win+l", "win+d", "alt+f4", "alt+tab", "alt+shift+tab",
    "win+r", "win+e", "win+i", "win+p", "win+a", "win+s", "win+x",
    "win+tab", "ctrl+shift+esc", "printscreen", "ctrl+esc"
}

# نگاشت کد کلید Qt به نام میانبر
KEY_NAMES = {
    Qt.Key.Key_Control: "ctrl",
    Qt.Key.Key_Alt: "alt",
    Qt.Key.Key_Shift: "shift",
    Qt.Key.Key_Meta: "win",
    Qt.Key.Key_Return: "enter",
    Qt.Key.Key_Enter: "enter",
    Qt.Key.Key_Escape: "esc",
    Qt.Key.Key_Backspace: "backspace",
    Qt.Key.Key_Delete: "delete",
    Qt.Key.Key_Tab: "tab",
    Qt.Key.Key_Space: "space",
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
    Qt.Key.Key_Up: "up",
    Qt.Key.Key_Down: "down",
    Qt.Key.Key_Home: "home",
    Qt.Key.Key_End: "end",
    Qt.Key.Key_PageUp: "pageup",
    Qt.Key.Key_PageDown: "pagedown",
    Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_CapsLock: "capslock",
    Qt.Key.Key_F1: "f1",  Qt.Key.Key_F2: "f2",  Qt.Key.Key_F3: "f3",
    Qt.Key.Key_F4: "f4",  Qt.Key.Key_F5: "f5",  Qt.Key.Key_F6: "f6",
    Qt.Key.Key_F7: "f7",  Qt.Key.Key_F8: "f8",  Qt.Key.Key_F9: "f9",
    Qt.Key.Key_F10: "f10", Qt.Key.Key_F11: "f11", Qt.Key.Key_F12: "f12",
}

MODIFIER_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Alt,
    Qt.Key.Key_Shift, Qt.Key.Key_Meta
}


class HotkeyRecorderWidget(QWidget):
    """
    ویجت تعریف میانبر به سبک گفتار-محور — کاربر روی دکمه کلیک می‌کند
    سپس کلیدهای دلخواه را فشار می‌دهد. میانبر بلافاصله ثبت می‌شود.
    """
    hotkey_changed = pyqtSignal(str)  # نوشته جدید به فرم pynput (ctrl+alt+v)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._recording = False
        self._current_keys = set()
        self._recorded_hotkey = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.display_label = QLabel()
        self.display_label.setObjectName("HotkeyDisplay")
        self.display_label.setMinimumWidth(180)
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display_label.setFont(get_font(12, QFont.Weight.Bold))
        layout.addWidget(self.display_label, 1)

        self.record_btn = QPushButton("تغییر")
        self.record_btn.setObjectName("RecordHotkeyBtn")
        self.record_btn.setFixedSize(64, 32)
        self.record_btn.setFont(get_font(11))
        self.record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self.record_btn)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._update_display()

    def get_hotkey(self) -> str:
        return self._recorded_hotkey

    def set_hotkey(self, hotkey: str):
        self._recorded_hotkey = hotkey.strip().lower()
        self._update_display()

    def _toggle_recording(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._recording = True
        self._current_keys = set()
        self.display_label.setText("کلیدهای دلخواه را فشار دهید...")
        self.record_btn.setText("لغو")
        self.display_label.setStyleSheet("background: rgba(47,129,247,0.12); border: 1.5px solid rgba(47,129,247,0.5); border-radius: 8px; padding: 4px 10px;")
        self.setFocus()

    def _stop_recording(self):
        self._recording = False
        self._current_keys = set()
        self.record_btn.setText("تغییر")
        self.display_label.setStyleSheet("")
        self._update_display()

    def _update_display(self):
        if self._recorded_hotkey:
            self.display_label.setText(self._recorded_hotkey.upper())
        else:
            self.display_label.setText("میانبر تعریف نشده")

    def keyPressEvent(self, event: QKeyEvent):
        if not self._recording:
            super().keyPressEvent(event)
            return

        key = Qt.Key(event.key())
        if key == Qt.Key.Key_Escape:
            self._stop_recording()
            return

        self._current_keys.add(key)
        self._show_live_keys()

        # اگر یک کلید غیر-مودیفایر فشار داده شد، ترکیب کامل است
        if key not in MODIFIER_KEYS:
            hotkey = self._build_hotkey()
            if hotkey:
                self._recorded_hotkey = hotkey
                QTimer.singleShot(250, self._finish_recording)

    def keyReleaseEvent(self, event: QKeyEvent):
        if not self._recording:
            super().keyReleaseEvent(event)
            return
        key = Qt.Key(event.key())
        self._current_keys.discard(key)

    def _show_live_keys(self):
        if self._current_keys:
            self.display_label.setText(self._build_hotkey_from_keys(self._current_keys).upper() or "کلیدهای دلخواه را فشار دهید...")

    def _finish_recording(self):
        self._recording = False
        self._current_keys = set()
        self.record_btn.setText("تغییر")
        self.display_label.setStyleSheet("")
        self._update_display()
        self.hotkey_changed.emit(self._recorded_hotkey)

    def _build_hotkey(self) -> str:
        return self._build_hotkey_from_keys(self._current_keys)

    def _build_hotkey_from_keys(self, keys: set) -> str:
        parts = []
        # اضافه کردن modifier ها به ترتیب استاندارد
        if Qt.Key.Key_Control in keys: parts.append("ctrl")
        if Qt.Key.Key_Alt in keys: parts.append("alt")
        if Qt.Key.Key_Shift in keys: parts.append("shift")
        if Qt.Key.Key_Meta in keys: parts.append("win")
        # اضافه کردن کلیدهای غیر-مودیفایر
        for key in keys:
            if key in MODIFIER_KEYS:
                continue
            name = KEY_NAMES.get(key)
            if name:
                parts.append(name)
            else:
                ch = chr(key).lower() if 32 <= key <= 126 else None
                if ch:
                    parts.append(ch)
        return "+".join(parts) if len(parts) >= 1 else ""


class UpdateCheckerThread(QThread):
    result_ready = Signal(object)

    def run(self):
        result = check_for_updates(timeout=10)
        self.result_ready.emit(result)


class SectionCard(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("SectionCard")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        lbl = QLabel(title)
        lbl.setFont(get_font(12, QFont.Weight.Bold))
        lbl.setObjectName("CardTitle")
        lbl.setStyleSheet("background: transparent;")
        outer.addWidget(lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("CardLine")
        outer.addWidget(line)

        self.body = QWidget()
        self.body.setStyleSheet("background: transparent;")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 2, 0, 0)
        self.body_layout.setSpacing(10)
        outer.addWidget(self.body)

def _get_check_icon_path() -> str:
    import os, sys
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base, "assets", "check.png")
    return p.replace("\\", "/")


class SettingsDialog(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        load_fonts()
        self.setWindowTitle(f"تنظیمات — Voice-to-Text Windows v{__version__}")
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(520, 680)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setFont(get_font(12))

        self._update_thread = None
        self._pending_download_url = ""

        self._init_ui()
        self._apply_theme()
        self._load_values()

    def _get_theme_colors(self, theme_choice: str = None):
        setting = theme_choice if theme_choice is not None else config.get("theme", "system")
        resolved = resolve_theme(setting)
        return get_colors(resolved), resolved

    def _apply_theme(self, theme_choice: str = None):
        colors, _ = self._get_theme_colors(theme_choice)
        self.setStyleSheet(self._build_full_style(colors))

    def _on_theme_selection_changed(self, index: int):
        theme_choice = self.theme_combo.currentData()
        if theme_choice:
            self._apply_theme(theme_choice)

    def _build_full_style(self, c: dict) -> str:
        check_path = _get_check_icon_path()
        return f"""
QDialog {{
    background-color: {c["bg"]};
    color: {c["text_primary"]};
    font-family: '{FONT_FAMILY}', Tahoma, 'Segoe UI';
}}
QWidget#SettingsHeader {{
    background-color: {c["bg_card"]};
    border-bottom: 1px solid {c["border"]};
}}
QWidget#SettingsBody {{
    background-color: {c["bg"]};
}}
QWidget#SettingsFooter {{
    background-color: {c["bg_card"]};
    border-top: 1px solid {c["border"]};
}}
QWidget#SectionCard {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border"]};
    border-radius: 12px;
}}
#CardTitle {{ color: {c["accent"]}; }}
#CardLine {{ background-color: {c["border"]}; border: none; max-height: 1px; }}
QLabel {{ color: {c["text_secondary"]}; background: transparent; }}
QLabel#HeaderTitle {{ color: {c["text_primary"]}; font-size: 17px; font-weight: 700; }}
QLabel#HeaderSub {{ color: {c["text_muted"]}; font-size: 12px; }}
QLabel#VersionLabel {{ color: {c["text_muted"]}; font-size: 11px; }}
QLabel#SettingsHint {{ color: {c["text_muted"]}; font-size: 11px; }}
QLabel#ChunkLbl {{ color: {c["mic_listening"]}; font-size: 11px; font-weight: bold; min-width: 70px; }}
QLabel#SilenceLbl {{ color: {c["accent"]}; font-size: 11px; font-weight: bold; min-width: 70px; }}
QLabel#HotkeyWarn {{ color: #f85149; font-size: 11px; }}

QLineEdit, QComboBox {{
    background-color: {c["bg"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    color: {c["text_primary"]};
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: {c["accent"]};
    selection-color: #ffffff;
}}
QLineEdit:focus, QComboBox:focus, QComboBox:hover {{
    border-color: {c["accent"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 26px;
}}
QComboBox QAbstractItemView {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    color: {c["text_primary"]};
    selection-background-color: {c["accent"]};
    selection-color: #ffffff;
    padding: 4px;
    outline: 0px;
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding: 4px 10px;
    color: {c["text_primary"]};
    background-color: {c["bg_card"]};
    border-radius: 4px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {c["accent"]};
    color: #ffffff;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {c["accent"]};
    color: #ffffff;
}}
QCheckBox {{
    color: {c["text_primary"]};
    spacing: 10px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid {c["border"]};
    background-color: {c["bg"]};
}}
QCheckBox::indicator:hover {{
    border-color: {c["accent"]};
}}
QCheckBox::indicator:checked {{
    background-color: {c["accent"]};
    border-color: {c["accent"]};
    image: url({check_path});
}}
QPushButton#PrimaryBtn {{
    background-color: {c["accent"]};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 0 18px;
    font-weight: bold;
}}
QPushButton#PrimaryBtn:hover {{
    background-color: {c["accent_hover"]};
}}
QPushButton#PrimaryBtn:pressed {{
    background-color: {c["accent_dark"]};
}}
QPushButton#PrimaryBtn:disabled {{
    background-color: {c["border"]};
    color: {c["text_muted"]};
}}
QPushButton#SecondaryBtn {{
    background-color: transparent;
    color: {c["text_secondary"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    padding: 0 16px;
}}
QPushButton#SecondaryBtn:hover {{
    background-color: rgba(127, 127, 127, 0.09);
    color: {c["text_primary"]};
    border-color: {c["text_muted"]};
}}
QPushButton#SecondaryBtn:disabled {{
    color: {c["text_muted"]};
}}
QSlider::groove:horizontal {{
    height: 4px;
    background: {c["border"]};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {c["accent"]};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {c["text_primary"]};
    border: 2px solid {c["accent"]};
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent;
    width: 5px;
    border-radius: 2px;
}}
QScrollBar::handle:vertical {{
    background: {c["border"]};
    border-radius: 2px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QProgressBar {{
    border: 1px solid {c["border"]};
    border-radius: 6px;
    background: {c["bg_card"]};
    height: 12px;
    text-align: center;
    color: {c["text_primary"]};
    font-size: 10px;
}}
QProgressBar::chunk {{
    background: {c["accent"]};
    border-radius: 6px;
}}
QLabel#HotkeyDisplay {{
    background-color: {c["bg"]};
    border: 1.5px solid {c["border"]};
    border-radius: 8px;
    color: {c["text_primary"]};
    padding: 6px 14px;
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 1px;
}}
QPushButton#RecordHotkeyBtn {{
    background-color: transparent;
    color: {c["accent"]};
    border: 1.5px solid {c["accent"]};
    border-radius: 7px;
    padding: 0 10px;
    font-weight: bold;
}}
QPushButton#RecordHotkeyBtn:hover {{
    background-color: {c["accent"]};
    color: #ffffff;
}}
"""

    def _make_btn(self, text: str, primary: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("PrimaryBtn" if primary else "SecondaryBtn")
        btn.setFont(get_font(12, QFont.Weight.Bold if primary else QFont.Weight.Normal))
        btn.setFixedHeight(36)
        btn.setMinimumWidth(110)
        return btn

    def _make_combo(self, width: int = 230) -> QComboBox:
        from PyQt6.QtWidgets import QListView
        c = QComboBox()
        c.setView(QListView())
        c.setFont(get_font(12))
        c.setMinimumWidth(width)
        return c

    def _make_lineedit(self, placeholder: str = "") -> QLineEdit:
        e = QLineEdit()
        e.setFont(get_font(12))
        e.setPlaceholderText(placeholder)
        return e

    def _make_check(self, text: str) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setFont(get_font(12))
        return cb

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(get_font(12))
        return lbl

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ===== هدر =====
        header = QWidget()
        header.setObjectName("SettingsHeader")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(22, 16, 22, 16)
        hl.setSpacing(2)

        hr = QHBoxLayout()
        title_lbl = QLabel("تنظیمات")
        title_lbl.setObjectName("HeaderTitle")
        title_lbl.setFont(get_font(17, QFont.Weight.Bold))
        hr.addWidget(title_lbl)
        hr.addStretch()

        ver_lbl = QLabel(f"v{__version__}")
        ver_lbl.setObjectName("VersionLabel")
        ver_lbl.setFont(get_font(10))
        hr.addWidget(ver_lbl)
        hl.addLayout(hr)

        sub = QLabel("تایپ صوتی هوشمند ویندوز ۱۱")
        sub.setObjectName("HeaderSub")
        sub.setFont(get_font(12))
        hl.addWidget(sub)
        root.addWidget(header)

        # ===== بدنه اسکرول‌دار =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("SettingsBody")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(18, 16, 18, 16)
        bl.setSpacing(12)

        # ---- کارت ۱: تشخیص گفتار ----
        c1 = SectionCard("🎙 تشخیص گفتار و زبان")
        row = QHBoxLayout(); row.addWidget(self._make_label("زبان پیش‌فرض:"))
        self.lang_combo = self._make_combo()
        self.lang_combo.addItem("🇮🇷  فارسی ایران (Persian)", "fa-IR")
        self.lang_combo.addItem("🇺🇸  English (United States)", "en-US")
        row.addWidget(self.lang_combo); c1.body_layout.addLayout(row)

        row2 = QHBoxLayout(); row2.addWidget(self._make_label("میکروفون:"))
        self.mic_combo = self._make_combo()
        self._fill_microphones()
        row2.addWidget(self.mic_combo); c1.body_layout.addLayout(row2)

        self.punct_check = self._make_check("تبدیل کلمات نگارشی صوتی (نقطه، ویرگول، علامت سوال...)")
        self.half_space_check = self._make_check("اعمال نیم‌فاصله فارسی (می‌رود، کتاب‌ها...)")
        self.digits_check = self._make_check("ارقام فارسی (۱۲۳ به جای 123)")
        c1.body_layout.addWidget(self.punct_check)
        c1.body_layout.addWidget(self.half_space_check)
        c1.body_layout.addWidget(self.digits_check)
        bl.addWidget(c1)

        # ---- کارت ۲: Streaming ----
        c2 = SectionCard("⚡ Streaming (تبدیل همزمان مثل Gboard)")
        hint = QLabel("هر چند ثانیه یک قطعه صوتی به Google ارسال شده و متن بلافاصله تایپ می‌شود.")
        hint.setObjectName("SettingsHint")
        hint.setFont(get_font(11)); hint.setWordWrap(True)
        c2.body_layout.addWidget(hint)

        row_ch = QHBoxLayout(); row_ch.addWidget(self._make_label("طول هر قطعه:"))
        self.chunk_lbl = QLabel("۱.۵ ثانیه")
        self.chunk_lbl.setObjectName("ChunkLbl")
        self.chunk_slider = QSlider(Qt.Orientation.Horizontal)
        self.chunk_slider.setRange(10, 40)
        self.chunk_slider.valueChanged.connect(lambda v: self.chunk_lbl.setText(f"{'%.1f' % (v/10)} ثانیه"))
        row_ch.addWidget(self.chunk_slider); row_ch.addWidget(self.chunk_lbl)
        c2.body_layout.addLayout(row_ch)

        self.auto_stop_check = self._make_check("توقف خودکار ضبط پس از سکوت")
        c2.body_layout.addWidget(self.auto_stop_check)

        row_s = QHBoxLayout(); row_s.addWidget(self._make_label("مدت سکوت:"))
        self.silence_lbl = QLabel("۰.۸ ثانیه")
        self.silence_lbl.setObjectName("SilenceLbl")
        self.silence_slider = QSlider(Qt.Orientation.Horizontal)
        self.silence_slider.setRange(5, 25)
        self.silence_slider.valueChanged.connect(lambda v: self.silence_lbl.setText(f"{'%.1f' % (v/10)} ثانیه"))
        row_s.addWidget(self.silence_slider); row_s.addWidget(self.silence_lbl)
        c2.body_layout.addLayout(row_s)
        bl.addWidget(c2)

        # ---- کارت ۳: میانبر ----
        c3 = SectionCard("⌨ کلید میانبر سراسری")

        hk_hint = QLabel("برای تعریف میانبر، روی دکمه 'تغییر' کلیک کنید سپس کلیدهای دلخواه را فشار دهید.")
        hk_hint.setObjectName("SettingsHint")
        hk_hint.setFont(get_font(11))
        hk_hint.setWordWrap(True)
        c3.body_layout.addWidget(hk_hint)

        row_hk = QHBoxLayout()
        row_hk.addWidget(self._make_label("کلید میانبر:"))
        self.hotkey_recorder = HotkeyRecorderWidget()
        self.hotkey_recorder.hotkey_changed.connect(self._validate_hotkey_recorder)
        row_hk.addWidget(self.hotkey_recorder, 1)
        c3.body_layout.addLayout(row_hk)

        self.hotkey_warn = QLabel("")
        self.hotkey_warn.setObjectName("HotkeyWarn")
        self.hotkey_warn.setFont(get_font(11))
        self.hotkey_warn.setWordWrap(True)
        c3.body_layout.addWidget(self.hotkey_warn)

        row_inj = QHBoxLayout(); row_inj.addWidget(self._make_label("روش درج متن:"))
        self.inject_combo = self._make_combo()
        self.inject_combo.addItem("📋 کلیپ‌بورد (پیشنهادی)", "clipboard")
        self.inject_combo.addItem("⌨ یونیکد مستقیم (SendInput)", "unicode")
        row_inj.addWidget(self.inject_combo); c3.body_layout.addLayout(row_inj)
        bl.addWidget(c3)

        # ---- کارت ۴: ظاهر و سیستم ----
        c4 = SectionCard("🎨 ظاهر و سیستم")
        row_th = QHBoxLayout(); row_th.addWidget(self._make_label("تم رنگی:"))
        self.theme_combo = self._make_combo()
        self.theme_combo.addItem("🌗 پیروی از تنظیمات ویندوز (پیشنهادی)", "system")
        self.theme_combo.addItem("🌑 تاریک (Dark)", "dark")
        self.theme_combo.addItem("🌕 روشن (Light)", "light")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_selection_changed)
        row_th.addWidget(self.theme_combo); c4.body_layout.addLayout(row_th)

        self.sounds_check = self._make_check("افکت صوتی هنگام شروع/پایان ضبط")
        self.autostart_check = self._make_check("اجرای خودکار با روشن شدن ویندوز")
        self.update_on_start_check = self._make_check("بررسی بروزرسانی هنگام راه‌اندازی (پیش‌فرض: فعال)")
        c4.body_layout.addWidget(self.sounds_check)
        c4.body_layout.addWidget(self.autostart_check)
        c4.body_layout.addWidget(self.update_on_start_check)
        bl.addWidget(c4)

        # ---- کارت ۵: بروزرسانی ----
        c5 = SectionCard("🔄 بروزرسانی برنامه")
        self.update_status_lbl = QLabel(f"نسخه فعلی: v{__version__}")
        self.update_status_lbl.setFont(get_font(12))
        self.update_status_lbl.setWordWrap(True)
        c5.body_layout.addWidget(self.update_status_lbl)

        self.update_progress = QProgressBar()
        self.update_progress.setVisible(False)
        self.update_progress.setFixedHeight(12)
        c5.body_layout.addWidget(self.update_progress)

        upd_row = QHBoxLayout()
        self.check_update_btn = self._make_btn("بررسی بروزرسانی")
        self.check_update_btn.clicked.connect(self._manual_check_update)
        self.download_update_btn = self._make_btn("دانلود و نصب", primary=True)
        self.download_update_btn.setVisible(False)
        self.download_update_btn.clicked.connect(self._start_download)
        upd_row.addWidget(self.check_update_btn)
        upd_row.addWidget(self.download_update_btn)
        upd_row.addStretch()
        c5.body_layout.addLayout(upd_row)

        gh_btn = self._make_btn("صفحه GitHub ↗")
        gh_btn.clicked.connect(lambda: __import__('webbrowser').open(__github_url__))
        c5.body_layout.addWidget(gh_btn)
        bl.addWidget(c5)

        bl.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

        # ===== فوتر =====
        footer = QWidget()
        footer.setObjectName("SettingsFooter")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(18, 10, 18, 10)
        fl.setSpacing(8)
        fl.addStretch()

        cancel_btn = self._make_btn("انصراف")
        cancel_btn.clicked.connect(self.reject)

        save_btn = self._make_btn("ذخیره تنظیمات", primary=True)
        save_btn.clicked.connect(self._save_values)

        fl.addWidget(cancel_btn)
        fl.addWidget(save_btn)
        root.addWidget(footer)

    def _fill_microphones(self):
        self.mic_combo.clear()
        self.mic_combo.addItem("میکروفون پیش‌فرض ویندوز", None)
        for dev in get_input_devices():
            self.mic_combo.addItem(dev["name"], dev["index"])

    def _validate_hotkey_recorder(self, hotkey: str):
        """بررسی معتبر بودن کلید میانبر ضبط‌شده."""
        normalized = hotkey.strip().lower().replace(" ", "")
        if normalized in RESERVED_HOTKEYS:
            self.hotkey_warn.setText(
                f"⚠ این کلید ({hotkey.strip()}) توسط ویندوز رزرو شده است."
                "لطفاً ترکیب دیگری مانند Ctrl+Alt+V یا F8 انتخاب کنید."
            )
        else:
            self.hotkey_warn.setText("")

    def _load_values(self):
        idx = self.lang_combo.findData(config.get("language", "fa-IR"))
        if idx >= 0: self.lang_combo.setCurrentIndex(idx)
        idx = self.mic_combo.findData(config.get("microphone_index"))
        if idx >= 0: self.mic_combo.setCurrentIndex(idx)
        self.punct_check.setChecked(bool(config.get("enable_persian_punctuation", True)))
        self.half_space_check.setChecked(bool(config.get("enable_half_space", True)))
        self.digits_check.setChecked(bool(config.get("persian_digits", False)))
        self.chunk_slider.setValue(max(10, min(40, int(float(config.get("stream_chunk_secs", 1.5)) * 10))))
        self.auto_stop_check.setChecked(bool(config.get("auto_stop_on_silence", True)))
        self.silence_slider.setValue(max(5, min(25, int(float(config.get("silence_timeout", 0.8)) * 10))))
        self.hotkey_recorder.set_hotkey(config.get("hotkey", "ctrl+alt+v"))
        idx = self.inject_combo.findData(config.get("injection_method", "clipboard"))
        if idx >= 0: self.inject_combo.setCurrentIndex(idx)
        self.theme_combo.blockSignals(True)
        idx = self.theme_combo.findData(config.get("theme", "system"))
        if idx >= 0: self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.blockSignals(False)
        self.sounds_check.setChecked(bool(config.get("audio_feedback", True)))
        self.autostart_check.setChecked(is_autostart_enabled())
        self.update_on_start_check.setChecked(bool(config.get("check_updates_on_start", True)))

    def _save_values(self):
        hotkey = self.hotkey_recorder.get_hotkey().strip().lower()
        if not hotkey:
            QMessageBox.warning(self, "خطا", "لطفاً ابتدا کلید میانبر را تعریف کنید.")
            return
        if hotkey.replace(" ", "") in RESERVED_HOTKEYS:
            QMessageBox.warning(self, "کلید رزرو شده",
                f"کلید «{hotkey}» توسط ویندوز رزرو شده است.\n"
                "لطفاً ترکیب دیگری انتخاب کنید.")
            return

        config.update({
            "language": self.lang_combo.currentData(),
            "microphone_index": self.mic_combo.currentData(),
            "enable_persian_punctuation": self.punct_check.isChecked(),
            "enable_half_space": self.half_space_check.isChecked(),
            "persian_digits": self.digits_check.isChecked(),
            "stream_chunk_secs": self.chunk_slider.value() / 10.0,
            "auto_stop_on_silence": self.auto_stop_check.isChecked(),
            "silence_timeout": self.silence_slider.value() / 10.0,
            "hotkey": hotkey,
            "injection_method": self.inject_combo.currentData(),
            "theme": self.theme_combo.currentData(),
            "audio_feedback": self.sounds_check.isChecked(),
            "autostart": self.autostart_check.isChecked(),
            "check_updates_on_start": self.update_on_start_check.isChecked(),
        })
        set_autostart(self.autostart_check.isChecked())
        self.settings_saved.emit()
        self.accept()

    def _manual_check_update(self):
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("در حال بررسی...")
        self.update_status_lbl.setText("در حال اتصال به GitHub...")
        self.download_update_btn.setVisible(False)

        self._update_thread = UpdateCheckerThread(self)
        self._update_thread.result_ready.connect(self._on_update_result)
        self._update_thread.start()

    def _on_update_result(self, result: UpdateResult):
        self.check_update_btn.setEnabled(True)
        self.check_update_btn.setText("بررسی بروزرسانی")

        if result.error:
            self.update_status_lbl.setText(f"⚠ {result.error}")
        elif result.has_update:
            notes = result.release_notes[:200] + "..." if len(result.release_notes) > 200 else result.release_notes
            self.update_status_lbl.setText(
                f"✨ نسخه جدید {result.latest_version} موجود است!\n\n{notes}"
            )
            self._pending_download_url = result.download_url
            self.download_update_btn.setVisible(bool(result.download_url))
        else:
            self.update_status_lbl.setText(
                f"✓ برنامه به‌روز است (نسخه فعلی: v{__version__})"
            )

    def _start_download(self):
        if not self._pending_download_url:
            return
        self.download_update_btn.setEnabled(False)
        self.check_update_btn.setEnabled(False)
        self.update_progress.setVisible(True)
        self.update_progress.setValue(0)
        self.update_status_lbl.setText("در حال دانلود بروزرسانی...")

        def on_progress(pct):
            self.update_progress.setValue(pct)
            self.update_status_lbl.setText(f"دانلود: {pct}%")

        def on_done(path):
            self.update_status_lbl.setText("✓ دانلود کامل شد. برنامه نصب می‌شود...")
            self.update_progress.setValue(100)
            QTimer.singleShot(1500, lambda: QMessageBox.information(
                self, "بروزرسانی",
                "نصب‌کننده اجرا شد. برای تکمیل نصب، برنامه فعلی را ببندید."
            ))

        def on_error(err):
            self.update_status_lbl.setText(f"⚠ خطا در دانلود: {err}")
            self.download_update_btn.setEnabled(True)
            self.check_update_btn.setEnabled(True)

        download_and_install_update(
            self._pending_download_url,
            on_progress=on_progress,
            on_done=on_done,
            on_error=on_error
        )

    def notify_update_available(self, result: UpdateResult):
        """فراخوانی از بیرون هنگام وجود بروزرسانی جدید."""
        self._on_update_result(result)
