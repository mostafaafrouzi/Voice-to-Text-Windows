from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer
from PyQt6.QtGui import QFont, QColor
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

        self._apply_theme()
        self._init_ui()
        self._load_values()

    def _get_theme_colors(self):
        setting = config.get("theme", "system")
        resolved = resolve_theme(setting)
        return get_colors(resolved), resolved

    def _apply_theme(self):
        colors, _ = self._get_theme_colors()
        self.setStyleSheet(self._build_full_style(colors))

    def _build_full_style(self, c: dict) -> str:
        return f"""
QDialog {{
    background-color: {c["bg"]};
    color: {c["text_primary"]};
    font-family: '{FONT_FAMILY}', Tahoma, 'Segoe UI';
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
QLineEdit, QComboBox {{
    background-color: {c["bg"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    color: {c["text_primary"]};
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: {c["accent"]};
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {c["accent"]}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border"]};
    color: {c["text_primary"]};
    selection-background-color: {c["accent"]};
    padding: 4px;
}}
QCheckBox {{ color: {c["text_primary"]}; spacing: 10px; }}
QCheckBox::indicator {{
    width: 17px; height: 17px; border-radius: 5px;
    border: 1.5px solid {c["border"]}; background-color: {c["bg"]};
}}
QCheckBox::indicator:hover {{ border-color: {c["accent"]}; }}
QCheckBox::indicator:checked {{
    background-color: {c["accent"]}; border-color: {c["accent"]};
}}
QSlider::groove:horizontal {{
    height: 4px; background: {c["border"]}; border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {c["accent"]}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {c["text_primary"]}; border: 2px solid {c["accent"]};
    width: 14px; margin: -5px 0; border-radius: 7px;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 5px; border-radius: 2px;
}}
QScrollBar::handle:vertical {{
    background: {c["border"]}; border-radius: 2px; min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QProgressBar {{
    border: 1px solid {c["border"]}; border-radius: 6px;
    background: {c["bg_card"]}; height: 12px; text-align: center;
    color: {c["text_primary"]}; font-size: 10px;
}}
QProgressBar::chunk {{
    background: {c["accent"]}; border-radius: 6px;
}}
"""

    def _make_btn(self, text: str, primary: bool = False) -> QPushButton:
        c, _ = self._get_theme_colors()
        btn = QPushButton(text)
        btn.setFont(get_font(12, QFont.Weight.Bold if primary else QFont.Weight.Normal))
        btn.setFixedHeight(36)
        btn.setMinimumWidth(110)
        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{ background:{c["accent"]}; color:#fff; border:none; border-radius:8px; padding:0 18px; }}
                QPushButton:hover {{ background:{c["accent_hover"]}; }}
                QPushButton:pressed {{ background:{c["accent_dark"]}; }}
                QPushButton:disabled {{ background:{c["border"]}; color:{c["text_muted"]}; }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; color:{c["text_secondary"]}; border:1px solid {c["border"]}; border-radius:8px; padding:0 16px; }}
                QPushButton:hover {{ background:rgba(127,127,127,0.07); color:{c["text_primary"]}; border-color:{c["text_muted"]}; }}
                QPushButton:disabled {{ color:{c["text_muted"]}; }}
            """)
        return btn

    def _make_combo(self, width: int = 230) -> QComboBox:
        c = QComboBox()
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
        colors, _ = self._get_theme_colors()
        header = QWidget()
        header.setStyleSheet(f"background-color: {colors['bg_card']}; border-bottom: 1px solid {colors['border']};")
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
        body.setStyleSheet(f"background-color: {colors['bg']};")
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
        hint.setFont(get_font(11)); hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {colors['text_muted']}; background: transparent;")
        c2.body_layout.addWidget(hint)

        row_ch = QHBoxLayout(); row_ch.addWidget(self._make_label("طول هر قطعه:"))
        self.chunk_lbl = QLabel("۱.۵ ثانیه")
        self.chunk_lbl.setFont(get_font(11, QFont.Weight.Bold))
        self.chunk_lbl.setStyleSheet(f"color: {colors['mic_listening']}; background: transparent; min-width: 70px;")
        self.chunk_slider = QSlider(Qt.Orientation.Horizontal)
        self.chunk_slider.setRange(10, 40)
        self.chunk_slider.valueChanged.connect(lambda v: self.chunk_lbl.setText(f"{'%.1f' % (v/10)} ثانیه"))
        row_ch.addWidget(self.chunk_slider); row_ch.addWidget(self.chunk_lbl)
        c2.body_layout.addLayout(row_ch)

        self.auto_stop_check = self._make_check("توقف خودکار ضبط پس از سکوت")
        c2.body_layout.addWidget(self.auto_stop_check)

        row_s = QHBoxLayout(); row_s.addWidget(self._make_label("مدت سکوت:"))
        self.silence_lbl = QLabel("۰.۸ ثانیه")
        self.silence_lbl.setFont(get_font(11, QFont.Weight.Bold))
        self.silence_lbl.setStyleSheet(f"color: {colors['accent']}; background: transparent; min-width: 70px;")
        self.silence_slider = QSlider(Qt.Orientation.Horizontal)
        self.silence_slider.setRange(5, 25)
        self.silence_slider.valueChanged.connect(lambda v: self.silence_lbl.setText(f"{'%.1f' % (v/10)} ثانیه"))
        row_s.addWidget(self.silence_slider); row_s.addWidget(self.silence_lbl)
        c2.body_layout.addLayout(row_s)
        bl.addWidget(c2)

        # ---- کارت ۳: میانبر ----
        c3 = SectionCard("⌨ کلید میانبر سراسری")
        row_hk = QHBoxLayout(); row_hk.addWidget(self._make_label("کلید میانبر:"))
        self.hotkey_edit = self._make_lineedit("مثال: ctrl+alt+v  یا  f8")
        self.hotkey_edit.textChanged.connect(self._validate_hotkey)
        row_hk.addWidget(self.hotkey_edit); c3.body_layout.addLayout(row_hk)

        self.hotkey_warn = QLabel("")
        self.hotkey_warn.setFont(get_font(11))
        self.hotkey_warn.setStyleSheet("color: #f85149; background: transparent;")
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
        footer.setStyleSheet(f"background-color: {colors['bg_card']}; border-top: 1px solid {colors['border']};")
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

    def _validate_hotkey(self, text: str):
        """بررسی معتبر بودن کلید میانبر و هشدار در صورت رزرو شده بودن."""
        normalized = text.strip().lower().replace(" ", "")
        if normalized in RESERVED_HOTKEYS:
            self.hotkey_warn.setText(
                f"⚠ این کلید ({text.strip()}) توسط ویندوز رزرو شده است و نمی‌توان آن را override کرد.\n"
                "لطفاً ترکیب دیگری مانند Ctrl+Alt+V یا F8 انتخاب کنید."
            )
        elif normalized and len(normalized) < 2:
            self.hotkey_warn.setText("⚠ کلید میانبر باید حداقل شامل یک ترکیب باشد (مثلاً ctrl+alt+v)")
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
        self.hotkey_edit.setText(config.get("hotkey", "ctrl+alt+v"))
        idx = self.inject_combo.findData(config.get("injection_method", "clipboard"))
        if idx >= 0: self.inject_combo.setCurrentIndex(idx)
        idx = self.theme_combo.findData(config.get("theme", "system"))
        if idx >= 0: self.theme_combo.setCurrentIndex(idx)
        self.sounds_check.setChecked(bool(config.get("audio_feedback", True)))
        self.autostart_check.setChecked(is_autostart_enabled())
        self.update_on_start_check.setChecked(bool(config.get("check_updates_on_start", True)))

    def _save_values(self):
        hotkey = self.hotkey_edit.text().strip().lower()
        if not hotkey:
            QMessageBox.warning(self, "خطا", "لطفاً یک کلید میانبر معتبر وارد کنید.")
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
