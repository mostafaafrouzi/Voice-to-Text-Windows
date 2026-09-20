import ctypes
import math
from PyQt6.QtCore import (
    Qt, QPoint, pyqtSignal, QObject, QRectF, QTimer,
    QPropertyAnimation, QEasingCurve, QSize
)
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QCursor, QGuiApplication,
    QFont, QLinearGradient, QRadialGradient
)
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QGraphicsDropShadowEffect, QToolTip, QSizePolicy
)
from .theme import (
    COLOR_MIC_LISTENING, COLOR_MIC_TRANSCRIBING, COLOR_MIC_IDLE,
    COLOR_MIC_ERROR, COLOR_MIC_SUCCESS
)
from .theme_manager import resolve_theme, get_colors
from .wave_widget import WaveVisualizerWidget
from .fonts import load_fonts, get_font, FONT_FAMILY
from ..config import config
from ..core.engine import SpeechEngine, SpeechState
from ..core.injector import save_target_window

user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOOLWINDOW = 0x00000080


class QtBridge(QObject):
    """پل ارتباطی ایمن بین thread‌های پس‌زمینه و UI اصلی."""
    state_changed = pyqtSignal(str, str)
    level_changed = pyqtSignal(float)
    hotkey_triggered = pyqtSignal()


class MicButton(QWidget):
    """دکمه میکروفون گرد مدرن با حلقه نئونی و انیمیشن ضربان."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # NoFocus: کلیک روی میکروفون نباید keyboard focus رو از پنجره هدف بگیرد
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._state = SpeechState.IDLE
        self._pulse = 0.0
        self._pulse_dir = 1
        self._hovered = False
        self._is_dark = True

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._pulse_tick)
        self._anim_timer.start(35)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        self.update()

    def _pulse_tick(self):
        if self._state == SpeechState.LISTENING:
            self._pulse += 0.08 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse = 1.0
                self._pulse_dir = -1
            elif self._pulse <= 0.0:
                self._pulse = 0.0
                self._pulse_dir = 1
        else:
            self._pulse = 0.0
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy, r = 20, 20, 18

        if self._state == SpeechState.LISTENING:
            main_color = QColor(COLOR_MIC_LISTENING)
            glow_alpha = int(35 + 45 * self._pulse)
            bg_color = QColor(63, 185, 80, glow_alpha)
            ring_alpha = int(120 + 90 * self._pulse)
            ring_color = QColor(63, 185, 80, ring_alpha)
        elif self._state == SpeechState.TRANSCRIBING:
            main_color = QColor(COLOR_MIC_TRANSCRIBING)
            bg_color = QColor(210, 168, 255, 35)
            ring_color = QColor(210, 168, 255, 140)
        elif self._state == SpeechState.ERROR:
            main_color = QColor(COLOR_MIC_ERROR)
            bg_color = QColor(248, 81, 73, 30)
            ring_color = QColor(248, 81, 73, 120)
        elif self._state == SpeechState.SUCCESS:
            main_color = QColor(COLOR_MIC_SUCCESS)
            bg_color = QColor(63, 185, 80, 30)
            ring_color = QColor(63, 185, 80, 150)
        else:
            if self._is_dark:
                main_color = QColor("#8b949e")
                bg_color = QColor(30, 36, 44, 180 if self._hovered else 100)
                ring_color = QColor(48, 54, 61, 220 if self._hovered else 140)
            else:
                main_color = QColor("#57606a")
                bg_color = QColor(234, 238, 242, 220 if self._hovered else 140)
                ring_color = QColor(208, 215, 222, 220 if self._hovered else 140)

        # دایره پس‌زمینه
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(ring_color, 1.5))
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # افکت پالس هنگام گوش دادن
        if self._state == SpeechState.LISTENING and self._pulse > 0.05:
            pulse_r = r + 3 + int(5 * self._pulse)
            pulse_alpha = int(70 * (1.0 - self._pulse))
            painter.setPen(QPen(QColor(63, 185, 80, pulse_alpha), 1.4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2))

        # رسم میکروفون مدرن
        painter.setBrush(QBrush(main_color))
        painter.setPen(Qt.PenStyle.NoPen)
        # کپسول میکروفون
        painter.drawRoundedRect(QRectF(cx - 4.5, cy - 9, 9, 13), 4.5, 4.5)

        # هلال پایه
        pen = QPen(main_color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(cx - 8, cy - 2, 16, 13), 0, -180 * 16)

        # ساقه و پایه
        painter.drawLine(cx, cy + 11, cx, cy + 15)
        painter.drawLine(cx - 5, cy + 15, cx + 5, cy + 15)

        painter.end()


class FloatingPillWidget(QWidget):
    """
    ویجت شناور کپسولی مدرن ویندوز ۱۱ با پشتیبانی کامل از تم تاریک/روشن،
    فونت زیبای Vazirmatn، مدیریت دقیق متون دوجهته (BiDi) و عدم اشغال فوکوس.
    """

    open_settings_requested = pyqtSignal()

    def __init__(self, engine: SpeechEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.bridge = QtBridge()

        load_fonts()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._drag_pos = QPoint()
        self._is_dragging = False
        self._current_theme_name = "dark"
        self._colors = {}

        self._init_ui()
        self.update_theme()
        self._apply_no_activate()
        self._connect_engine()
        self._restore_position()

    def _init_ui(self):
        # ابعاد گسترده‌تر و متناسب برای جلوگیری کامل از بریدگی متن
        self.setFixedSize(360, 64)

        # کانتینر اصلی
        self.container = QWidget(self)
        self.container.setObjectName("PillContainer")
        self.container.setGeometry(6, 5, 348, 54)
        # NoFocus روی کانتینر اصلی
        self.container.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # افکت سایه نرم ویندوز ۱۱
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(26)
        self.shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(self.shadow)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # دکمه میکروفون
        self.mic_btn = MicButton(self.container)
        self.mic_btn.clicked.connect(self._on_mic_clicked)
        layout.addWidget(self.mic_btn)

        # ستون مرکزی: ویژوالایزر امواج + برچسب وضعیت
        center_col = QWidget(self.container)
        center_col.setStyleSheet("background: transparent;")
        center_layout = QVBoxLayout(center_col)
        center_layout.setContentsMargins(0, 4, 0, 4)
        center_layout.setSpacing(2)

        self.wave_widget = WaveVisualizerWidget(center_col)
        center_layout.addWidget(self.wave_widget, 0, Qt.AlignmentFlag.AlignHCenter)

        self.status_label = QLabel(self._get_idle_text(), center_col)
        self.status_label.setObjectName("StatusText")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(get_font(10))
        center_layout.addWidget(self.status_label)

        layout.addWidget(center_col, 1)

        # دکمه‌های سمت راست
        right_layout = QHBoxLayout()
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # دکمه تغییر زبان (FA / EN)
        cur_lang = config.get("language", "fa-IR")
        lang_text = "FA" if cur_lang.startswith("fa") else "EN"
        self.lang_btn = QPushButton(lang_text, self.container)
        self.lang_btn.setObjectName("LangButton")
        self.lang_btn.setFixedSize(34, 26)
        self.lang_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lang_btn.setFont(get_font(10, QFont.Weight.Bold))
        self.lang_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # NoFocus
        self.lang_btn.clicked.connect(self._on_toggle_language)
        right_layout.addWidget(self.lang_btn)

        # دکمه تنظیمات
        self.settings_btn = QPushButton("⚙", self.container)
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_btn.setFont(get_font(13))
        self.settings_btn.setToolTip("تنظیمات")
        self.settings_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # NoFocus
        self.settings_btn.clicked.connect(self.open_settings_requested.emit)
        right_layout.addWidget(self.settings_btn)

        # دکمه مخفی کردن
        self.hide_btn = QPushButton("✕", self.container)
        self.hide_btn.setObjectName("HideBtn")
        self.hide_btn.setFixedSize(24, 24)
        self.hide_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hide_btn.setFont(get_font(11))
        self.hide_btn.setToolTip("مخفی کردن ویجت (برنامه در کنار ساعت فعال است)")
        self.hide_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # NoFocus
        self.hide_btn.clicked.connect(self.hide)
        right_layout.addWidget(self.hide_btn)

        layout.addLayout(right_layout)

    def _get_idle_text(self) -> str:
        hk = config.get("hotkey", "ctrl+alt+v").upper()
        # استفاده از علائم جهت‌دار BiDi تا کلمات انگلیسی و فارسی قاطی نشوند
        return f"آماده تایپ • \u200E{hk}\u200E"

    def update_theme(self):
        """به‌روزرسانی کامل استایل‌های ویجت بر اساس تم فعال (Dark یا Light)."""
        setting = config.get("theme", "system")
        resolved = resolve_theme(setting)
        self._current_theme_name = resolved
        c = get_colors(resolved)
        self._colors = c
        is_dark = (resolved == "dark")

        # به‌روزرسانی سایه پنجره
        if is_dark:
            self.shadow.setColor(QColor(0, 0, 0, 160))
            bg_pill = "rgba(18, 24, 33, 0.95)"
            border_pill = "rgba(48, 54, 61, 0.85)"
            btn_hover = "rgba(255, 255, 255, 0.10)"
            btn_text = "#8b949e"
            btn_hover_text = "#f0f6fc"
        else:
            self.shadow.setColor(QColor(0, 0, 0, 45))
            bg_pill = "rgba(255, 255, 255, 0.96)"
            border_pill = "rgba(208, 215, 222, 0.90)"
            btn_hover = "rgba(0, 0, 0, 0.06)"
            btn_text = "#57606a"
            btn_hover_text = "#1f2328"

        self.mic_btn.set_theme(is_dark)

        qss = f"""
        #PillContainer {{
            background-color: {bg_pill};
            border: 1px solid {border_pill};
            border-radius: 27px;
        }}
        #LangButton {{
            background-color: rgba(47, 129, 247, 0.12);
            color: {c["accent"]};
            border: 1px solid rgba(47, 129, 247, 0.28);
            border-radius: 13px;
            font-family: '{FONT_FAMILY}', 'Segoe UI', Tahoma;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 6px;
        }}
        #LangButton:hover {{
            background-color: {c["accent"]};
            color: #ffffff;
            border-color: {c["accent"]};
        }}
        #SettingsBtn, #HideBtn {{
            background: transparent;
            border: none;
            border-radius: 14px;
            color: {btn_text};
            font-size: 13px;
            padding: 2px;
        }}
        #SettingsBtn:hover, #HideBtn:hover {{
            background-color: {btn_hover};
            color: {btn_hover_text};
        }}
        #StatusText {{
            color: {c["text_secondary"]};
            font-family: '{FONT_FAMILY}', 'Segoe UI', Tahoma;
            font-size: 10px;
        }}
        QToolTip {{
            background-color: {c["bg_card"]};
            color: {c["text_primary"]};
            border: 1px solid {c["border"]};
            border-radius: 6px;
            padding: 4px 8px;
            font-family: '{FONT_FAMILY}', 'Segoe UI', Tahoma;
            font-size: 11px;
        }}
        """
        self.container.setStyleSheet(qss)
        self.status_label.setText(self._get_idle_text())

    def _apply_no_activate(self):
        try:
            hwnd = int(self.winId())
            cur = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, cur | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        except Exception as e:
            print(f"[Pill] WS_EX_NOACTIVATE error: {e}")

    def _connect_engine(self):
        self.bridge.state_changed.connect(self._update_state_ui)
        self.bridge.level_changed.connect(self.wave_widget.set_audio_level)
        self.bridge.hotkey_triggered.connect(self._on_hotkey_triggered)

        self.engine.on_state_change = lambda st, msg: self.bridge.state_changed.emit(st, msg)
        self.engine.on_level_change = lambda lvl: self.bridge.level_changed.emit(lvl)

    def _on_hotkey_triggered(self):
        """ذخیره پنجره هدف قبل از toggle — از طریق میانبر صفحه‌کلید."""
        if self.engine.state in (SpeechState.IDLE, SpeechState.SUCCESS, SpeechState.ERROR):
            save_target_window()
        self.engine.toggle()

    def _update_state_ui(self, state: str, message: str):
        self.mic_btn.set_state(state)
        self.wave_widget.set_state(state)
        c = self._colors if self._colors else get_colors(self._current_theme_name)

        if state == SpeechState.LISTENING:
            self.status_label.setText("در حال گوش دادن...")
            self.status_label.setStyleSheet(f"color: {c['mic_listening']}; font-weight: bold;")
            if not self.isVisible():
                self.show()

        elif state == SpeechState.TRANSCRIBING:
            self.status_label.setText("در حال تایپ...")
            self.status_label.setStyleSheet(f"color: {c['mic_transcribing']}; font-weight: bold;")

        elif state == SpeechState.SUCCESS:
            self.status_label.setText("✓ ثبت شد")
            self.status_label.setStyleSheet(f"color: {c['mic_success']}; font-weight: bold;")

        elif state == SpeechState.ERROR:
            err_msg = message if message else "⚠ خطا در اتصال"
            self.status_label.setText(err_msg[:24])
            self.status_label.setStyleSheet(f"color: {c['mic_error']};")

        else:
            self.status_label.setText(self._get_idle_text())
            self.status_label.setStyleSheet(f"color: {c['text_secondary']};")

    def _on_mic_clicked(self):
        """ذخیره پنجره هدف قبل از شروع ضبط — از طریق کلیک روی دکمه میکروفون."""
        if self.engine.state in (SpeechState.IDLE, SpeechState.SUCCESS, SpeechState.ERROR):
            save_target_window()
        self.engine.toggle()

    def _on_toggle_language(self):
        cur = config.get("language", "fa-IR")
        new_lang = "en-US" if cur.startswith("fa") else "fa-IR"
        config.set("language", new_lang)
        self.lang_btn.setText("EN" if new_lang == "en-US" else "FA")
        label = "زبان گفتار: انگلیسی (en-US)" if new_lang == "en-US" else "زبان گفتار: فارسی (fa-IR)"
        QToolTip.showText(QCursor.pos(), label, self)

    def _restore_position(self):
        x = config.get("widget_x", -1)
        y = config.get("widget_y", -1)
        if x >= 0 and y >= 0:
            self.move(x, y)
        else:
            screen = QGuiApplication.primaryScreen()
            if screen:
                g = screen.availableGeometry()
                self.move(g.x() + (g.width() - self.width()) // 2, g.y() + g.height() - self.height() - 56)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            config.set("widget_x", self.x())
            config.set("widget_y", self.y())
            event.accept()
