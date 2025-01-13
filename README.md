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

---

## Usage

### Launch the Application
1. Run `voice_to_text.py`.
2. Use the 🎤 button to toggle the microphone on or off.
3. Alternatively, press `Ctrl + Alt + V` to start or stop voice-to-text.

### Settings
- You can:
  - Select the recognition **language** (automatically synced with Windows keyboard layout).
  - Switch between **Google** (online) and **Vosk** (offline) models.

---

## Shortcuts
- **`Ctrl + Alt + V`**: Start or stop voice-to-text.

---

## Debugging
- Logs are stored in `debug_log.txt` in the application directory for troubleshooting.

---

## Contribution
Feel free to fork the repository, contribute new features, or fix bugs. Pull requests are welcome!

---

## License
This project is licensed under the [MIT License](LICENSE).

---

### Dependencies
The following Python libraries are required to run this project:
- `speechrecognition`
- `vosk`
- `pynput`
- `tk`
- `pyaudio`
- `pywin32`

Install them with:
```bash
pip install -r requirements.txt
```

---

### Notes
```plaintext
- **Vosk Model**: Ensure you download and place a Vosk model in the project directory for offline recognition.
- **Permissions**: Some features may require administrative permissions for proper functionality.
- **Supported Languages**: Google Speech Recognition supports multiple languages, and the language will sync automatically with the Windows keyboard layout.
```
