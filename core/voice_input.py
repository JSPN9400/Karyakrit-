"""
Lightweight voice input helper using SpeechRecognition (microphone) if available.

This is optional functionality. The core app works without it. To enable
the `voice` command, install the extra dependencies:

    pip install -r requirements-voice.txt

On Windows you may also need PyAudio wheels (`pipwin install pyaudio`) if
the plain pip install fails to build.

Usage:
    from core.voice_input import listen_from_mic
    text = listen_from_mic(timeout=5)
"""


def listen_from_mic(timeout: int = 5) -> str:
    """Listen from the default microphone for `timeout` seconds and return transcribed text.

    Uses `speech_recognition` with the default Google recognizer as a fallback. This requires
    internet for the Google API. If you need fully offline transcription, integrate whisper separately.

    Raises:
        RuntimeError: If the optional voice dependencies are not installed, or if no
            microphone is available, with a message describing how to fix it.
    """
    try:
        import speech_recognition as sr
    except ImportError:
        raise RuntimeError(
            "Voice input requires extra packages that aren't installed. "
            "Run: pip install -r requirements-voice.txt "
            "(on Windows, if PyAudio fails to build, try: pipwin install pyaudio)"
        )

    try:
        r = sr.Recognizer()
        mic = sr.Microphone()
    except OSError as e:
        raise RuntimeError(f"No microphone available: {e}")

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print(f"Listening for {timeout} seconds...")
        audio = r.record(source, duration=timeout)

    try:
        print("Transcribing (using Google Speech Recognition)...")
        text = r.recognize_google(audio)
        return text
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition API unavailable or unresponsive: {e}")
    except sr.UnknownValueError:
        return ''
