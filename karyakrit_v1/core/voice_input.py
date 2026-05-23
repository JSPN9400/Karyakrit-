"""
Lightweight voice input helper using SpeechRecognition (microphone) if available.
This keeps the implementation small; if `pyaudio` is not installed you'll get an informative error.

Usage:
    from core.voice_input import listen_from_mic
    text = listen_from_mic(timeout=5)

Notes:
- On Windows you may need to install PyAudio wheels or use `pipwin install pyaudio`.
- This module intentionally keeps behavior simple and optional.
"""

import time


def listen_from_mic(timeout: int = 5) -> str:
    """Listen from the default microphone for `timeout` seconds and return transcribed text.

    Uses `speech_recognition` with the default Google recognizer as a fallback. This requires
    internet for the Google API. If you need fully offline transcription, integrate whisper separately.
    """
    try:
        import speech_recognition as sr
    except Exception as e:
        raise RuntimeError('speech_recognition is required for microphone input: ' + str(e))

    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print(f"Listening for {timeout} seconds...")
        audio = r.record(source, duration=timeout)

    try:
        print("Transcribing (using Google Speech Recognition)...")
        text = r.recognize_google(audio)
        return text
    except sr.RequestError as e:
        raise RuntimeError('API unavailable or unresponsive: ' + str(e))
    except sr.UnknownValueError:
        return ''
 