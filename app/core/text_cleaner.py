import re

ZWNJ = "\u200c"  # نیم‌فاصله (Zero Width Non-Joiner)

# نقشه علائم نگارشی صوتی فارسی
PERSIAN_PUNCTUATION_MAP = [
    (r"\b(علامت\s+سوال|علامت\s+پرسش)\b", "؟"),
    (r"\b(علامت\s+تعجب)\b", "!"),
    (r"\b(سه\s+نقطه)\b", "..."),
    (r"\b(دو\s+نقطه)\b", ":"),
    (r"\b(نقطه)\b", "."),
    (r"\b(ویرگول|کاما)\b", "،"),
    (r"\b(برو\s+خط\s+بعد|خط\s+جدید|خط\s+بعد|سطر\s+بعد|اینتر)\b", "\n"),
    (r"\b(پرانتز\s+باز)\b", "("),
    (r"\b(پرانتز\s+بسته)\b", ")"),
    (r"\b(گیومه\s+باز)\b", "«"),
    (r"\b(گیومه\s+بسته)\b", "»"),
    (r"\b(خط\s+تیره|خط\s+فاصله)\b", "-"),
]

# نقشه علائم نگارشی صوتی انگلیسی
ENGLISH_PUNCTUATION_MAP = [
    (r"\b(question\s+mark)\b", "?"),
    (r"\b(exclamation\s+mark|exclamation\s+point)\b", "!"),
    (r"\b(period|full\s+stop)\b", "."),
    (r"\b(comma)\b", ","),
    (r"\b(colon)\b", ":"),
    (r"\b(semicolon)\b", ";"),
    (r"\b(new\s+line|new\s+paragraph|enter)\b", "\n"),
    (r"\b(open\s+parenthesis|open\s+bracket)\b", "("),
    (r"\b(close\s+parenthesis|close\s+bracket)\b", ")"),
    (r"\b(open\s+quote)\b", "\""),
    (r"\b(close\s+quote)\b", "\""),
    (r"\b(dash|hyphen)\b", "-"),
    (r"\b(ellipsis|dot\s+dot\s+dot)\b", "..."),
]

# قوانین نیم‌فاصله فارسی
PERSIAN_PREFIX_RE = re.compile(r"\b(می|نمی)\s+([آ-ی])", re.UNICODE)
PERSIAN_PLURAL_RE = re.compile(r"([آ-ی])\s+(ها|های|هایی|هایم|هایت|هایش|هایمان|هایتان|هایشان)\b", re.UNICODE)
PERSIAN_COMPARATIVE_RE = re.compile(r"([آ-ی])\s+(تر|ترین|تری)\b", re.UNICODE)
PERSIAN_INDEFINITE_RE = re.compile(r"([هة])\s+(ای|ات|اش|ام|اید|اند)\b", re.UNICODE)

# ارقام
EN_TO_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
FA_TO_EN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def apply_persian_punctuation(text: str) -> str:
    """تبدیل کلمات گفتاری علائم نگارشی به نمادها."""
    result = text
    for pattern, symbol in PERSIAN_PUNCTUATION_MAP:
        result = re.sub(pattern, symbol, result, flags=re.IGNORECASE)
    return result


def apply_english_punctuation(text: str) -> str:
    """Convert spoken punctuation words to symbols in English."""
    result = text
    for pattern, symbol in ENGLISH_PUNCTUATION_MAP:
        result = re.sub(pattern, symbol, result, flags=re.IGNORECASE)
    return result


def apply_half_spaces(text: str) -> str:
    """تصحیح نیم‌فاصله‌ها در کلمات رایج فارسی (می‌شود، کتاب‌ها، سریع‌تر و ...)."""
    # پیشوندهای «می» و «نمی»
    text = PERSIAN_PREFIX_RE.sub(r"\1" + ZWNJ + r"\2", text)
    # پسوندهای جمع «ها»
    text = PERSIAN_PLURAL_RE.sub(r"\1" + ZWNJ + r"\2", text)
    # پسوندهای «تر» و «ترین»
    text = PERSIAN_COMPARATIVE_RE.sub(r"\1" + ZWNJ + r"\2", text)
    # پسوندهای کلمات منتهی به «ه» مانند «خانه‌ای»
    text = PERSIAN_INDEFINITE_RE.sub(r"\1" + ZWNJ + r"\2", text)
    return text


def fix_spacing(text: str) -> str:
    """تنظیم فواصل استاندارد اطراف علائم نگارشی."""
    # حذف فاصله قبل از نشانه‌های پایانی: . ، , ؟ ? ! : ; ) » ] }
    text = re.sub(r"\s+([.،,؟!?:;\)»\]\}])", r"\1", text)
    # ایجاد یک فاصله بعد از نشانه‌های پایانی در صورت وجود کلمه بعد از آن
    text = re.sub(r"([.،,؟!?:;\)»\]\}])(?=[^\s\n.،,؟!?:;\)»\]\}])", r"\1 ", text)
    # حذف فاصله بعد از نشانه‌های بازکننده: ( « [ { "
    text = re.sub(r"([(\«\[{\"])\s+", r"\1", text)
    # ایجاد فاصله قبل از نشانه‌های بازکننده
    text = re.sub(r"([^\s\n(\«\[{\"])([(\«\[{\"])", r"\1 \2", text)
    # پاکسازی فاصله‌های متوالی
    text = re.sub(r"[ \t]+", " ", text)
    # پاکسازی فاصله‌های قبل و بعد از سطر جدید
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    return text.strip()


def capitalize_english(text: str) -> str:
    """حرف اول جملات انگلیسی را بزرگ می‌کند."""
    if not text:
        return text
    # Capitalize after start of string or after sentence ending punctuation (. ? !) followed by whitespace or newline
    def cap(match):
        return match.group(1) + match.group(2).upper()

    text = re.sub(r"(^|[.!?\n]\s*)([a-z])", cap, text)
    return text


def clean_text(
    text: str,
    language: str = "fa-IR",
    enable_punctuation: bool = True,
    enable_half_space: bool = True,
    persian_digits: bool = False
) -> str:
    """
    پردازش نهایی متن تشخیص داده شده متناسب با زبان و تنظیمات کاربر.
    """
    if not text:
        return ""

    cleaned = text.strip()

    is_persian = language.startswith("fa")

    if enable_punctuation:
        if is_persian:
            cleaned = apply_persian_punctuation(cleaned)
        else:
            cleaned = apply_english_punctuation(cleaned)

    if is_persian and enable_half_space:
        cleaned = apply_half_spaces(cleaned)

    cleaned = fix_spacing(cleaned)

    if not is_persian:
        cleaned = capitalize_english(cleaned)

    if is_persian and persian_digits:
        # تبدیل اعداد لاتین به فارسی
        cleaned = cleaned.translate(EN_TO_FA_DIGITS)
    elif is_persian and not persian_digits:
        # گوگل برای فارسی ارقام عربی-هندی برمی‌گرداند — آن‌ها را به لاتین تبدیل کن
        cleaned = cleaned.translate(FA_TO_EN_DIGITS)
    elif not is_persian:
        cleaned = cleaned.translate(FA_TO_EN_DIGITS)

    return cleaned
