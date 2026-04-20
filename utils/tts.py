"""Text-to-speech helpers."""

import threading

import pyttsx3

from config import settings


def _speak_text_blocking(text: str):
    if not text or not settings.USE_TTS:
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", settings.TTS_RATE)
        engine.setProperty("volume", settings.TTS_VOLUME)
        if settings.TTS_VOICE_INDEX is not None:
            voices = engine.getProperty("voices")
            if 0 <= settings.TTS_VOICE_INDEX < len(voices):
                engine.setProperty("voice", voices[settings.TTS_VOICE_INDEX].id)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[TTS error] {e}")


def speak_async(text: str):
    if not settings.USE_TTS or not text:
        return
    t = threading.Thread(target=_speak_text_blocking, args=(text,), daemon=True)
    t.start()
