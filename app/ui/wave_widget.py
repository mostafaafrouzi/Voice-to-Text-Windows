import math
import random
from PyQt6.QtCore import Qt, QTimer, QRectF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient
from PyQt6.QtWidgets import QWidget
from ..core.engine import SpeechState


class WaveVisualizerWidget(QWidget):
    """
    ویژوالایزر امواج صوتی با انیمیشن ۳۰ FPS — سبک Google Assistant.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 36)
        self._num_bars = 5
        self._current_levels = [0.08] * self._num_bars
        self._target_levels = [0.08] * self._num_bars
        self._state = SpeechState.IDLE
        self._phase = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_state(self, state: str):
        self._state = state
        if state in (SpeechState.IDLE, SpeechState.SUCCESS, SpeechState.ERROR):
            self._target_levels = [0.08] * self._num_bars

    def set_audio_level(self, level: float):
        if self._state not in (SpeechState.LISTENING,):
            return
        level = max(0.05, min(1.0, level))
        mults = [0.55, 0.88, 1.00, 0.82, 0.58]
        for i in range(self._num_bars):
            jitter = (random.random() - 0.5) * 0.15 * level
            self._target_levels[i] = min(1.0, max(0.07, level * mults[i] + jitter))

    def _tick(self):
        self._phase += 0.10

        if self._state == SpeechState.TRANSCRIBING or self._state == SpeechState.LISTENING:
            if self._state == SpeechState.TRANSCRIBING:
                for i in range(self._num_bars):
                    s = math.sin(self._phase + i * 0.9)
                    self._target_levels[i] = 0.30 + 0.32 * s
        elif self._state == SpeechState.IDLE:
            for i in range(self._num_bars):
                self._target_levels[i] = 0.07 + 0.04 * math.sin(self._phase * 0.4 + i)

        for i in range(self._num_bars):
            self._current_levels[i] += (self._target_levels[i] - self._current_levels[i]) * 0.30

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        bw = 4.0
        spacing = (w - self._num_bars * bw) / (self._num_bars + 1)
        max_h = h - 6

        if self._state == SpeechState.LISTENING:
            c_top, c_bot = QColor("#3fb950"), QColor("#238636")
        elif self._state == SpeechState.TRANSCRIBING:
            c_top, c_bot = QColor("#d2a8ff"), QColor("#8957e5")
        elif self._state == SpeechState.ERROR:
            c_top, c_bot = QColor("#f85149"), QColor("#da3633")
        elif self._state == SpeechState.SUCCESS:
            c_top, c_bot = QColor("#3fb950"), QColor("#2ea043")
        else:
            c_top, c_bot = QColor("#484f58"), QColor("#30363d")

        for i in range(self._num_bars):
            bar_h = max(3.5, self._current_levels[i] * max_h)
            x = spacing + i * (bw + spacing)
            y = (h - bar_h) / 2.0

            g = QLinearGradient(x, y, x, y + bar_h)
            g.setColorAt(0.0, c_top)
            g.setColorAt(1.0, c_bot)
            painter.setBrush(QBrush(g))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(x, y, bw, bar_h), bw / 2, bw / 2)

        painter.end()
