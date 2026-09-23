"""
JARVIS - AI Voice Assistant for Windows
Ported to Windows with pyttsx3 TTS, Google Speech Recognition, and Universal Multi-LLM Brain.
"""

import os
import sys
import subprocess
import datetime
try:
    import pywintypes
    import pythoncom
except ImportError:
    if sys.platform == 'win32':
        print("[!] Missing 'pywin32' (pywintypes / pythoncom). Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
            import pywintypes
            import pythoncom
        except Exception:
            pass

try:
    import speech_recognition as sr
except ImportError:
    print("[!] Missing 'SpeechRecognition'. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "SpeechRecognition"])
    import speech_recognition as sr

try:
    import pyttsx3
except ImportError:
    print("[!] Missing 'pyttsx3'. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyttsx3"])
    import pyttsx3

# Import Universal Processing Engine
import jarvis_engine


# ============================================================
#  MOUTH — Text-to-Speech (pyttsx3 for Windows)
# ============================================================
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')

def init_voice_settings():
    v_config = jarvis_engine.get_voice_settings()
    target_id = v_config.get("voice_id")
    target_rate = v_config.get("voice_rate", 175)
    try:
        engine.setProperty('rate', target_rate)
    except Exception:
        pass
    applied_voice = None
    if target_id:
        for v in voices:
            if v.id == target_id:
                engine.setProperty('voice', v.id)
                applied_voice = v
                break
    if not applied_voice:
        for v in voices:
            if "david" in v.name.lower():
                engine.setProperty('voice', v.id)
                applied_voice = v
                break
        if not applied_voice and voices:
            engine.setProperty('voice', voices[0].id)

init_voice_settings()

def speak(text):
    """Jarvis speaks out loud"""
    if not text:
        return
    print(f"🗣️  Jarvis (Speaking): {text}")
    try:
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[!] TTS Error: {e}")


# ============================================================
#  EARS — Speech Recognition (Google API with retry + timeout)
# ============================================================
def listen():
    """Listen to the microphone and return text. Returns None on failure."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    with sr.Microphone() as source:
        print("\n🎤 Listening...", flush=True)
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return None

    try:
        print("🧠 Recognizing...", flush=True)
        text = recognizer.recognize_google(audio, language='en-in')
        text = text.lower().strip()
        print(f"✅ You said: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"❌ Google API error: {e}")
        return None


# ============================================================
#  MAIN LOOP — Always listening, no wake word needed
# ============================================================
def greet():
    """Greet the user based on time of day"""
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good morning!")
    elif hour < 18:
        speak("Good afternoon!")
    else:
        speak("Good evening!")
    speak("Jarvis online! How can I help you today?")

def main():
    active_brain = jarvis_engine.get_active_brain_status()
    print("=" * 60)
    print("🔵 JARVIS SYSTEM ONLINE")
    print("=" * 60)
    print(f"🧠 Brain:   {active_brain}")
    print("🗣️  Voice:   pyttsx3 (Windows SAPI5)")
    print("🎤 Ears:    Google Speech Recognition")
    print("⚡ Actions: Windows System Commands + Universal Query Engine")
    print("=" * 60)
    print("\n💡 Speak naturally or ask ANYTHING. Say 'exit' or 'goodbye' to quit.\n")

    greet()

    while True:
        command = listen()

        if command is None:
            continue

        full_response, spoken_summary = jarvis_engine.get_answer_and_summary(command)

        if full_response == "EXIT":
            speak("Powering down. Goodbye, my friend!")
            break

        # Display full ChatGPT response in console
        print(f"\n🤖 JARVIS:\n{full_response}\n")

        # Speak concise summary
        speak(spoken_summary)

if __name__ == "__main__":
    main()
