"""
تم و استایل‌های بصری مدرن ویندوز ۱۱ (Fluent Design) — نسخه ۲.
"""
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtWidgets import QWidget

# پالت رنگی اصلی
COLOR_BG = "#0d1117"
COLOR_BG_CARD = "#161b22"
COLOR_BG_CARD2 = "#1c2333"
COLOR_BORDER = "#30363d"
COLOR_ACCENT = "#2f81f7"
COLOR_ACCENT_GLOW = "#388bfd"
COLOR_ACCENT_DARK = "#1f6feb"
COLOR_TEXT_PRIMARY = "#f0f6fc"
COLOR_TEXT_SECONDARY = "#8b949e"
COLOR_TEXT_MUTED = "#6e7681"

# رنگ‌های وضعیت میکروفون
COLOR_MIC_IDLE = "#484f58"
COLOR_MIC_LISTENING = "#3fb950"       # سبز درخشان گیتهاب
COLOR_MIC_TRANSCRIBING = "#d2a8ff"    # بنفش نئونی
COLOR_MIC_SUCCESS = "#3fb950"         # سبز تأیید
COLOR_MIC_ERROR = "#f85149"           # سرخ هشدار


PILL_STYLE = """
/* ===================== PILL CONTAINER ===================== */
#PillContainer {
    background-color: rgba(13, 17, 23, 0.97);
    border: 1px solid rgba(48, 54, 61, 0.9);
    border-radius: 28px;
}

/* ===================== LANGUAGE BUTTON ===================== */
#LangButton {
    background-color: rgba(47, 129, 247, 0.14);
    color: #58a6ff;
    border: 1px solid rgba(47, 129, 247, 0.28);
    border-radius: 14px;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 11px;
    letter-spacing: 0.5px;
}
#LangButton:hover {
    background-color: rgba(47, 129, 247, 0.28);
    color: #ffffff;
    border-color: rgba(47, 129, 247, 0.55);
}

/* ===================== ICON BUTTONS ===================== */
#SettingsBtn, #HideBtn {
    background: transparent;
    border: none;
    border-radius: 16px;
    color: #6e7681;
    font-size: 14px;
    padding: 2px;
}
#SettingsBtn:hover, #HideBtn:hover {
    background-color: rgba(255, 255, 255, 0.09);
    color: #c9d1d9;
}

/* ===================== STATUS TEXT ===================== */
#StatusText {
    color: #8b949e;
    font-size: 12px;
}

/* ===================== TOOLTIP ===================== */
QToolTip {
    background-color: #21262d;
    color: #f0f6fc;
    border: 1px solid #388bfd;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 12px;
}
"""

SETTINGS_STYLE = """
/* ===================== MAIN DIALOG ===================== */
QDialog {
    background-color: #0d1117;
    color: #f0f6fc;
}

/* ===================== GROUP BOXES ===================== */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    margin-top: 22px;
    padding: 18px 16px 14px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #58a6ff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 12px;
    background-color: transparent;
}

/* ===================== LABELS ===================== */
QLabel {
    color: #c9d1d9;
    font-size: 13px;
    background: transparent;
}
QLabel#SectionTitle {
    color: #f0f6fc;
    font-size: 17px;
    font-weight: 700;
}
QLabel#SubTitle {
    color: #8b949e;
    font-size: 12px;
}

/* ===================== INPUTS ===================== */
QLineEdit, QComboBox, QSpinBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #f0f6fc;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #1f6feb;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #2f81f7;
    background-color: #0d1117;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
    subcontrol-position: right center;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    color: #f0f6fc;
    selection-background-color: #1f6feb;
    padding: 4px;
    font-size: 13px;
}

/* ===================== CHECKBOXES ===================== */
QCheckBox {
    color: #c9d1d9;
    font-size: 13px;
    spacing: 10px;
}
QCheckBox:hover { color: #f0f6fc; }
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid #30363d;
    background-color: #0d1117;
}
QCheckBox::indicator:hover { border-color: #2f81f7; }
QCheckBox::indicator:checked {
    background-color: #2f81f7;
    border-color: #2f81f7;
    image: url(data:image/svg+xml,<svg/> );
}

/* ===================== BUTTONS ===================== */
#PrimaryBtn {
    background-color: #2f81f7;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
    font-weight: 700;
}
#PrimaryBtn:hover { background-color: #388bfd; }
#PrimaryBtn:pressed { background-color: #1f6feb; }

#SecondaryBtn {
    background-color: transparent;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 13px;
}
#SecondaryBtn:hover {
    background-color: rgba(255, 255, 255, 0.05);
    color: #f0f6fc;
    border-color: #8b949e;
}

/* ===================== SLIDERS ===================== */
QSlider::groove:horizontal {
    border: none;
    height: 5px;
    background: #21262d;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #2f81f7;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #f0f6fc;
    border: 2px solid #2f81f7;
    width: 16px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover { background: #ffffff; }

/* ===================== SCROLLBAR ===================== */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: transparent;
    width: 5px;
    border-radius: 2px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 2px;
    min-height: 30px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def create_app_icon(color_hex: str = COLOR_ACCENT) -> "QIcon":
    import os
    import sys
    from PyQt6.QtGui import QPixmap, QIcon

    # ابتدا بررسی وجود فایل رسمی آیکون ویندوز
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ico_path = os.path.join(base, "assets", "icon.ico")
    if os.path.exists(ico_path):
        icon = QIcon(ico_path)
        if not icon.isNull():
            return icon

    # در صورت عدم وجود فایل، رسم پویا در حافظه
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # گرادیانت پس‌زمینه
    grad = QLinearGradient(0, 0, 64, 64)
    grad.setColorAt(0.0, QColor("#1f6feb"))
    grad.setColorAt(1.0, QColor("#0d1117"))
    painter.setBrush(QBrush(grad))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(2, 2, 60, 60), 18, 18)

    # بدنه میکروفون
    painter.setBrush(QBrush(QColor("#ffffff")))
    painter.drawRoundedRect(QRectF(24.5, 14, 15, 22), 7.5, 7.5)

    # قوس و پایه
    pen = QPen(QColor("#ffffff"), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(QRectF(17, 23, 30, 20), 0, -180 * 16)
    painter.drawLine(32, 43, 32, 50)
    painter.drawLine(24, 50, 40, 50)

    painter.end()
    return QIcon(pixmap)


def get_check_icon_path() -> str:
    import os
    import sys
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p = os.path.join(base, "assets", "check.png")
    return p.replace("\\", "/")

