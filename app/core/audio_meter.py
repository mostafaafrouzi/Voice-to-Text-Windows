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

# اندازه هر پنجره کوچک ضبط (به نمونه) — تعادل بین تاخیر و کیفیت
WINDOW_SAMPLES = 4096   # ~256ms per chunk for level reading
STREAM_CHUNK_SECS = 1.5  # هر چند ثانیه یک قطعه برای Streaming استخراج می‌شود


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
    ضبط‌کننده Streaming بلادرنگ صوتی.
    صدا را در قطعات کوچک ضبط کرده و هر قطعه را از طریق callback به موتور
    تشخیص گفتار ارسال می‌کند تا تبدیل همزمان با صحبت انجام شود (مثل Gboard).
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
        self._is_recording = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _record_loop(self, device_index: int | None):
        self._p = pyaudio.PyAudio()
        silence_timeout = float(config.get("silence_timeout", 0.85))
        energy_threshold = float(config.get("energy_threshold", 280))

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

        # بافرهای جداگانه
        chunk_frames = []  # بافر قطعه جاری که به API ارسال می‌شود
        pre_buffer = []    # بافر پیش-صحبت (قبل از تشخیص صدا)
        PRE_BUF_MAX = 4    # تعداد پنجره‌های پیش-بافر (~256ms × 4 = 1s)

        speech_started = False
        last_voice_time = time.time()
        chunk_start_time = time.time()

        # Streaming Chunk Size: هر n ثانیه ارسال کن
        chunk_secs = float(config.get("stream_chunk_secs", STREAM_CHUNK_SECS))
        auto_stop = bool(config.get("auto_stop_on_silence", True))

        try:
            while self._is_recording:
                try:
                    data = self._stream.read(WINDOW_SAMPLES, exception_on_overflow=False)
                except Exception:
                    time.sleep(0.01)
                    continue

                if not data:
                    continue

                samples = np.frombuffer(data, dtype=np.int16)
                rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2))) if len(samples) > 0 else 0.0
                norm_level = min(1.0, max(0.0, (rms - 60) / 1200.0))

                if self.on_level_callback:
                    try:
                        self.on_level_callback(norm_level)
                    except Exception:
                        pass

                now = time.time()
                is_voice = rms > energy_threshold

                if is_voice:
                    if not speech_started:
                        speech_started = True
                        chunk_start_time = now
                        # بافر پیش-صحبت را به قطعه اضافه کن
                        chunk_frames.extend(pre_buffer)
                        pre_buffer.clear()
                    last_voice_time = now
                    chunk_frames.append(data)
                else:
                    if not speech_started:
                        # نگه داشتن پیش-بافر چرخشی
                        pre_buffer.append(data)
                        if len(pre_buffer) > PRE_BUF_MAX:
                            pre_buffer.pop(0)
                    else:
                        chunk_frames.append(data)

                # ارسال قطعه streaming اگر کافی بود
                if speech_started and chunk_frames:
                    elapsed_since_chunk = now - chunk_start_time
                    silence_since_voice = now - last_voice_time

                    should_send = (
                        elapsed_since_chunk >= chunk_secs or
                        (auto_stop and silence_since_voice >= silence_timeout)
                    )

                    if should_send:
                        # ساخت WAV از فریم‌های جاری
                        frames_to_send = list(chunk_frames)
                        chunk_frames = []
                        chunk_start_time = now

                        wav_bytes = self._build_wav(frames_to_send)
                        if wav_bytes and self.on_chunk_ready:
                            try:
                                self.on_chunk_ready(wav_bytes)
                            except Exception as e:
                                print(f"[StreamingRecorder] on_chunk_ready error: {e}")

                        # اگر سکوت تشخیص داده شد، ضبط متوقف شود
                        if auto_stop and silence_since_voice >= silence_timeout:
                            speech_started = False
                            if self.on_silence_detected:
                                try:
                                    self.on_silence_detected()
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


# حفظ backward compatibility
AudioRecorder = StreamingAudioRecorder
