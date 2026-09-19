import json
import os
import sys
from pathlib import Path

DEFAULT_CONFIG = {
    "language": "fa-IR",
    "hotkey": "ctrl+alt+v",
    "microphone_index": None,
    "audio_feedback": True,
    "enable_persian_punctuation": True,
    "enable_half_space": True,
    "persian_digits": False,
    "injection_method": "clipboard",
    "theme": "system",
    "widget_x": -1,
    "widget_y": -1,
    "silence_timeout": 0.80,
    "stream_chunk_secs": 1.5,
    "energy_threshold": 280,
    "auto_stop_on_silence": True,
    "autostart": False,
    "check_updates_on_start": True,
}



def get_config_dir() -> Path:
    """Returns the persistent configuration directory in AppData or user home."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        base_dir = Path(appdata) / "VoiceToTextWindows"
    else:
        base_dir = Path.home() / ".voicetotext_windows"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


class ConfigManager:
    """Manages application settings with JSON file persistence."""

    def __init__(self):
        self._path = get_config_path()
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    if isinstance(user_data, dict):
                        self._data.update(user_data)
            except Exception as e:
                print(f"[Config] Error loading config, using defaults: {e}")

    def save(self):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    def get(self, key, default=None):
        return self._data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def update(self, new_data: dict):
        self._data.update(new_data)
        self.save()

    def all(self) -> dict:
        return dict(self._data)


config = ConfigManager()
