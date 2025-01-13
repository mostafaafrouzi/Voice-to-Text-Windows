import speech_recognition as sr
from vosk import Model, KaldiRecognizer
from pynput.keyboard import Controller
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard
import threading
import win32api
import win32con
import time
import ctypes
from queue import Queue
import wave
import os

# Flag to control the activation of voice-to-text
is_active = False
keyboard_controller = Controller()  # For sending keyboard input
audio_queue = Queue()  # Queue for audio processing
result_buffer = []  # Buffer to hold partial results

# Debug log function
def debug_log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    with open("debug_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

# Function to get current keyboard layout
def get_current_keyboard_language():
    user32 = ctypes.windll.user32
    current_window = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(current_window, None)
    layout_id = user32.GetKeyboardLayout(thread_id)
    lang_code = layout_id & 0xFFFF
    return lang_code

# Map keyboard layout codes to Google Speech Recognition language codes
keyboard_language_map = {
    0x0409: 'en-US',  # English (US)
    0x0429: 'fa-IR',  # Persian
    0x0410: 'it-IT',  # Italian
    0x040C: 'fr-FR',  # French
    0x0416: 'pt-BR',  # Portuguese (Brazil)
    0x0407: 'de-DE',  # German
    0x0419: 'ru-RU',  # Russian
    0x0411: 'ja-JP',  # Japanese
    0x0412: 'ko-KR',  # Korean
    0x0804: 'zh-CN',  # Chinese (Simplified)
    0x041E: 'th-TH',  # Thai
    0x040A: 'es-ES',  # Spanish
    # Add more mappings as needed
}

# Function to get the current language for Google Speech Recognition
def get_google_language():
    lang_code = get_current_keyboard_language()
    return keyboard_language_map.get(lang_code, 'en-US')  # Default to English (US)

# Function to synchronize language with Windows keyboard
def sync_language_with_keyboard():
    current_lang = get_google_language()
    if language_var.get() != current_lang:
        debug_log(f"Keyboard language changed to: {current_lang}")
        language_var.set(current_lang)

# Function to change keyboard layout
def set_keyboard_language(language_code):
    lang_map = {
        'fa-IR': '00000429',  # Persian
        'en-US': '00000409',  # English (US)
        'it-IT': '00000410',  # Italian
        'fr-FR': '0000040C',  # French
        'pt-BR': '00000416',  # Portuguese (Brazil)
        'de-DE': '00000407',  # German
        'ru-RU': '00000419',  # Russian
        'ja-JP': '00000411',  # Japanese
        'ko-KR': '00000412',  # Korean
        'zh-CN': '00000804',  # Chinese (Simplified)
        'th-TH': '0000041E',  # Thai
        'es-ES': '0000040A',  # Spanish
    }
    lang_hex = lang_map.get(language_code, '00000409')  # Default to English (US)
    try:
        win32api.LoadKeyboardLayout(lang_hex, win32con.KLF_ACTIVATE)
        debug_log(f"Keyboard layout set to: {language_code}")
    except Exception as e:
        debug_log(f"Failed to set keyboard layout: {e}")

# Function to type text using pynput
def type_text(text):
    debug_log(f"Typing text: {text}")
    for char in text:
        keyboard_controller.type(char)
    debug_log("Text typed successfully.")

# Function to process audio from the queue
def process_audio():
    selected_model = model_var.get()
    recognizer = sr.Recognizer() if selected_model == "Google" else None
    vosk_model = Model("model") if selected_model == "Vosk" else None

    while is_active:
        if not audio_queue.empty():
            audio = audio_queue.get()
            try:
                start_time = time.time()
                text = ""

                if selected_model == "Google":
                    text = recognizer.recognize_google(audio, language=language_var.get())
                elif selected_model == "Vosk":
                    with wave.open("temp.wav", "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(audio.get_wav_data())
                    rec = KaldiRecognizer(vosk_model, 16000)
                    with open("temp.wav", "rb") as wf:
                        if rec.AcceptWaveform(wf.read()):
                            text = eval(rec.Result())["text"]

                # Add result to buffer
                result_buffer.append(text)
                debug_log(f"Partial recognized text: {text}")

                # Combine buffer and type
                combined_text = " ".join(result_buffer)
                debug_log(f"Combined text: {combined_text}")
                type_text(combined_text + " ")

                # Clear buffer after typing
                result_buffer.clear()

                # Measure recognition time
                recognition_time = time.time() - start_time
                debug_log(f"Recognition time: {recognition_time:.2f} seconds")

                # Change keyboard language
                set_keyboard_language(language_var.get())

                # Measure total processing time
                total_time = time.time() - start_time
                debug_log(f"Total processing time: {total_time:.2f} seconds")

            except sr.UnknownValueError:
                debug_log("Speech Recognition could not understand the audio.")
            except sr.RequestError as e:
                debug_log(f"Google Speech Recognition request error: {e}")
            except Exception as e:
                debug_log(f"Unexpected error: {e}")

# Function to listen continuously with VAD and buffering
def listen_continuously():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        debug_log("Listening started (continuous)...")
        while is_active:
            try:
                sync_language_with_keyboard()  # Sync language with Windows keyboard
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=3)
                debug_log("Audio captured.")
                audio_queue.put(audio)
            except Exception as e:
                debug_log(f"Error during listening: {e}")

# Function to toggle activation
def toggle_activation():
    global is_active
    is_active = not is_active
    update_ui_status()
    if is_active:
        threading.Thread(target=listen_continuously, daemon=True).start()
        threading.Thread(target=process_audio, daemon=True).start()

# Function to update UI status
def update_ui_status():
    status_label.config(
        text=f"Status: {'Active' if is_active else 'Inactive'}",
        foreground="green" if is_active else "red"
    )
    mic_button.config(bg="#4caf50" if is_active else "#f44336")

# Function to quit program
def quit_program():
    global is_active
    is_active = False
    root.destroy()

# Function to show help window
def show_help():
    help_window = tk.Toplevel(root)
    help_window.title("Help")
    help_window.geometry("400x300")
    help_window.configure(bg="#f0f0f0")

    help_text = (
        "Shortcuts:\n"
        "- Press Ctrl+Alt+V to toggle voice-to-text.\n\n"
        "Language:\n"
        "- The language is automatically synchronized with the Windows keyboard layout.\n\n"
        "Models:\n"
        "- You can choose between Google and Vosk models.\n\n"
        "Usage:\n"
        "- Click the microphone icon to start/stop voice-to-text."
    )

    ttk.Label(help_window, text=help_text, background="#f0f0f0", font=("Helvetica", 10)).pack(padx=10, pady=10)

# GUI Setup
root = tk.Tk()
root.title("Voice-to-Text")
root.geometry("400x300")
root.configure(bg="#f0f0f0")

# Create modern-style UI
style = ttk.Style()
style.configure("TButton", font=("Helvetica", 10), padding=5)
style.configure("TLabel", font=("Helvetica", 12))

# Language selection
initial_language = get_google_language()
language_var = tk.StringVar(value=initial_language)  # Set initial language based on keyboard
language_label = ttk.Label(root, text="Select Language:", background="#f0f0f0")
language_label.pack(pady=10)

language_dropdown = ttk.Combobox(root, textvariable=language_var, values=list(keyboard_language_map.values()))
language_dropdown.pack(pady=5)

# Model selection
model_var = tk.StringVar(value="Google")
model_label = ttk.Label(root, text="Select Model:", background="#f0f0f0")
model_label.pack(pady=10)

model_dropdown = ttk.Combobox(root, textvariable=model_var, values=["Google", "Vosk"])
model_dropdown.pack(pady=5)

# Status label
status_label = ttk.Label(root, text="Status: Inactive", background="#f0f0f0", foreground="red")
status_label.pack(pady=20)

# Microphone button
mic_button = tk.Button(root, text="🎤", font=("Helvetica", 20), bg="#f44336", fg="white", relief="flat",
                       command=toggle_activation)
mic_button.pack(pady=10)

# Help button
help_button = ttk.Button(root, text="?", command=show_help)
help_button.pack(pady=5)

# Quit button
quit_button = ttk.Button(root, text="Quit", command=quit_program)
quit_button.pack(pady=10)

# Keyboard shortcut
def on_activate():
    toggle_activation()

keyboard_listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+v': on_activate})
keyboard_listener.start()

# Handle window close
root.protocol("WM_DELETE_WINDOW", quit_program)
root.mainloop()
