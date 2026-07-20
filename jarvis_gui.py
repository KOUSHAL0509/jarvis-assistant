"""
JARVIS GUI — Desktop App with Iron Man-Inspired Interface
Uses Eel (Python + HTML/CSS/JS) for a stunning visual frontend.
Integrates: Speech Recognition, pyttsx3 TTS, OpenAI GPT, Windows system commands.
"""

import eel
import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import webbrowser
import os
import subprocess
import psutil
import threading
import time

# --- Optional: OpenAI Brain ---
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[!] OpenAI not installed. GPT brain disabled. Install with: pip install openai python-dotenv")


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
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
    threading.Thread(target=_speak, daemon=True).start()


# ============================================================
#  BRAIN — OpenAI GPT Integration with Conversation Memory
# ============================================================
conversation_history = []
openai_client = None

def get_openai_client():
    global openai_client
    if openai_client is None and HAS_OPENAI:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key.strip() and not api_key.startswith("your_"):
            openai_client = OpenAI(api_key=api_key.strip())
    return openai_client

def ask_gpt(query):
    """Send a query to OpenAI GPT and get a Jarvis-style response"""
    global conversation_history
    client = get_openai_client()
    if not client:
        return "My AI brain is offline, sir. Please add your OpenAI API key to the .env file."

    messages = [
        {"role": "system", "content": "You are JARVIS, Tony Stark's AI assistant from Iron Man. You are witty, intelligent, and speak concisely in 1-2 sentences max. Address the user as 'sir'."}
    ]
    messages.extend(conversation_history[-6:])
    messages.append({"role": "user", "content": query})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        result = response.choices[0].message.content.strip()
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": result})
        return result
    except Exception as e:
        return f"I encountered an error connecting to my brain, sir. {str(e)[:60]}"


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
#  ACTIONS — Windows System Commands
# ============================================================
def execute_action(command):
    """
    Try to match the command to a hardcoded action.
    Returns a response string if matched, or None if no match.
    """
    # --- Web & Apps ---
    if 'open youtube' in command or command == 'youtube':
        webbrowser.open('https://www.youtube.com')
        return "Opening YouTube, sir."

    if 'open google' in command or command == 'google':
        webbrowser.open('https://www.google.com')
        return "Opening Google, sir."

    if 'open github' in command or command == 'github':
        webbrowser.open('https://www.github.com')
        return "Opening GitHub, sir."

    if 'open chatgpt' in command or 'chat gpt' in command:
        webbrowser.open('https://chat.openai.com')
        return "Opening ChatGPT, sir."

    if command.startswith('search ') or command.startswith('google '):
        query = command.replace('search', '').replace('google', '').replace('for', '').strip()
        if query:
            webbrowser.open(f'https://www.google.com/search?q={query.replace(" ", "+")}')
            return f"Searching Google for {query}, sir."

    # --- Windows Apps ---
    if 'open notepad' in command:
        subprocess.Popen('notepad.exe')
        return "Opening Notepad, sir."

    if 'open calculator' in command or 'calculator' == command:
        subprocess.Popen('calc.exe')
        return "Opening Calculator, sir."

    if 'open chrome' in command or command == 'chrome':
        try:
            os.startfile(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
            return "Opening Google Chrome, sir."
        except Exception:
            webbrowser.open('https://www.google.com')
            return "Chrome not found at default path. Opened Google instead, sir."

    if any(kw in command for kw in ['open vs code', 'visual studio code', 'code editor']):
        try:
            subprocess.Popen('code', shell=True)
            return "Opening Visual Studio Code, sir."
        except Exception:
            return "Failed to open VS Code. Please check if it's installed, sir."

    if 'open file explorer' in command or 'open explorer' in command or 'open folder' in command:
        subprocess.Popen('explorer.exe')
        return "Opening File Explorer, sir."

    if 'open terminal' in command or 'open command prompt' in command:
        subprocess.Popen('cmd.exe')
        return "Opening Command Prompt, sir."

    # --- Screenshot ---
    if any(kw in command for kw in ['take screenshot', 'screenshot', 'capture screen']):
        try:
            import pyautogui
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{timestamp}.png")
            pyautogui.screenshot(path)
            return f"Screenshot saved to your Desktop, sir."
        except ImportError:
            return "Screenshot requires pyautogui. Install with: pip install pyautogui"
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    # --- Date & Time ---
    if any(kw in command for kw in ['what time', 'the time', 'current time', 'tell me the time']):
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}, sir."

    if any(kw in command for kw in ['what date', 'the date', "today's date", 'todays date', 'what day']):
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}, sir."

    # --- System Status ---
    if any(kw in command for kw in ['system status', 'battery', 'cpu', 'system report', 'how is the system']):
        battery = psutil.sensors_battery()
        cpu = psutil.cpu_percent(interval=0.5)
        if battery:
            plugged = "plugged in" if battery.power_plugged else "on battery power"
            return f"System is operating at {cpu} percent CPU. Battery is at {battery.percent} percent, currently {plugged}."
        else:
            return f"System is operating at {cpu} percent CPU capacity, sir."

    # --- Wikipedia ---
    if 'wikipedia' in command:
        query = command.replace('wikipedia', '').replace('jarvis', '').strip()
        if query:
            try:
                results = wikipedia.summary(query, sentences=2)
                return f"According to Wikipedia: {results}"
            except Exception:
                return "I couldn't find anything about that on Wikipedia, sir."
        return "What would you like me to search on Wikipedia, sir?"

    # --- Jarvis Identity ---
    if any(kw in command for kw in ['who are you', 'what are you', 'introduce yourself']):
        return "I am Jarvis, your personal AI assistant. Modeled after Tony Stark's companion system. I am here to serve, sir."

    if any(kw in command for kw in ['how are you', "how's it going", "how do you do"]):
        return "All systems are operating at peak efficiency, sir. Thank you for asking."

    # --- Clear Memory ---
    if any(kw in command for kw in ['clear history', 'forget everything', 'reset memory']):
        global conversation_history
        conversation_history = []
        return "Conversation history cleared, sir. Fresh start."

    # --- Exit ---
    if any(kw in command for kw in ['goodbye', 'exit', 'quit', 'stop', 'power down', 'shut down jarvis', 'sleep']):
        return "EXIT"

    # No match
    return None


# ============================================================
#  EEL EXPOSED FUNCTIONS (called from JavaScript frontend)
# ============================================================

@eel.expose
def execute_command(text):
    """Execute a text command — try action matching first, then GPT fallback."""
    command = text.lower().strip()
    if not command:
        return

    # Try hardcoded actions first
    result = execute_action(command)

    if result == "EXIT":
        eel.addMessage("JARVIS", "Powering down. Goodbye, sir.")
        speak("Powering down. Goodbye, sir.")
        eel.setOrbState("idle")
        time.sleep(2)
        os._exit(0)
    elif result:
        eel.setOrbState("speaking")
        eel.addMessage("JARVIS", result)
        speak(result)
        time.sleep(0.5)
        eel.setOrbState("idle")
    else:
        # Fall back to GPT
        eel.setOrbState("thinking")
        eel.addMessage("JARVIS", "Processing, sir...")
        gpt_response = ask_gpt(command)
        # Remove the "Processing" message by adding the real response
        eel.setOrbState("speaking")
        eel.addMessage("JARVIS", gpt_response)
        speak(gpt_response)
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
    """Send system status to the frontend status bar."""
    cpu = psutil.cpu_percent(interval=0.5)
    battery = psutil.sensors_battery()

    data = {"cpu": cpu}
    if battery:
        data["battery"] = round(battery.percent)
    else:
        data["battery"] = "N/A"

    # Check brain status
    client = get_openai_client()
    if client:
        data["brain"] = "GPT-4o Online"
    else:
        data["brain"] = "Offline"

    eel.updateSystemBar(data)


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
    print("=" * 60)

    # Initialize Eel with the web folder
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
    eel.init(web_dir)

    # Start background status updater
    threading.Thread(target=status_updater, daemon=True).start()

    print("[>] Launching JARVIS interface...")
    print("[i] Close the browser window or say 'exit' to quit.\n")

    # Try Edge first (more likely on Windows), then Chrome, then default
    try:
        eel.start(
            'index.html',
            size=(1280, 800),
            position=(100, 50),
            mode='edge',
            port=8147,
            host='localhost',
            disable_cache=True
        )
    except EnvironmentError:
        try:
            eel.start(
                'index.html',
                size=(1280, 800),
                position=(100, 50),
                mode='chrome',
                port=8147,
                host='localhost',
                disable_cache=True
            )
        except EnvironmentError:
            print("[!] Edge/Chrome not found. Opening in default browser...")
            eel.start(
                'index.html',
                size=(1280, 800),
                port=8147,
                host='localhost',
                mode=None,
                app_mode=False,
                disable_cache=True
            )


if __name__ == "__main__":
    main()
