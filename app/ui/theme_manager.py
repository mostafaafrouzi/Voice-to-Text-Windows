"""
مدیریت تم برنامه: تاریک / روشن / پیروی از تنظیمات ویندوز.
"""
import winreg
from enum import Enum


class AppTheme(str, Enum):
    SYSTEM = "system"
    DARK = "dark"
    LIGHT = "light"


def is_windows_dark_mode() -> bool:
    """بررسی تم جاری ویندوز از رجیستری."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0  # 0 = Dark, 1 = Light
    except Exception:
        return True  # پیش‌فرض به تاریک


def resolve_theme(setting: str) -> str:
    """
    بازگرداندن تم واقعی ('dark' یا 'light') با توجه به تنظیم انتخابی کاربر.
    """
    if setting == AppTheme.SYSTEM:
        return "dark" if is_windows_dark_mode() else "light"
    return setting


# ===================== رنگ‌های تم تاریک =====================
DARK = {
    "bg":            "#0d1117",
    "bg_card":       "#161b22",
    "bg_card2":      "#1c2333",
    "border":        "#30363d",
    "accent":        "#2f81f7",
    "accent_hover":  "#388bfd",
    "accent_dark":   "#1f6feb",
    "text_primary":  "#f0f6fc",
    "text_secondary":"#8b949e",
    "text_muted":    "#6e7681",
    "mic_idle":      "#484f58",
    "mic_listening": "#3fb950",
    "mic_transcribing": "#d2a8ff",
    "mic_success":   "#3fb950",
    "mic_error":     "#f85149",
}

# ===================== رنگ‌های تم روشن =====================
LIGHT = {
    "bg":            "#ffffff",
    "bg_card":       "#f6f8fa",
    "bg_card2":      "#eaeef2",
    "border":        "#d0d7de",
    "accent":        "#0969da",
    "accent_hover":  "#0a57bf",
    "accent_dark":   "#1a7f64",
    "text_primary":  "#1f2328",
    "text_secondary":"#57606a",
    "text_muted":    "#8c959f",
    "mic_idle":      "#8c959f",
    "mic_listening": "#1a7f37",
    "mic_transcribing": "#8250df",
    "mic_success":   "#1a7f37",
    "mic_error":     "#cf222e",
}


def get_colors(theme_name: str) -> dict:
    """بازگرداندن دیکشنری رنگ‌ها برای تم مشخص‌شده."""
    return DARK if theme_name == "dark" else LIGHT


def build_pill_style(colors: dict) -> str:
    c = colors
    return f"""
#PillContainer {{
    background-color: {c["bg"] + "F7"};
    border: 1px solid {c["border"]};
    border-radius: 28px;
}}
#LangButton {{
    background-color: rgba(47,129,247,0.14);
    color: {c["accent"]};
    border: 1px solid rgba(47,129,247,0.28);
    border-radius: 14px;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 11px;
    letter-spacing: 0.5px;
}}
#LangButton:hover {{
    background-color: rgba(47,129,247,0.28);
    color: {c["text_primary"]};
    border-color: {c["accent"]};
}}
#SettingsBtn, #HideBtn {{
    background: transparent;
    border: none;
    border-radius: 16px;
    color: {c["text_muted"]};
    font-size: 14px;
    padding: 2px;
}}
#SettingsBtn:hover, #HideBtn:hover {{
    background-color: rgba(127,127,127,0.13);
    color: {c["text_primary"]};
}}
#StatusText {{
    color: {c["text_secondary"]};
    font-size: 12px;
}}
QToolTip {{
    background-color: {c["bg_card"]};
    color: {c["text_primary"]};
    border: 1px solid {c["accent"]};
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 12px;
}}
"""


def build_settings_style(colors: dict) -> str:
    c = colors
    return f"""
QDialog {{
    background-color: {c["bg"]};
    color: {c["text_primary"]};
}}
QWidget#SectionCard {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border"]};
    border-radius: 12px;
}}
QLabel {{
    color: {c["text_secondary"]};
    background: transparent;
}}
QLineEdit, QComboBox {{
    background-color: {c["bg"]};
    border: 1px solid {c["border"]};
    border-radius: 8px;
    color: {c["text_primary"]};
    padding: 7px 12px;
    font-size: 13px;
    selection-background-color: {c["accent"]};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {c["accent"]};
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background-color: {c["bg_card"]};
    border: 1px solid {c["border"]};
    color: {c["text_primary"]};
    selection-background-color: {c["accent"]};
    padding: 4px;
    font-size: 13px;
}}
QCheckBox {{
    color: {c["text_primary"]};
    spacing: 10px;
}}
QCheckBox:hover {{ color: {c["text_primary"]}; }}
QCheckBox::indicator {{
    width: 17px; height: 17px;
    border-radius: 5px;
    border: 1.5px solid {c["border"]};
    background-color: {c["bg"]};
}}
QCheckBox::indicator:hover {{ border-color: {c["accent"]}; }}
QCheckBox::indicator:checked {{
    background-color: {c["accent"]};
    border-color: {c["accent"]};
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 5px; border-radius: 2px;
}}
QScrollBar::handle:vertical {{
    background: {c["border"]}; border-radius: 2px; min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
