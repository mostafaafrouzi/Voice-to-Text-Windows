import io
import queue
import threading
import time
import speech_recognition as sr
from .audio_meter import StreamingAudioRecorder
from .injector import inject_text, start_new_session
from .sounds import play_cancel_sound, play_start_sound, play_stop_sound
from .text_cleaner import clean_text
from ..config import config


class SpeechState:
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    SUCCESS = "success"
    ERROR = "error"


class StreamingSpeechEngine:
    """
    موتور هوشمند تبدیل گفتار به متن — دقیقاً مشابه کیبورد گوگل (Gboard) در اندروید.
    قطعات گفتاری را به ترتیب دریافت کرده، با Google Cloud Speech API به متن تبدیل
    می‌کند و بلافاصله به مکان‌نمای فعال کاربر تزریق می‌نماید.
    """

    def __init__(self, on_state_change=None, on_level_change=None, on_result=None):
        self.on_state_change = on_state_change
        self.on_level_change = on_level_change
        self.on_result = on_result

        self._state = SpeechState.IDLE
        self._recognizer = sr.Recognizer()
        self._lock = threading.Lock()

        # صف پردازش متوالی تا کلمات به ترتیب ارسال و تایپ شوند
        self._queue = queue.Queue()
        self._worker_thread = None
        self._stop_worker = False

        self._recorder = StreamingAudioRecorder(
            on_level_callback=self._handle_audio_level,
            on_chunk_ready=self._handle_chunk_ready,
            on_silence_detected=self._handle_silence_detected
        )

        self._start_worker()

    @property
    def state(self) -> str:
        return self._state

    def _start_worker(self):
        self._stop_worker = False
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _set_state(self, new_state: str, message: str = ""):
        self._state = new_state
        if self.on_state_change:
            try:
                self.on_state_change(new_state, message)
            except Exception as e:
                print(f"[Engine] state callback error: {e}")

    def _handle_audio_level(self, level: float):
        if self.on_level_change:
            try:
                self.on_level_change(level)
            except Exception:
                pass

    def _handle_chunk_ready(self, wav_bytes: bytes):
        """دریافت یک قطعه صوتی و قرار دادن آن در صف پردازش ترتیبی."""
        print(f"[Engine] _handle_chunk_ready: received {len(wav_bytes)} bytes")
        if not wav_bytes or len(wav_bytes) < 3000:
            print(f"[Engine] _handle_chunk_ready: SKIPPED (too small: {len(wav_bytes)} bytes)")
            return
        self._queue.put(wav_bytes)
        print(f"[Engine] _handle_chunk_ready: queued for transcription (queue size: {self._queue.qsize()})")

    def _handle_silence_detected(self):
        """سکوت پایانی کاربر تشخیص داده شد."""
        self.stop_and_finalize()

    def _worker_loop(self):
        """حلقه کاری پردازش ترتیبی صف قطعات صوتی."""
        while not self._stop_worker:
            try:
                wav_bytes = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            try:
                self._process_chunk(wav_bytes)
            except Exception as e:
                print(f"[Engine] Worker error: {e}")
            finally:
                self._queue.task_done()

                # اگر ضبط متوقف شده و صف خالی شد، پایان جلسه را اعلام کن
                if not self._recorder.is_recording and self._queue.empty():
                    if self._state != SpeechState.ERROR:
                        play_stop_sound()
                        self._set_state(SpeechState.IDLE, "")

    def _process_chunk(self, wav_bytes: bytes):
        language = config.get("language", "fa-IR")
        enable_punct = config.get("enable_persian_punctuation", True)
        enable_half = config.get("enable_half_space", True)
        persian_digits = config.get("persian_digits", False)

        try:
            with io.BytesIO(wav_bytes) as buf:
                with sr.AudioFile(buf) as source:
                    audio_data = self._recognizer.record(source)

            # فراخوانی Google Cloud Speech Recognition
            print(f"[Engine] Sending {len(wav_bytes)} bytes to Google Speech API (lang={language})...")
            raw_text = self._recognizer.recognize_google(audio_data, language=language)
            print(f"[Engine] Google returned: '{raw_text}'")

            if not raw_text or not raw_text.strip():
                print(f"[Engine] Empty result from Google, skipping.")
                return

            cleaned_text = clean_text(
                raw_text,
                language=language,
                enable_punctuation=enable_punct,
                enable_half_space=enable_half,
                persian_digits=persian_digits
            )

            if not cleaned_text:
                print(f"[Engine] clean_text returned empty, skipping.")
                return

            # تزریق آنی متن در فیلد متنی فعال
            to_inject = cleaned_text if cleaned_text.endswith("\n") else (cleaned_text + " ")
            print(f"[Engine] Injecting text: '{cleaned_text[:30]}...'")
            inject_text(to_inject)

            if self.on_result:
                try:
                    self.on_result(raw_text, cleaned_text)
                except Exception:
                    pass

        except sr.UnknownValueError:
            # صدای نامفهوم — رد می‌شود
            pass

        except sr.RequestError as e:
            print(f"[Engine] Google Speech API RequestError: {e}")
            play_cancel_sound()
            self._set_state(SpeechState.ERROR, "خطا در اتصال به اینترنت برای تشخیص گفتار")
            time.sleep(2.0)
            if self._state == SpeechState.ERROR:
                self._set_state(SpeechState.IDLE if not self._recorder.is_recording else SpeechState.LISTENING, "")

        except Exception as e:
            print(f"[Engine] Transcribe exception: {e}")

    def start_listening(self):
        with self._lock:
            if self._state == SpeechState.LISTENING or self._recorder.is_recording:
                return
            start_new_session()
            mic_index = config.get("microphone_index")
            play_start_sound()
            self._set_state(SpeechState.LISTENING, "در حال گوش دادن...")
            self._recorder.start(device_index=mic_index)

    def stop_and_finalize(self):
        with self._lock:
            if not self._recorder.is_recording and self._state != SpeechState.LISTENING:
                return
            self._recorder.stop()

        # اگر صف خالی است، فوراً خاتمه بده؛ اگر هنوز آیتم دارد، ورکر پس از اتمام خارج می‌شود
        if self._queue.empty():
            play_stop_sound()
            self._set_state(SpeechState.IDLE, "")

    def cancel(self):
        with self._lock:
            if self._recorder.is_recording:
                self._recorder.stop()
            # خالی کردن صف آیتم‌های منتظر
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except Exception:
                    break
        play_cancel_sound()
        self._set_state(SpeechState.IDLE, "")

    def toggle(self):
        if self._state == SpeechState.LISTENING:
            self.stop_and_finalize()
        elif self._state in (SpeechState.IDLE, SpeechState.SUCCESS, SpeechState.ERROR):
            self.start_listening()


SpeechEngine = StreamingSpeechEngine
