"""
JARVIS - AI Voice Assistant for Windows
Inspired by prudhviraj0310/jarvis-learning-server
Ported to Windows with pyttsx3 TTS, Google Speech Recognition, and OpenAI Brain.
"""

import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import webbrowser
import os
import subprocess
import psutil
import json
import time

# --- Optional: OpenAI Brain ---
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("⚠️  OpenAI not installed. GPT brain disabled. Install with: pip install openai python-dotenv")


# ============================================================
#  MOUTH — Text-to-Speech (pyttsx3 for Windows)
# ============================================================
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')

# Try to set a male "David" voice for Jarvis feel
for v in voices:
    if "david" in v.name.lower():
        engine.setProperty('voice', v.id)
        break
engine.setProperty('rate', 175)

def speak(text):
    """Jarvis speaks out loud"""
    if not text:
        return
    print(f"🗣️  Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()


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
        return "My AI brain is offline, sir. Please add your OpenAI API key to the .env file on your Desktop."

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

    # Try Google Speech Recognition (online, fast)
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
#  ACTIONS — Windows System Commands (ported from macOS repo)
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

    # --- Screenshot (requires pyautogui) ---
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
#  MAIN LOOP — Always listening, no wake word needed
# ============================================================
def greet():
    """Greet the user based on time of day"""
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good Morning, sir!")
    elif hour < 18:
        speak("Good Afternoon, sir!")
    else:
        speak("Good Evening, sir!")
    speak("Jarvis online. All systems operational. How may I assist you?")

def main():
    print("=" * 60)
    print("🔵 JARVIS SYSTEM ONLINE")
    print("=" * 60)
    print("🧠 Brain:   " + ("GPT-4o-mini Ready" if HAS_OPENAI and os.getenv('OPENAI_API_KEY') else "Offline (no API key)"))
    print("🗣️  Voice:   pyttsx3 (Windows SAPI5)")
    print("🎤 Ears:    Google Speech Recognition")
    print("⚡ Actions: Windows System Commands")
    print("=" * 60)
    print("\n💡 Just speak naturally. Say 'exit' or 'goodbye' to quit.\n")

    greet()

    while True:
        command = listen()

        if command is None:
            continue

        # 1. Try hardcoded actions first
        result = execute_action(command)

        if result == "EXIT":
            speak("Powering down. Goodbye, sir.")
            break
        elif result:
            speak(result)
        else:
            # 2. Fall back to OpenAI Brain for anything else
            speak("Processing, sir...")
            gpt_response = ask_gpt(command)
            speak(gpt_response)

if __name__ == "__main__":
    main()
