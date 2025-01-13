# Voice-to-Text
A modern, lightweight application for converting speech to text using Google and Vosk speech recognition models. This application automatically synchronizes with the Windows keyboard layout to provide multilingual support.

---

## Features
- **Real-time voice-to-text conversion**
- **Supports multiple models**: Google and Vosk
- **Automatic language synchronization** with Windows keyboard layout
- **Customizable settings** for language and model selection
- **Global keyboard shortcut**: `Ctrl + Alt + V` to toggle the microphone
- **Debug logging** for troubleshooting

---

## Installation

### Prerequisites
- Python 3.9 or higher
- Ensure `pip` is installed for managing dependencies
- A working microphone

### Steps
```bash
git clone https://github.com/your-username/voice-to-text.git
cd voice-to-text
pip install -r requirements.txt
python voice_to_text.py
