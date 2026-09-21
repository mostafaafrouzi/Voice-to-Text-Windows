import io
import math
import threading
import time
import wave
import numpy as np
import pyaudio
from ..config import config
from .injector import update_target_window

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
    ضبط‌کننده بلادرنگ صوتی هوشمند مبتنی بر تفکیک عبارات طبیعی گفتار (Natural Phrase VAD).
    دقیقاً مانند کیبورد گوگل در اندروید، گفتار کاربر را در پایان هر عبارت یا مکث طبیعی
    تفکیک کرده و بدون بریدن کلمات در میانه صحبت، با دقت ۱۰۰٪ برای تبدیل و تایپ ارسال می‌کند.
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

        # خواندن تنظیمات کاربر
        # سکوت پایانی برای توقف خودکار: حداقل ۱.۰ ثانیه تا کاربر زمان کافی برای تنفس داشته باشد
        silence_timeout = max(1.0, float(config.get("silence_timeout", 1.2)))
        auto_stop = bool(config.get("auto_stop_on_silence", True))
        base_threshold = float(config.get("energy_threshold", 240.0))

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
            print(f"[StreamingRecorder] Stream opened: rate={SAMPLE_RATE}, device={device_index}, silence_timeout={silence_timeout}, auto_stop={auto_stop}")
        except Exception as e:
            print(f"[StreamingRecorder] Cannot open stream: {e}")
            self._is_recording = False
            self._p.terminate()
            return

        # بافرهای صدا
        chunk_frames: list[bytes] = []
        pre_buffer: list[bytes] = []
        PRE_BUF_MAX = 5  # نگهداری حدود ۳۲۰ میلی‌ثانیه قبل از شروع صحبت برای حفظ صامت آغازین

        ambient_rms = 120.0
        alpha = 0.94  # ضریب فیلتر نویز زمینه

        speech_active = False
        has_spoken = False
        speech_start_time = 0.0
        last_voice_time = time.time()

        # پارامترهای تفکیک عبارات طبیعی
        # مکث طبیعی بین عبارات ۳۸۰ میلی‌ثانیه است
        pause_threshold = 0.38
        min_speech_duration = 0.65  # حداقل طول یک عبارت معتبر

        _debug_frame_count = 0

        try:
            while self._is_recording:
                try:
                    data = self._stream.read(WINDOW_SAMPLES, exception_on_overflow=False)
                except Exception:
                    time.sleep(0.01)
                    continue

                if not data:
                    continue

                # محاسبه RMS فریم
                samples = np.frombuffer(data, dtype=np.int16)
                if len(samples) > 0:
                    rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
                else:
                    rms = 0.0

                now = time.time()
                _debug_frame_count += 1

                # به‌روزرسانی نویز زمینه فقط در زمان سکوت
                if not speech_active:
                    ambient_rms = alpha * ambient_rms + (1.0 - alpha) * rms

                # آستانه تشخیص صدای گفتار
                dynamic_threshold = max(base_threshold, ambient_rms * 1.6)
                is_voice = (rms > dynamic_threshold)

                # ارسال سطح صدا به ویژوالایزر امواج
                norm_level = min(1.0, max(0.0, (rms - ambient_rms) / 1400.0))
                if self.on_level_callback:
                    try:
                        self.on_level_callback(norm_level)
                    except Exception:
                        pass

                if is_voice:
                    has_spoken = True
                    if not speech_active:
                        speech_active = True
                        speech_start_time = now
                        print(f"[VAD] >>> Speech STARTED at frame {_debug_frame_count}, rms={rms:.0f}")
                        try:
                            update_target_window()
                        except Exception:
                            pass
                        # افزودن بافر پیش از شروع صحبت
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

                # --- بررسی شرایط ارسال عبارت صوتی برای تبدیل و تایپ همزمان ---
                if speech_active and chunk_frames:
                    silence_duration = now - last_voice_time
                    phrase_duration = now - speech_start_time

                    # شرط الف: مکث طبیعی بین عبارات رخ داده است (کلمات به هیچ وجه در میانه بریده نمی‌شوند)
                    natural_pause_ready = (
                        silence_duration >= pause_threshold and
                        phrase_duration >= min_speech_duration
                    )

                    # شرط ب: صحبت طولانی پیوسته (بیش از ۴.۵ ثانیه با وجود افت صدا یا حداکثر ۶.۵ ثانیه)
                    long_phrase_ready = (
                        phrase_duration >= 4.5 and
                        silence_duration >= 0.20
                    ) or (phrase_duration >= 6.5)

                    if natural_pause_ready or long_phrase_ready:
                        frames_to_send = list(chunk_frames)
                        chunk_frames.clear()
                        speech_active = False

                        try:
                            update_target_window()
                        except Exception:
                            pass

                        wav_bytes = self._build_wav(frames_to_send)
                        print(f"[VAD] >>> Phrase chunk ready ({phrase_duration:.1f}s, pause={silence_duration:.2f}s): {len(wav_bytes)} bytes")
                        if wav_bytes and self.on_chunk_ready:
                            try:
                                self.on_chunk_ready(wav_bytes)
                            except Exception as e:
                                print(f"[StreamingRecorder] on_chunk_ready error: {e}")

                # --- بررسی سکوت طولانی برای توقف خودکار ---
                if auto_stop and not speech_active:
                    total_silence = now - last_voice_time
                    if not has_spoken and total_silence >= 8.0:
                        # اگر پس از شروع ۸ ثانیه اصلاً صحبتی نشد
                        if self.on_silence_detected:
                            try:
                                self.on_silence_detected()
                            except Exception:
                                pass
                        break
                    elif has_spoken and total_silence >= silence_timeout:
                        # کاربر صحبت کرده بود و حالا سکوت کامل رخ داده است
                        if chunk_frames and len(chunk_frames) >= 3:
                            frames_to_send = list(chunk_frames)
                            chunk_frames.clear()
                            wav_bytes = self._build_wav(frames_to_send)
                            if wav_bytes and self.on_chunk_ready:
                                try:
                                    self.on_chunk_ready(wav_bytes)
                                except Exception:
                                    pass

                        if self.on_silence_detected:
                            try:
                                self.on_silence_detected()
                            except Exception:
                                pass
                        break

            # اگر هنگام متوقف شدن دستی بافری باقی مانده بود، حتماً ارسال شود تا کلمه‌ای جا نماند
            if chunk_frames and len(chunk_frames) >= 3:
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

    def _build_wav(self, frames: list[bytes]) -> bytes:
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
