<div align="center">

<img src="https://img.shields.io/github/v/release/mostafaafrouzi/Voice-to-Text-Windows?style=for-the-badge&label=Latest%20Release&color=2f81f7" alt="Latest Release">
<img src="https://img.shields.io/github/actions/workflow/status/mostafaafrouzi/Voice-to-Text-Windows/release.yml?style=for-the-badge&label=Build" alt="Build Status">
<img src="https://img.shields.io/github/downloads/mostafaafrouzi/Voice-to-Text-Windows/total?style=for-the-badge&label=Downloads&color=3fb950" alt="Downloads">
<img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D4.svg?style=for-the-badge&logo=windows" alt="Windows">
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=for-the-badge&logo=python" alt="Python">
<img src="https://img.shields.io/badge/UI-PyQt6%20Fluent-41CD52.svg?style=for-the-badge&logo=qt" alt="PyQt6">
<img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">

<br><br>

# 🎙 Voice-to-Text Windows 11
### **Intelligent, Real-Time Cloud Voice Typing for Windows**

> **Replicating the seamless, instantaneous voice typing experience of Google Keyboard (Gboard) and Android Speech Services across all Windows apps — 100% Free, no API keys, and no heavy offline models required.**

[Download Installer](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases/latest) • 
[Release Notes](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases) • 
[Report Bug](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/issues) • 
[راهنمای فارسی](README.md)

</div>

---

## 🌟 Why Voice-to-Text Windows?

On Android, Google Keyboard (**Gboard**) and **Google Speech Services** offer one of the fastest, most accurate voice typing experiences in the world, especially for languages like Persian (Farsi) and English. Windows 11's built-in voice typing lacks good Persian language support, and offline alternatives require downloading multi-gigabyte models and running heavy GPU inference.

**Voice-to-Text Windows** bridges this gap: a modern, lightweight, free, and lightning-fast voice typing assistant for Windows 10/11. Powered by Google's cloud speech recognition engine, it activates anywhere with a single global shortcut (`Ctrl + Alt + V`) and streams transcribed text directly into whatever text field you are typing in (Word, Telegram, WhatsApp, Chrome, VS Code, Discord, etc.).

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| ⚡ **Real-Time Streaming Dictation** | Transcribes speech incrementally as you talk — just like Gboard on Android |
| 🌐 **Bilingual (Persian & English)** | Flawless accuracy for Persian (`fa-IR`) and English (`en-US`) with instant one-click switching |
| 🎯 **Universal Compatibility** | Works across any input field in any application (Word, Browser, Telegram, Slack, etc.) |
| 🎨 **Windows 11 Fluent Acrylic UI** | Modern floating capsule widget with smooth drop shadows, draggable anywhere on screen |
| 🔒 **Focus-Safe Non-Activating Window** | Uses Win32 `WS_EX_NOACTIVATE` — never steals focus or cursor from your target app |
| 🌊 **Audio Waveform Visualizer** | Smooth 30 FPS visualizer responsive to real-time microphone amplitude |
| ✍️ **Intelligent Spoken Punctuation** | Say "period", "comma", "question mark", "new line" (or Persian equivalents) to insert punctuation |
| 📐 **Persian Half-Space Normalization** | Automatically normalizes Persian half-spaces (نیم‌فاصله) for «می‌شود», «کتاب‌ها», «سریع‌تر» |
| 🌓 **Adaptive Theme (Dark/Light/System)**| Seamlessly follows Windows 11 theme preferences or allows manual override |
| 🕒 **System Tray & Startup Integration** | Lives quietly next to the clock; configurable via Windows Taskbar settings & run on startup |
| 🔄 **Automatic & Manual Updates** | Background update checker on launch + manual check in settings with 1-click update |
| 📦 **No Python Required** | Distributed as a standalone `.exe` and official Windows Installer (`Setup.exe`) |

---

## 🗣 Spoken Punctuation Commands

| Spoken (English) | Spoken (Persian) | Inserted Symbol |
| :--- | :--- | :---: |
| "period" / "full stop" | «نقطه» | `.` |
| "comma" | «ویرگول» / «کاما» | `،` or `,` |
| "question mark" | «علامت سوال» | `؟` or `?` |
| "exclamation mark" | «علامت تعجب» | `!` |
| "colon" | «دو نقطه» | `:` |
| "new line" / "enter" | «برو خط بعد» / «خط جدید» | Line break (`\n`) |
| "open parenthesis" / "close parenthesis" | «پرانتز باز» / «پرانتز بسته» | `(` / `)` |
| "open quote" / "close quote" | «گیومه باز» / «گیومه بسته» | `«` / `»` or `"` |
| "ellipsis" | «سه نقطه» | `...` |
| "dash" / "hyphen" | «خط تیره» | `-` |

---

## ⬇ Download & Installation

### Option 1: Windows Setup Installer (Recommended)
1. Download `VoiceToText-Setup-vX.X.X.exe` from [GitHub Releases](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases/latest).
2. Run the installer wizard:
   - Sets up Desktop and Start Menu shortcuts.
   - Registers standard Windows uninstall entry.
   - Option to automatically launch with Windows startup.
3. Launch from the Start menu or desktop icon.

### Option 2: Standalone Portable Executable
1. Download `VoiceToText.exe` from [GitHub Releases](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases/latest).
2. Run directly — no installation, no admin rights, and no Python required.

> **System Requirements:**
> - Windows 10 or 11 (64-bit)
> - Active Internet connection (for Google Speech API)
> - Working microphone

---

## 🚀 How to Use

```
1. Run the app — the microphone icon appears in the System Tray next to the clock.
2. Click any text field in any program (Notepad, Word, Browser, Telegram...).
3. Press Ctrl + Alt + V (or click the microphone on the floating pill).
4. Speak naturally — text will stream directly into the active field!
5. Press Ctrl + Alt + V again (or pause speaking) to finish.
```

---

## ⚙ Settings & Customization

Open settings by right-clicking the System Tray icon → **Settings**, or clicking the ⚙ icon on the floating widget:

- **Speech & Language:** Select default language (`fa-IR` or `en-US`), input microphone, and enable Persian typography / digit rules.
- **Streaming & Silence Detection:** Adjust audio chunk duration (1.0 – 4.0s) and silence timeout for automatic stopping.
- **Global Hotkey:** Change `Ctrl+Alt+V` to any custom key combination (e.g. `F8`, `Ctrl+Shift+Space`). Warns automatically if a shortcut is reserved by Windows.
- **Appearance & Theme:** Choose between System Default (adapts to Windows Dark/Light mode), Dark, or Light.
- **Updates:** Check for the latest releases from GitHub with 1-click download and install.

---

## 🛠 Building from Source (Developers)

```bash
# 1. Clone the repository
git clone https://github.com/mostafaafrouzi/Voice-to-Text-Windows.git
cd Voice-to-Text-Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run application
python main.py
```

### Build Standalone EXE:
```bash
python build_exe.py
# Output: dist/VoiceToText.exe
```

### Build Windows Installer:
```bash
python build_installer.py
# Output: dist/VoiceToText-Setup-v2.0.0.exe
```

---

## 🏗 Architecture

```
Voice-to-Text-Windows/
├── app/
│   ├── core/
│   │   ├── engine.py        # Real-time streaming speech engine (Google Speech API)
│   │   ├── audio_meter.py   # Streaming audio capture & real-time RMS meter
│   │   ├── text_cleaner.py  # Spoken punctuation processor & Persian half-space normalizer
│   │   ├── injector.py      # Focus-safe fast text injection via clipboard simulation
│   │   ├── hotkey.py        # Global asynchronous hotkey manager
│   │   ├── updater.py       # GitHub Releases auto-update checker & installer
│   │   └── autostart.py     # Windows Startup Registry manager (HKCU)
│   ├── ui/
│   │   ├── pill_widget.py   # Windows 11 Fluent floating capsule widget
│   │   ├── wave_widget.py   # Real-time 30 FPS audio waveform visualizer
│   │   ├── settings_win.py  # Comprehensive Fluent settings dialog
│   │   ├── tray_icon.py     # Windows System Tray manager with quick menu
│   │   ├── theme_manager.py # Dark/Light/System theme engine
│   │   └── fonts.py         # Vazirmatn font loader
│   ├── config.py            # Persistent settings manager (%APPDATA%)
│   └── version.py           # Central version metadata
├── assets/fonts/            # Embedded Vazirmatn font files
├── installer/setup.iss      # Inno Setup Windows installer script
├── .github/workflows/       # Automated CI/CD GitHub Actions release pipeline
├── tests/                   # Comprehensive automated test suite
├── build_exe.py             # PyInstaller standalone EXE builder
├── build_installer.py       # Local Inno Setup installer builder
└── main.py                  # Single-instance application entry point
```

---

## 🧪 Testing

Run all automated unit tests:
```bash
python -m unittest discover -s tests -v
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Made with ❤️ by [Mostafa Afrouzi](https://github.com/mostafaafrouzi)

⭐ Star this repository if you find it helpful!

</div>
