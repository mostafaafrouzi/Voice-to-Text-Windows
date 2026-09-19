import io
import math
import threading
import time
import wave
import numpy as np
import pyaudio
from ..config import config

SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16

# اندازه پنجره نمونه‌برداری بلادرنگ — 1024 نمونه معادل 64 میلی‌ثانیه برای ویژوالایزر نرم
WINDOW_SAMPLES = 1024


def get_input_devices() -> list[dict]:
    p = pyaudio.PyAudio()
    devices = []
    seen = set()
    try:
        default_index = None
        try:
            default_device = p.get_default_input_device_info()
            default_index = default_device.get("index")
        except Exception:
            pass

        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    name = info.get("name", f"Mic {i}")
                    if name not in seen:
                        devices.append({
                            "index": i,
                            "name": name,
                            "is_default": (i == default_index)
                        })
                        seen.add(name)
            except Exception:
                pass
    finally:
        p.terminate()
    return devices


class StreamingAudioRecorder:
    """
    ضبط‌کننده هوشمند صوتی با تفکیک عبارات بر اساس مکث‌های طبیعی صحبت (VAD).
    به جای بریدن کورکورانه کلمات در زمان‌های ثابت، پایان هر عبارت یا مکث کاربر را
    تشخیص داده و صدا را کامل به موتور گفتار ارسال می‌کند تا هیچ کلمه‌ای جا نماند.
    """

    def __init__(
        self,
        on_level_callback=None,
        on_chunk_ready=None,
        on_silence_detected=None
    ):
        self.on_level_callback = on_level_callback
        self.on_chunk_ready = on_chunk_ready
        self.on_silence_detected = on_silence_detected

        self._is_recording = False
        self._thread = None
        self._p = None
        self._stream = None
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self, device_index: int | None = None):
        with self._lock:
            if self._is_recording:
                return
            self._is_recording = True
            self._thread = threading.Thread(
                target=self._record_loop,
                args=(device_index,),
                daemon=True
            )
            self._thread.start()

    def stop(self):
        with self._lock:
            self._is_recording = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _record_loop(self, device_index: int | None):
        self._p = pyaudio.PyAudio()
        silence_timeout = float(config.get("silence_timeout", 1.2))
        auto_stop = bool(config.get("auto_stop_on_silence", True))

        stream_kwargs = {
            "format": FORMAT,
            "channels": CHANNELS,
            "rate": SAMPLE_RATE,
            "input": True,
            "frames_per_buffer": WINDOW_SAMPLES,
        }
        if device_index is not None and device_index >= 0:
            stream_kwargs["input_device_index"] = device_index

        try:
            self._stream = self._p.open(**stream_kwargs)
        except Exception as e:
            print(f"[StreamingRecorder] Cannot open stream: {e}")
            self._is_recording = False
            self._p.terminate()
            return

        # بافرهای صدا
        chunk_frames = []
        pre_buffer = []
        PRE_BUF_MAX = 6   # نگهداری حدود ۳۸۰ میلی‌ثانیه قبل از شروع صحبت

        # متغیرهای ردیابی نویز محیط و آستانه صدا
        ambient_rms = 120.0
        alpha = 0.95      # ضریب فیلتر پایین‌گذر برای سطح نویز زمینه

        speech_active = False
        speech_start_time = 0.0
        last_voice_time = time.time()
        pause_threshold = 0.42  # مکث طبیعی بین عبارات (۴۲۰ میلی‌ثانیه)
        min_speech_duration = 0.5  # حداقل طول صحبت برای ارسال به عنوان یک قطعه
        max_phrase_duration = 7.0  # حداکثر طول یک قطعه بدون مکث

        try:
            while self._is_recording:
                try:
                    data = self._stream.read(WINDOW_SAMPLES, exception_on_overflow=False)
                except Exception:
                    time.sleep(0.01)
                    continue

                if not data:
                    continue

                # محاسبه RMS صدا
                samples = np.frombuffer(data, dtype=np.int16)
                if len(samples) > 0:
                    rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
                else:
                    rms = 0.0

                now = time.time()

                # به‌روزرسانی نویز زمینه فقط وقتی صحبت نمی‌شود
                if not speech_active:
                    ambient_rms = alpha * ambient_rms + (1.0 - alpha) * rms

                # آستانه تشخیص صدای صحبت
                dynamic_threshold = max(240.0, ambient_rms * 1.8)
                is_voice = rms > dynamic_threshold

                # ارسال شدت صدا به ویژوالایزر (نرم‌شده)
                norm_level = min(1.0, max(0.0, (rms - ambient_rms) / 1400.0))
                if self.on_level_callback:
                    try:
                        self.on_level_callback(norm_level)
                    except Exception:
                        pass

                if is_voice:
                    if not speech_active:
                        speech_active = True
                        speech_start_time = now
                        # افزودن بافر پیش از شروع صحبت تا هجای آغازین قطع نشود
                        chunk_frames.extend(pre_buffer)
                        pre_buffer.clear()

                    last_voice_time = now
                    chunk_frames.append(data)
                else:
                    if not speech_active:
                        pre_buffer.append(data)
                        if len(pre_buffer) > PRE_BUF_MAX:
                            pre_buffer.pop(0)
                    else:
                        chunk_frames.append(data)

                # بررسی اتمام یا ارسال یک عبارت
                if speech_active and chunk_frames:
                    silence_duration = now - last_voice_time
                    phrase_duration = now - speech_start_time

                    # شرط ۱: مکث طبیعی بین کلمات/عبارات رخ داده
                    natural_pause_ready = (
                        silence_duration >= pause_threshold and
                        phrase_duration >= min_speech_duration
                    )

                    # شرط ۲: صحبت طولانی پیوسته (بیش از ۷ ثانیه)
                    too_long = phrase_duration >= max_phrase_duration and silence_duration >= 0.2

                    if natural_pause_ready or too_long:
                        # استخراج قطعه کامل
                        frames_to_send = list(chunk_frames)
                        chunk_frames = []
                        speech_active = False

                        wav_bytes = self._build_wav(frames_to_send)
                        if wav_bytes and self.on_chunk_ready:
                            try:
                                self.on_chunk_ready(wav_bytes)
                            except Exception as e:
                                print(f"[StreamingRecorder] on_chunk_ready error: {e}")

                    # بررسی سکوت طولانی نهایی برای توقف خودکار
                    if auto_stop and silence_duration >= silence_timeout:
                        if self.on_silence_detected:
                            try:
                                self.on_silence_detected()
                            except Exception:
                                pass
                        break

            # اگر بافر پایانی باقی مانده است، هنگام توقف ارسال شود
            if chunk_frames and (time.time() - speech_start_time >= min_speech_duration):
                wav_bytes = self._build_wav(chunk_frames)
                if wav_bytes and self.on_chunk_ready:
                    try:
                        self.on_chunk_ready(wav_bytes)
                    except Exception:
                        pass

        finally:
            try:
                if self._stream:
                    self._stream.stop_stream()
                    self._stream.close()
            except Exception:
                pass
            try:
                if self._p:
                    self._p.terminate()
            except Exception:
                pass

        if self.on_level_callback:
            try:
                self.on_level_callback(0.0)
            except Exception:
                pass

    def _build_wav(self, frames: list) -> bytes:
        if not frames:
            return b""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
        return buf.getvalue()


AudioRecorder = StreamingAudioRecorder
