<div dir="rtl">

<div align="center">

<img src="https://img.shields.io/github/v/release/mostafaafrouzi/Voice-to-Text-Windows?style=for-the-badge&label=آخرین%20نسخه&color=2f81f7" alt="Latest Release">
<img src="https://img.shields.io/github/actions/workflow/status/mostafaafrouzi/Voice-to-Text-Windows/release.yml?style=for-the-badge&label=بیلد" alt="Build Status">
<img src="https://img.shields.io/github/downloads/mostafaafrouzi/Voice-to-Text-Windows/total?style=for-the-badge&label=دانلود&color=3fb950" alt="Downloads">
<img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-0078d4?style=for-the-badge&logo=windows" alt="Windows">
<img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">

<br><br>

# 🎙 تایپ صوتی هوشمند ویندوز ۱۱
### **Voice-to-Text Windows**

> **تبدیل گفتار به متن بلادرنگ مثل Google Keyboard (Gboard) — رایگان، برای همه برنامه‌های ویندوز**

[دانلود نصب‌کننده](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases/latest) • 
[مشاهده تغییرات](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases) • 
[گزارش مشکل](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/issues) •
[English](README_EN.md)

</div>

---

## ✨ ویژگی‌های کلیدی

| ویژگی | توضیح |
|-------|-------|
| ⚡ **Streaming بلادرنگ** | همزمان با صحبت متن تایپ می‌شود — دقیقاً مثل Gboard اندروید |
| 🌍 **چندزبانه** | پشتیبانی کامل از فارسی ایران و انگلیسی آمریکا |
| 🎯 **کار در همه‌جا** | در هر فیلد متنی در هر برنامه‌ای (ورد، مرورگر، ایمیل...) |
| ⌨ **کلید میانبر** | فعال‌سازی سریع با `Ctrl+Alt+V` (قابل تنظیم) |
| 🔤 **فونت Vazirmatn** | رندر کامل و صحیح متون فارسی |
| 🌓 **تم خودکار** | تاریک / روشن / پیروی از تنظیمات ویندوز |
| 📝 **پردازش متن فارسی** | نیم‌فاصله، ویرگول، نقطه و علائم نگارشی صوتی |
| 🔄 **بروزرسانی خودکار** | بررسی و نصب نسخه جدید با یک کلیک |
| 📦 **EXE مستقل** | نیازی به نصب Python یا هیچ کتابخانه‌ای نیست |
| 🔕 **بدون مزاحمت** | آیکون در System Tray، بدون اشغال فوکوس |

---

## 🖥 نمایش برنامه

<div align="center">

> ویجت کپسولی شناور در پایین صفحه — قابل جابجایی، همیشه روی بقیه پنجره‌ها

</div>

---

## ⬇ نصب و راه‌اندازی

### روش ۱: نصب‌کننده (پیشنهادی)

1. آخرین نسخه `VoiceToText-Setup-vX.X.X.exe` را از [صفحه Releases](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases/latest) دانلود کنید
2. نصب‌کننده را اجرا کنید — نصب کامل، آیکون دسکتاپ، منوی Start
3. برنامه را از دسکتاپ یا منوی Start اجرا کنید

### روش ۲: فایل قابل‌اجرا مستقل

1. `VoiceToText.exe` را دانلود کنید
2. مستقیماً اجرا کنید — بدون هیچ نصبی

> **سیستم‌مورد نیاز:**
> - ویندوز ۱۰ / ۱۱ (۶۴ بیتی)
> - اتصال به اینترنت (برای Google Speech API)
> - میکروفون

---

## 🚀 نحوه استفاده

```
۱. برنامه را اجرا کنید — آیکون در System Tray کنار ساعت ظاهر می‌شود
۲. فیلد متنی دلخواه خود را انتخاب کنید (در هر برنامه‌ای)
۳. Ctrl + Alt + V بفشارید — ویجت فعال می‌شود
۴. صحبت کنید — متن بلافاصله تایپ می‌شود
۵. دوباره Ctrl + Alt + V بفشارید تا ضبط متوقف شود
```

---

## ⚙ تنظیمات

از طریق آیکون System Tray ← تنظیمات، یا کلیک روی آیکون ⚙ در ویجت:

| تنظیم | توضیح |
|-------|-------|
| **زبان** | فارسی / انگلیسی |
| **کلید میانبر** | تغییر Ctrl+Alt+V به هر ترکیب دلخواه |
| **تم** | تاریک / روشن / سیستم |
| **طول قطعه Streaming** | ۱ تا ۴ ثانیه |
| **نیم‌فاصله** | اعمال خودکار |
| **اجرای خودکار با ویندوز** | فعال/غیرفعال |
| **بروزرسانی** | بررسی دستی یا خودکار هنگام اجرا |

---

## 🔧 اجرا از سورس (برای توسعه‌دهندگان)

```bash
git clone https://github.com/mostafaafrouzi/Voice-to-Text-Windows.git
cd Voice-to-Text-Windows
pip install -r requirements.txt
python main.py
```

**ساخت EXE:**
```bash
python build_exe.py
# خروجی: dist/VoiceToText.exe
```

**ساخت Installer:**
```bash
python build_exe.py
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
# خروجی: dist/VoiceToText-Setup-vX.X.X.exe
```

---

## 🏗 معماری فنی

```
Voice-to-Text-Windows/
├── app/
│   ├── core/
│   │   ├── engine.py        ← موتور Streaming تشخیص گفتار
│   │   ├── audio_meter.py   ← ضبط‌کننده صوتی streaming
│   │   ├── text_cleaner.py  ← پردازش متن فارسی (نیم‌فاصله، علائم)
│   │   ├── injector.py      ← درج متن در برنامه فعال
│   │   ├── hotkey.py        ← مدیریت کلید میانبر سراسری
│   │   ├── updater.py       ← بررسی بروزرسانی از GitHub
│   │   └── autostart.py     ← مدیریت اجرای خودکار ویندوز
│   ├── ui/
│   │   ├── pill_widget.py   ← ویجت کپسولی شناور
│   │   ├── settings_win.py  ← پنجره تنظیمات
│   │   ├── tray_icon.py     ← System Tray Icon
│   │   ├── theme_manager.py ← مدیریت تم تاریک/روشن
│   │   └── fonts.py         ← بارگذاری فونت Vazirmatn
│   ├── config.py            ← مدیریت تنظیمات (AppData)
│   └── version.py           ← شماره نسخه
├── assets/fonts/            ← فونت Vazirmatn
├── installer/setup.iss      ← اسکریپت Inno Setup
├── .github/workflows/       ← GitHub Actions CI/CD
├── tests/                   ← تست‌های واحد
└── main.py                  ← نقطه ورود اصلی
```

---

## ❓ سوالات متداول

**آیا نیاز به اتصال اینترنت دارد؟**
بله — از Google Speech-to-Text API برای تشخیص گفتار استفاده می‌شود. این API رایگان است و نیاز به کلید API ندارد.

**آیا فارسی را کامل پشتیبانی می‌کند؟**
بله — نیم‌فاصله، علائم نگارشی صوتی، و رندر صحیح با فونت Vazirmatn.

**آیا از Windows Defender بلاک می‌شود؟**
ممکن است هشدار SmartScreen نمایش داده شود (به دلیل نبود امضای دیجیتال). روی "More info" ← "Run anyway" کلیک کنید.

**چرا متن با تاخیر تایپ می‌شود؟**
در تنظیمات، "طول هر قطعه Streaming" را کاهش دهید (پیش‌فرض ۱.۵ ثانیه).

---

## 📄 مجوز

این پروژه تحت مجوز [MIT License](LICENSE) منتشر شده است.

---

<div align="center">

ساخته شده با ❤️ توسط [Mostafa Afrouzi](https://github.com/mostafaafrouzi)

⭐ اگر این پروژه مفید بود، ستاره بدید!

</div>

</div>
