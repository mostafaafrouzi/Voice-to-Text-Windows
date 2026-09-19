"""
مدیریت بارگذاری فونت Vazirmatn — تنها یک‌بار هنگام راه‌اندازی برنامه فراخوانی می‌شود.
"""
import os
import sys
from PyQt6.QtGui import QFontDatabase, QFont


FONT_FAMILY = "Vazirmatn"
_loaded = False


def _get_assets_dir() -> str:
    """بازگرداندن مسیر پوشه assets چه در محیط کامپایل‌شده و چه پایتون خالص."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        # app/ui/fonts.py  →  app/ui/  →  app/  →  root/
        this_file = os.path.abspath(__file__)
        base = os.path.dirname(os.path.dirname(os.path.dirname(this_file)))
    return os.path.join(base, "assets", "fonts")


def load_fonts():
    """بارگذاری فونت Vazirmatn به رجیستری فونت‌های کیوت."""
    global _loaded
    if _loaded:
        return FONT_FAMILY

    fonts_dir = _get_assets_dir()
    loaded_count = 0

    priority_fonts = [
        "Vazirmatn-Regular.ttf",
        "Vazirmatn-Medium.ttf",
        "Vazirmatn-Bold.ttf",
        "Vazirmatn-SemiBold.ttf",
        "Vazirmatn-Light.ttf",
    ]

    for fname in priority_fonts:
        path = os.path.join(fonts_dir, fname)
        if os.path.exists(path):
            fid = QFontDatabase.addApplicationFont(path)
            if fid >= 0:
                loaded_count += 1

    if loaded_count == 0:
        print("[Fonts] WARNING: Vazirmatn fonts not found, falling back to system fonts.")
        return "Segoe UI"

    _loaded = True
    print(f"[Fonts] Loaded {loaded_count} Vazirmatn font variants.")
    return FONT_FAMILY


def get_font(size: int = 13, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    family = load_fonts()
    font = QFont(family, size)
    font.setWeight(weight)
    return font
