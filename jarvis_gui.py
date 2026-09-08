"""
JARVIS GUI — Desktop App with Iron Man-Inspired Interface
Uses Eel (Python + HTML/CSS/JS) for a visual frontend.
Integrates: Speech Recognition, pyttsx3 TTS, Universal Multi-LLM Brain, Windows system commands.
"""

import os
import sys
import subprocess
import threading
import time
import datetime

try:
    import psutil
except ImportError:
    print("[!] Missing 'psutil'. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

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

# Automatic installation / safe import for Eel GUI framework
try:
    import eel
except ImportError:
    print("[!] Missing required library 'eel'. Attempting automatic installation...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "eel"])
        import eel
        print("[+] 'eel' installed successfully!\n")
    except Exception as err:
        print(f"[X] Auto-install failed: {err}")
        print("[!] Please run: pip install eel (or pip install -r requirements.txt)")
        sys.exit(1)

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

for v in voices:
    if "david" in v.name.lower():
        engine.setProperty('voice', v.id)
        break
engine.setProperty('rate', 175)

voice_enabled = True
tts_lock = threading.Lock()

def speak(text):
    """Jarvis speaks out loud (thread-safe)"""
    if not text or not voice_enabled:
        return
    def _speak():
        with tts_lock:
            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
    threading.Thread(target=_speak, daemon=True).start()


# ============================================================
#  EARS — Speech Recognition
# ============================================================
def listen_once():
    """Listen to the microphone and return text. Returns None on failure."""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return None

    try:
        text = recognizer.recognize_google(audio, language='en-in')
        return text.lower().strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None


# ============================================================
#  EEL EXPOSED FUNCTIONS (called from JavaScript frontend)
# ============================================================

@eel.expose
def execute_command(text):
    """Execute any voice or text command — processed by Universal Brain Engine."""
    command = text.strip()
    if not command:
        return

    eel.setOrbState("thinking")

    full_response, spoken_summary = jarvis_engine.get_answer_and_summary(command)

    if full_response == "EXIT":
        eel.addMessage("JARVIS", "Powering down. Goodbye, sir.")
        speak("Powering down. Goodbye, sir.")
        eel.setOrbState("idle")
        time.sleep(1.5)
        os._exit(0)

    eel.setOrbState("speaking")
    eel.addMessage("JARVIS", full_response)
    speak(spoken_summary)
    
    if spoken_summary and voice_enabled:
        words = len(spoken_summary.split())
        speech_duration = max(1.5, min(8.0, words / 2.8))
        time.sleep(speech_duration)
    else:
        time.sleep(0.5)
        
    eel.setOrbState("idle")


@eel.expose
def start_listening():
    """Start microphone listening, recognize speech, and execute command."""
    eel.setOrbState("listening")
    text = listen_once()

    if text is None:
        eel.setOrbState("idle")
        eel.addMessage("JARVIS", "I didn't catch that, sir. Please try again.")
        return

    eel.addMessage("You", text)
    execute_command(text)


@eel.expose
def get_system_status():
    """Send system status & active brain info to the frontend status bar."""
    cpu = psutil.cpu_percent(interval=0.5)
    battery = psutil.sensors_battery()

    data = {"cpu": cpu}
    if battery:
        data["battery"] = round(battery.percent)
    else:
        data["battery"] = "N/A"

    data["brain"] = jarvis_engine.get_active_brain_status()
    eel.updateSystemBar(data)


@eel.expose
def set_astra_mode(mode):
    """Switch Astra Operational Mode."""
    res = jarvis_engine.set_astra_mode(mode)
    eel.addMessage("JARVIS", res)
    speak(f"Astra mode switched to {mode}")

@eel.expose
def trigger_screen_vision(query=None):
    """Trigger desktop screen vision analysis."""
    eel.setOrbState("thinking")
    eel.addMessage("You", "Analyze Screen Vision")
    res = jarvis_engine.analyze_screen(query)
    eel.setOrbState("speaking")
    eel.addMessage("JARVIS", res)
    spoken = jarvis_engine.get_spoken_summary(res)
    speak(spoken)
    time.sleep(2)
    eel.setOrbState("idle")

@eel.expose
def toggle_voice(enabled):
    """Enable or disable voice output."""
    global voice_enabled
    voice_enabled = enabled
    status = "enabled" if enabled else "disabled"
    eel.addMessage("JARVIS", f"Voice output {status}, sir.")


auto_listen = False

@eel.expose
def toggle_autolisten(enabled):
    """Enable or disable auto-listen mode."""
    global auto_listen
    auto_listen = enabled
    status = "enabled" if enabled else "disabled"
    eel.addMessage("JARVIS", f"Auto-listen mode {status}, sir.")
    if enabled:
        threading.Thread(target=auto_listen_loop, daemon=True).start()


def auto_listen_loop():
    """Continuously listen when auto-listen is enabled."""
    while auto_listen:
        try:
            start_listening()
            time.sleep(0.5)
        except Exception:
            time.sleep(1)


# ============================================================
#  SYSTEM STATUS UPDATER (runs in background)
# ============================================================
def status_updater():
    """Periodically update system stats on the frontend."""
    while True:
        try:
            get_system_status()
        except Exception:
            pass
        time.sleep(5)


# ============================================================
#  MAIN — Launch the Eel app
# ============================================================
def main():
    print("=" * 60)
    print("[*] JARVIS GUI - Starting Desktop App")
    print(f"[*] Brain Status: {jarvis_engine.get_active_brain_status()}")
    print("=" * 60)

    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
    eel.init(web_dir)

    threading.Thread(target=status_updater, daemon=True).start()

    print("[>] Launching JARVIS interface...")
    print("[i] Close the browser window or say 'exit' to quit.\n")

    modes_to_try = [
        {'mode': 'edge', 'size': (1280, 800), 'position': (100, 50)},
        {'mode': 'chrome', 'size': (1280, 800), 'position': (100, 50)},
        {'mode': None, 'app_mode': False}
    ]

    launched = False
    for opts in modes_to_try:
        for port in [8147, 8148, 0]:
            try:
                eel.start(
                    'index.html',
                    port=port,
                    host='localhost',
                    disable_cache=True,
                    **opts
                )
                launched = True
                break
            except (EnvironmentError, OSError):
                continue
        if launched:
            break


if __name__ == "__main__":
    main()
    