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
from .theme import PILL_STYLE, COLOR_MIC_LISTENING, COLOR_MIC_TRANSCRIBING, COLOR_MIC_IDLE, COLOR_MIC_ERROR, COLOR_MIC_SUCCESS
from .wave_widget import WaveVisualizerWidget
from .fonts import load_fonts, get_font, FONT_FAMILY
from ..config import config
from ..core.engine import SpeechEngine, SpeechState

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
    """دکمه میکروفون گرد با حلقه گلوی نئونی و انیمیشن ضربان."""

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._state = SpeechState.IDLE
        self._pulse = 0.0
        self._pulse_dir = 1
        self._hovered = False

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._pulse_tick)
        self._anim_timer.start(40)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def _pulse_tick(self):
        if self._state == SpeechState.LISTENING:
            self._pulse += 0.07 * self._pulse_dir
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

        cx, cy, r = 22, 22, 19

        # رنگ‌بندی متناسب با وضعیت
        if self._state == SpeechState.LISTENING:
            main_color = QColor(COLOR_MIC_LISTENING)
            glow_alpha = int(30 + 45 * self._pulse)
            bg_color = QColor(63, 185, 80, glow_alpha)
            ring_alpha = int(100 + 100 * self._pulse)
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
            main_color = QColor(COLOR_MIC_IDLE)
            bg_color = QColor(72, 79, 88, 40 if self._hovered else 20)
            ring_color = QColor(72, 79, 88, 120 if self._hovered else 60)

        # پس‌زمینه دایره‌ای
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(ring_color, 1.8))
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # Pulse ring برای حالت Listening
        if self._state == SpeechState.LISTENING and self._pulse > 0.1:
            pulse_r = r + 4 + int(6 * self._pulse)
            pulse_alpha = int(60 * (1.0 - self._pulse))
            painter.setPen(QPen(QColor(63, 185, 80, pulse_alpha), 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2))

        # آیکون میکروفون
        painter.setBrush(QBrush(main_color))
        painter.setPen(Qt.PenStyle.NoPen)
        # بدنه (کپسول)
        painter.drawRoundedRect(QRectF(cx - 5, cy - 10, 10, 14), 5, 5)

        # قوس پایه
        pen = QPen(main_color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(QRectF(cx - 9, cy - 2, 18, 14), 0, -180 * 16)

        # خط عمودی
        painter.drawLine(cx, cy + 12, cx, cy + 16)
        painter.drawLine(cx - 6, cy + 16, cx + 6, cy + 16)

        painter.end()


class FloatingPillWidget(QWidget):
    """
    ویجت شناور کپسولی مدرن ویندوز ۱۱ با فونت Vazirmatn، انیمیشن، و عدم اشغال فوکوس.
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

        self._init_ui()
        self._apply_no_activate()
        self._connect_engine()
        self._restore_position()

    def _init_ui(self):
        self.setFixedSize(310, 62)
        self.setStyleSheet(f"font-family: '{FONT_FAMILY}', 'Segoe UI', Tahoma;")

        # کانتینر اصلی
        self.container = QWidget(self)
        self.container.setObjectName("PillContainer")
        self.container.setGeometry(5, 4, 300, 54)

        # افکت سایه نرم ویندوز ۱۱
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)

        self.container.setStyleSheet(PILL_STYLE)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        # دکمه میکروفون
        self.mic_btn = MicButton(self.container)
        self.mic_btn.clicked.connect(self._on_mic_clicked)
        layout.addWidget(self.mic_btn)

        # ستون مرکزی: ویژوالایزر + متن وضعیت
        center_col = QWidget(self.container)
        center_col.setStyleSheet("background: transparent;")
        center_layout = QVBoxLayout(center_col)
        center_layout.setContentsMargins(0, 4, 0, 4)
        center_layout.setSpacing(2)

        self.wave_widget = WaveVisualizerWidget(center_col)
        center_layout.addWidget(self.wave_widget, 0, Qt.AlignmentFlag.AlignHCenter)

        self.status_label = QLabel("آماده‌ام — کلیک کنید یا Ctrl+Alt+V", center_col)
        self.status_label.setObjectName("StatusText")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(get_font(10))
        center_layout.addWidget(self.status_label)

        layout.addWidget(center_col, 1)

        # دکمه‌های سمت راست
        right_layout = QHBoxLayout()
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # دکمه زبان
        cur_lang = config.get("language", "fa-IR")
        lang_text = "FA" if cur_lang.startswith("fa") else "EN"
        self.lang_btn = QPushButton(lang_text, self.container)
        self.lang_btn.setObjectName("LangButton")
        self.lang_btn.setFixedSize(36, 26)
        self.lang_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.lang_btn.setFont(get_font(10, QFont.Weight.Bold))
        self.lang_btn.clicked.connect(self._on_toggle_language)
        right_layout.addWidget(self.lang_btn)

        # دکمه تنظیمات
        self.settings_btn = QPushButton("⚙", self.container)
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_btn.setFont(get_font(13))
        self.settings_btn.setToolTip("تنظیمات")
        self.settings_btn.clicked.connect(self.open_settings_requested.emit)
        right_layout.addWidget(self.settings_btn)

        # دکمه مخفی کردن
        self.hide_btn = QPushButton("✕", self.container)
        self.hide_btn.setObjectName("HideBtn")
        self.hide_btn.setFixedSize(24, 24)
        self.hide_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hide_btn.setFont(get_font(11))
        self.hide_btn.setToolTip("مخفی‌کن (در تری باقی می‌ماند)")
        self.hide_btn.clicked.connect(self.hide)
        right_layout.addWidget(self.hide_btn)

        layout.addLayout(right_layout)

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
        self.bridge.hotkey_triggered.connect(self.engine.toggle)

        self.engine.on_state_change = lambda st, msg: self.bridge.state_changed.emit(st, msg)
        self.engine.on_level_change = lambda lvl: self.bridge.level_changed.emit(lvl)

    def _update_state_ui(self, state: str, message: str):
        self.mic_btn.set_state(state)
        self.wave_widget.set_state(state)

        if state == SpeechState.LISTENING:
            if "تبدیل" in message:
                self.status_label.setText("در حال تبدیل...")
                self.status_label.setStyleSheet("color: #8b949e;")
            else:
                self.status_label.setText("در حال گوش دادن...")
                self.status_label.setStyleSheet("color: #3fb950; font-weight: bold;")
            if not self.isVisible():
                self.show()

        elif state == SpeechState.TRANSCRIBING:
            self.status_label.setText("پردازش...")
            self.status_label.setStyleSheet("color: #d2a8ff;")

        elif state == SpeechState.SUCCESS:
            self.status_label.setText("✓ انجام شد")
            self.status_label.setStyleSheet("color: #3fb950; font-weight: bold;")

        elif state == SpeechState.ERROR:
            self.status_label.setText("⚠ خطا — اینترنت؟")
            self.status_label.setStyleSheet("color: #f85149;")

        else:
            self.status_label.setText("آماده‌ام — کلیک یا Ctrl+Alt+V")
            self.status_label.setStyleSheet("color: #6e7681;")

    def _on_mic_clicked(self):
        self.engine.toggle()

    def _on_toggle_language(self):
        cur = config.get("language", "fa-IR")
        new_lang = "en-US" if cur.startswith("fa") else "fa-IR"
        config.set("language", new_lang)
        self.lang_btn.setText("EN" if new_lang == "en-US" else "FA")
        label = "زبان: انگلیسی" if new_lang == "en-US" else "زبان: فارسی"
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
