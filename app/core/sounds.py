import io
import math
import os
import struct
import tempfile
import wave
import winsound
from ..config import config


def _generate_wav(frequencies: list[int], duration_ms: int = 120, volume: float = 0.25) -> bytes:
    """تولید صدای ملایم و نرم با محوشدگی تدریجی در حافظه."""
    sample_rate = 22050
    total_samples = int(sample_rate * (duration_ms / 1000.0))
    buf = io.BytesIO()

    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        attack = int(sample_rate * 0.015)
        release = int(sample_rate * 0.035)
        frames = bytearray()

        for i in range(total_samples):
            t = float(i) / sample_rate
            if i < attack:
                env = i / attack
            elif i > (total_samples - release):
                env = (total_samples - i) / release
            else:
                env = 1.0

            frac = i / total_samples
            idx = min(int(frac * len(frequencies)), len(frequencies) - 1)
            freq = frequencies[idx]

            sample_val = int(volume * 32767.0 * env * math.sin(2.0 * math.pi * freq * t))
            sample_val = max(-32767, min(32767, sample_val))
            frames.extend(struct.pack("<h", sample_val))

        wf.writeframes(frames)

    return buf.getvalue()


def _save_to_temp(wav_bytes: bytes, name: str) -> str:
    """ذخیره صدا در فایل موقت برای پخش بدون خطا."""
    tmp_dir = os.path.join(tempfile.gettempdir(), "VoiceToText_sounds")
    os.makedirs(tmp_dir, exist_ok=True)
    path = os.path.join(tmp_dir, f"{name}.wav")
    with open(path, "wb") as f:
        f.write(wav_bytes)
    return path


# پیش‌تولید فایل‌های صداها
_SOUND_START_PATH = _save_to_temp(
    _generate_wav([523, 784], duration_ms=130, volume=0.25), "start")
_SOUND_STOP_PATH = _save_to_temp(
    _generate_wav([784, 1046], duration_ms=110, volume=0.22), "stop")
_SOUND_CANCEL_PATH = _save_to_temp(
    _generate_wav([659, 440], duration_ms=150, volume=0.20), "cancel")


def play_start_sound():
    if not config.get("audio_feedback", True):
        return
    try:
        winsound.PlaySound(_SOUND_START_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as e:
        print(f"[Sound] play_start_sound error: {e}")


def play_stop_sound():
    if not config.get("audio_feedback", True):
        return
    try:
        winsound.PlaySound(_SOUND_STOP_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as e:
        print(f"[Sound] play_stop_sound error: {e}")


def play_cancel_sound():
    if not config.get("audio_feedback", True):
        return
    try:
        winsound.PlaySound(_SOUND_CANCEL_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except Exception as e:
        print(f"[Sound] play_cancel_sound error: {e}")

