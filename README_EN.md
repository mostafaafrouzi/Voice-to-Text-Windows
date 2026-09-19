<div align="center">

<a href="https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases/latest">
  <img src="https://img.shields.io/github/v/release/mostafaafrouzi/Voice-to-Text-Windows?style=for-the-badge&logo=github&color=2f81f7" alt="Latest Release">
</a>
<a href="https://github.com/mostafaafrouzi/Voice-to-Text-Windows/actions">
  <img src="https://img.shields.io/github/actions/workflow/status/mostafaafrouzi/Voice-to-Text-Windows/release.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white" alt="Build Status">
</a>
<a href="https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases">
  <img src="https://img.shields.io/github/downloads/mostafaafrouzi/Voice-to-Text-Windows/total?style=for-the-badge&logo=windows&color=3fb950" alt="Downloads">
</a>
<img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078d4?style=for-the-badge&logo=windows&logoColor=white" alt="Platform">
<a href="LICENSE">
  <img src="https://img.shields.io/badge/License-MIT-f39c12?style=for-the-badge" alt="License">
</a>

<br><br>

# 🎙 Voice-to-Text Windows 11
### **Intelligent, Real-Time Cloud Voice Typing for Windows**

> **Replicating the seamless, instantaneous voice typing experience of Google Keyboard (Gboard) and Android Speech Services across all Windows apps — 100% Free, no API keys, and no heavy offline models required.**

[⬇ Download Installer (Setup)](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases/latest) • 
[📋 Release Notes](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/releases) • 
[🐛 Report Bug / Feature Request](https://github.com/mostafaafrouzi/Voice-to-Text-Windows/issues) • 
[🇮🇷 راهنمای فارسی (Persian)](README.md)

</div>

---

## 🌟 Why Voice-to-Text Windows?

On Android devices, Google Keyboard (**Gboard**) and **Google Speech Services** deliver one of the fastest, most accurate voice typing experiences in the world, particularly for languages like Persian (Farsi) and English. 

On Windows, however:
- The default built-in voice typing (`Win + H`) has very poor or non-existent Persian language dictation.
- Third-party alternatives are often expensive subscription services, or require downloading multi-gigabyte models that hog GPU and RAM.

**Voice-to-Text Windows** solves this: a modern, lightweight, free, and lightning-fast voice dictation assistant for Windows 10 & 11. Powered by Google's cloud speech recognition engine, it activates anywhere with a single global shortcut (`Ctrl + Alt + V`) and streams transcribed text directly into whatever text field you are typing in (Word, Telegram, WhatsApp, Chrome, VS Code, Discord, etc.).

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| ⚡ **Real-Time Streaming Dictation** | Transcribes speech incrementally as you talk — just like Gboard on Android |
| 🧠 **Intelligent VAD (Pause Detection)** | Audio is chunked during natural sentence pauses so words are never cut in half during fast speech |
| 🌐 **Bilingual (Persian & English)** | Flawless accuracy for Persian (`fa-IR`) and English (`en-US`) with instant one-click switching |
| 🎯 **Universal Compatibility** | Works across any input field in any application (Word, Browser, Telegram, Slack, etc.) |
| 🎨 **Windows 11 Fluent Acrylic UI** | Modern floating capsule widget with smooth drop shadows, draggable anywhere on screen |
| 🔒 **Focus-Safe Non-Activating Window** | Uses Win32 `WS_EX_NOACTIVATE` — never steals focus or cursor from your target app |
| 🌊 **Audio Waveform Visualizer** | Smooth 30 FPS visualizer responsive to real-time microphone amplitude |
| ✍️ **Intelligent Spoken Punctuation** | Say "period", "comma", "question mark", "new line" (or Persian equivalents) to insert punctuation |
| 📐 **Persian Half-Space Normalization** | Automatically normalizes Persian half-spaces (نیم‌فاصله) for «می‌شود», «کتاب‌ها», «سریع‌تر» |
| 🌓 **Adaptive Theme (Dark/Light/System)**| Seamlessly follows Windows 11 theme preferences or allows manual override with live preview |
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

## ⚙ Settings Dialog

Access the settings by clicking the ⚙ gear button on the floating pill or right-clicking the System Tray icon:
- **Language selection:** Persian (`fa-IR`) or English (`en-US`).
- **Microphone selection:** Default system mic or specific audio input hardware.
- **Custom Hotkey:** Change `Ctrl + Alt + V` to any preferred shortcut (with reserved Windows key validation).
- **Streaming audio tuning:** Adjust slice length (1.0s - 4.0s) and silence timeout detection.
- **Theme Selection:** System Sync, Force Dark, or Force Light mode with live instantaneous UI preview.
- **Persian Text Normalization:** Toggle spoken punctuation, Persian digits, and half-space rules.
- **Autostart:** Start minimized to System Tray on Windows boot.
- **Updates:** Check for new releases and perform 1-click automatic in-app updates.

---

## 💻 Developer & Build Guide

```bash
# Clone the repository
git clone https://github.com/mostafaafrouzi/Voice-to-Text-Windows.git
cd Voice-to-Text-Windows

# Install dependencies
pip install -r requirements.txt

# Run from source
python main.py
```

### Build Standalone Executable:
```bash
python build_exe.py
# Compiled binary located at: dist/VoiceToText.exe
```

### Build Windows Installer:
```bash
python build_installer.py
# Requires Inno Setup 6: generates dist/VoiceToText-Setup-vX.X.X.exe
```

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>Does this require an API key or credit card?</b></summary>
No. The app connects to the public Google Speech Recognition endpoint, requiring no API key and no payments.
</details>

<details>
<summary><b>Will fast speaking drop words?</b></summary>
No. Our custom Voice Activity Detection (VAD) buffer synchronizes with sentence rhythm and natural speech pauses, avoiding arbitrary mid-word audio cuts.
</details>

<details>
<summary><b>Does the floating widget block application clicks?</b></summary>
No. The widget uses Win32 <code>WS_EX_NOACTIVATE</code>, meaning clicks and keystrokes are preserved in your target application. You can also hide the widget with the ✕ button to run purely via the tray icon and shortcut.
</details>

---

## 📄 License

This project is open source and licensed under the [MIT License](LICENSE).

---

<div align="center">

Built with ❤️ by [Mostafa Afrouzi](https://github.com/mostafaafrouzi)

⭐ If you find this project useful, please consider giving it a star on GitHub!

</div>
