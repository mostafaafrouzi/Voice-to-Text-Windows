import io
import threading
import time
import speech_recognition as sr
from .audio_meter import StreamingAudioRecorder
from .injector import inject_text
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
    موتور Streaming تشخیص گفتار — مشابه رفتار دقیق کیبورد گوگل (Gboard) در اندروید.
    هر قطعه صوتی بلافاصله به Google Speech API ارسال شده و متن همزمان با صحبت
    در برنامه فعال تایپ می‌شود.
    """

    def __init__(self, on_state_change=None, on_level_change=None, on_result=None):
        self.on_state_change = on_state_change
        self.on_level_change = on_level_change
        self.on_result = on_result

        self._state = SpeechState.IDLE
        self._recognizer = sr.Recognizer()
        self._lock = threading.Lock()
        self._session_texts = []  # تمام متن‌های تایپ‌شده در یک جلسه
        self._transcribe_pool_lock = threading.Lock()
        self._active_transcribes = 0

        self._recorder = StreamingAudioRecorder(
            on_level_callback=self._handle_audio_level,
            on_chunk_ready=self._handle_chunk_ready,
            on_silence_detected=self._handle_session_ended
        )

    @property
    def state(self) -> str:
        return self._state

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
        """
        هر قطعه صوتی آماده شد — بلافاصله در یک ترد جداگانه به API ارسال کن.
        این عملیات بلوک‌کننده نیست و ضبط ادامه می‌یابد.
        """
        if not wav_bytes or len(wav_bytes) < 2000:
            return

        with self._transcribe_pool_lock:
            self._active_transcribes += 1

        # نمایش وضعیت ترکیبی: در حال گوش دادن + پردازش
        if self._state == SpeechState.LISTENING:
            self._set_state(SpeechState.LISTENING, "در حال تبدیل...")

        t = threading.Thread(
            target=self._transcribe_and_inject,
            args=(wav_bytes,),
            daemon=True
        )
        t.start()

    def _handle_session_ended(self):
        """جلسه صوتی به پایان رسید — انتظار برای پایان تمام پردازش‌های در حال اجرا."""
        # صبر کن تا همه پردازش‌ها تمام شوند
        max_wait = 8.0
        start = time.time()
        while True:
            with self._transcribe_pool_lock:
                if self._active_transcribes <= 0:
                    break
            if time.time() - start > max_wait:
                break
            time.sleep(0.05)

        play_stop_sound()
        self._session_texts.clear()
        self._set_state(SpeechState.IDLE, "")

    def _transcribe_and_inject(self, wav_bytes: bytes):
        try:
            language = config.get("language", "fa-IR")
            enable_punct = config.get("enable_persian_punctuation", True)
            enable_half = config.get("enable_half_space", True)
            persian_digits = config.get("persian_digits", False)

            with io.BytesIO(wav_bytes) as buf:
                with sr.AudioFile(buf) as source:
                    audio_data = self._recognizer.record(source)

            raw_text = self._recognizer.recognize_google(audio_data, language=language)

            if not raw_text or not raw_text.strip():
                return

            cleaned_text = clean_text(
                raw_text,
                language=language,
                enable_punctuation=enable_punct,
                enable_half_space=enable_half,
                persian_digits=persian_digits
            )

            if not cleaned_text:
                return

            # تزریق فوری — این بخش قلب Streaming است
            inject_text(cleaned_text + " ")

            self._session_texts.append(cleaned_text)

            if self.on_result:
                try:
                    self.on_result(raw_text, cleaned_text)
                except Exception:
                    pass

        except sr.UnknownValueError:
            # صدا وجود داشت ولی قابل تشخیص نبود — به آرامی رد می‌شود
            pass

        except sr.RequestError as e:
            print(f"[Engine] Google Speech API error: {e}")
            play_cancel_sound()
            self._set_state(SpeechState.ERROR, "خطا در اتصال به سرور گوگل. اینترنت را بررسی کنید.")
            time.sleep(2.0)
            if self._state == SpeechState.ERROR:
                self._set_state(SpeechState.IDLE if not self._recorder.is_recording else SpeechState.LISTENING, "")

        except Exception as e:
            print(f"[Engine] Unexpected error: {e}")

        finally:
            with self._transcribe_pool_lock:
                self._active_transcribes = max(0, self._active_transcribes - 1)

    def start_listening(self):
        with self._lock:
            if self._state == SpeechState.LISTENING or self._recorder.is_recording:
                return
            self._session_texts.clear()
            mic_index = config.get("microphone_index")
            play_start_sound()
            self._set_state(SpeechState.LISTENING, "در حال گوش دادن...")
            self._recorder.start(device_index=mic_index)

    def stop_and_finalize(self):
        with self._lock:
            if not self._recorder.is_recording and self._state != SpeechState.LISTENING:
                return
            self._recorder.stop()

        # بعد از توقف، منتظر می‌مانیم تا پردازش‌های در حال اجرا تمام شوند
        threading.Thread(target=self._handle_session_ended, daemon=True).start()

    def cancel(self):
        with self._lock:
            if self._recorder.is_recording:
                self._recorder.stop()
        play_cancel_sound()
        self._session_texts.clear()
        self._set_state(SpeechState.IDLE, "")

    def toggle(self):
        if self._state == SpeechState.LISTENING:
            self.stop_and_finalize()
        elif self._state in (SpeechState.IDLE, SpeechState.SUCCESS, SpeechState.ERROR):
            self.start_listening()


# Export با نام قبلی برای compatibility
SpeechEngine = StreamingSpeechEngine
