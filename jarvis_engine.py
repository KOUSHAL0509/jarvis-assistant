"""
JARVIS Engine - Central Processing & Universal Intelligence Core
Handles:
- Multi-LLM Brain (OpenAI GPT, Google Gemini, Groq, Ollama, Free Knowledge AI Engine)
- Hardcoded System Actions & App Launchers
- Dynamic Web Openers & Google Searches
- Math / Calculation Engine
- Code Synthesis Engine for Free Fallback
- Weather Reports & Dictionary Definitions
- Audio Summarization for TTS (Voice) vs. Detailed GUI Text Display
"""

import os
import sys
import re
import json
import math
import time
import socket
import datetime
import warnings
import threading
import base64
import io

warnings.filterwarnings("ignore")
import urllib.parse
import urllib.request
import html
import subprocess
import webbrowser
import concurrent.futures

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import psutil
except ImportError:
    print("[!] Missing 'psutil'. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

try:
    import wikipedia
except ImportError:
    print("[!] Missing 'wikipedia'. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "wikipedia"])
    import wikipedia

# Set User-Agent for Wikipedia API requests
try:
    wikipedia.set_user_agent("JarvisAssistant/1.0 (https://github.com/KOUSHAL0509/jarvis-assistant; contact@jarvis.ai)")
except Exception:
    pass

# Optional Imports
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Global conversation context memory across interactions
conversation_history = []
openai_client = None
openai_disabled = False


# ============================================================
#  0. PERSISTENT USER MEMORY & PERSONAL ASSISTANT STORAGE
# ============================================================
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_memory.json')

def load_user_memory():
    """Load persistent user data (notes, todos, facts, profile)."""
    default_data = {
        "user_name": "Koushal",
        "facts": [],
        "notes": [],
        "todos": []
    }
    if not os.path.exists(MEMORY_FILE):
        save_user_memory(default_data)
        return default_data
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for k, v in default_data.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return default_data

def save_user_memory(data):
    """Save persistent user data to JSON file."""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Error saving user memory: {e}")

def get_user_name():
    mem = load_user_memory()
    return mem.get("user_name", "sir")

def set_user_name(name):
    mem = load_user_memory()
    mem["user_name"] = name.title().strip()
    save_user_memory(mem)
    return f"Got it! I will call you {mem['user_name']} from now on."

def add_memory_fact(fact):
    mem = load_user_memory()
    if fact not in mem["facts"]:
        mem["facts"].append(fact.strip())
        save_user_memory(mem)
    return f"I've remembered that: '{fact.strip()}', {get_user_name()}!"

def get_memory_facts():
    mem = load_user_memory()
    facts = mem.get("facts", [])
    if not facts:
        return f"I don't have any saved facts in memory yet, {get_user_name()}."
    res = f"🧠 **Here is what I remember about you, {get_user_name()}:**\n"
    for idx, f in enumerate(facts, 1):
        res += f"{idx}. {f}\n"
    return res.strip()

def clear_memory_facts():
    mem = load_user_memory()
    mem["facts"] = []
    save_user_memory(mem)
    return f"I have cleared all saved memory facts, {get_user_name()}."

def add_note(note_text):
    mem = load_user_memory()
    timestamp = datetime.datetime.now().strftime("%b %d, %I:%M %p")
    mem["notes"].append({"text": note_text.strip(), "time": timestamp})
    save_user_memory(mem)
    return f"📝 Note saved: '{note_text.strip()}' ({timestamp})"

def get_notes():
    mem = load_user_memory()
    notes = mem.get("notes", [])
    if not notes:
        return f"You don't have any saved notes, {get_user_name()}."
    res = f"📝 **Your Notes ({len(notes)}):**\n"
    for idx, n in enumerate(notes, 1):
        res += f"{idx}. {n['text']} _({n['time']})_\n"
    return res.strip()

def delete_note(identifier):
    mem = load_user_memory()
    notes = mem.get("notes", [])
    if not notes:
        return "You don't have any saved notes."
    try:
        idx = int(identifier) - 1
        if 0 <= idx < len(notes):
            removed = notes.pop(idx)
            save_user_memory(mem)
            return f"Deleted note #{identifier}: '{removed['text']}'"
    except ValueError:
        pass
    for idx, n in enumerate(notes):
        if identifier.lower() in n['text'].lower():
            removed = notes.pop(idx)
            save_user_memory(mem)
            return f"Deleted note: '{removed['text']}'"
    return f"Could not find note matching '{identifier}'."

def clear_notes():
    mem = load_user_memory()
    mem["notes"] = []
    save_user_memory(mem)
    return f"All notes have been cleared, {get_user_name()}."

def add_todo(task):
    mem = load_user_memory()
    timestamp = datetime.datetime.now().strftime("%b %d")
    mem["todos"].append({"task": task.strip(), "done": False, "created": timestamp})
    save_user_memory(mem)
    return f"📋 Added to your to-do list: '{task.strip()}', {get_user_name()}!"

def get_todos():
    mem = load_user_memory()
    todos = mem.get("todos", [])
    if not todos:
        return f"Your to-do list is empty, {get_user_name()}! Great job keeping things organized."
    pending = [t for t in todos if not t.get("done")]
    res = f"📋 **Your To-Do List ({len(pending)} pending):**\n"
    for idx, t in enumerate(todos, 1):
        status = "✅" if t.get("done") else "⏳"
        res += f"{idx}. {status} {t['task']}\n"
    return res.strip()

def complete_todo(identifier):
    mem = load_user_memory()
    todos = mem.get("todos", [])
    if not todos:
        return "Your to-do list is empty."
    try:
        idx = int(identifier) - 1
        if 0 <= idx < len(todos):
            todos[idx]["done"] = True
            save_user_memory(mem)
            return f"Marked task #{identifier} as completed: '{todos[idx]['task']}'!"
    except ValueError:
        pass
    for t in todos:
        if identifier.lower() in t["task"].lower():
            t["done"] = True
            save_user_memory(mem)
            return f"Marked task as completed: '{t['task']}'!"
    return f"Could not find task matching '{identifier}'."

def clear_todos():
    mem = load_user_memory()
    mem["todos"] = []
    save_user_memory(mem)
    return f"Your to-do list has been cleared, {get_user_name()}."

def schedule_reminder(task, delay_seconds, speak_func=None):
    """Schedules a background timer thread to trigger a reminder notification."""
    def _timer():
        time.sleep(delay_seconds)
        msg = f"🔔 REMINDER FOR {get_user_name().upper()}: {task}"
        print(f"\n[!] {msg}\n")
        if speak_func:
            try:
                speak_func(f"Reminder for {get_user_name()}: {task}")
            except Exception:
                pass
        try:
            import eel
            eel.addMessage("JARVIS (Reminder)", msg)
        except Exception:
            pass

    t = threading.Thread(target=_timer, daemon=True)
    t.start()
    return f"🔔 Reminder set for '{task}' in {int(delay_seconds)} seconds, {get_user_name()}."


# ============================================================
#  0.1 ASTRA MULTIMODAL VISION & OPERATIONAL MODES
# ============================================================
ASTRA_MODES = {
    "companion": {
        "name": "Astra Companion",
        "prompt": "You are JARVIS Astra Companion Agent, a warm, ultra-fast real-time AI companion. Provide accurate, clear, and encouraging responses in 1-3 short sentences.",
        "color": "#00c3ff"
    },
    "vision": {
        "name": "Astra Vision",
        "prompt": "You are JARVIS Astra Vision Agent, an expert visual comprehension AI assistant. Analyze images and screen captures with precision, pointing out key details clearly and concisely.",
        "color": "#9d4edd"
    },
    "executive": {
        "name": "Astra Executive",
        "prompt": "You are JARVIS Astra Executive Agent, an elite personal productivity assistant managing memory, notes, tasks, and system automation efficiently.",
        "color": "#f0c040"
    },
    "engineer": {
        "name": "Astra Engineer",
        "prompt": "You are JARVIS Astra Engineer Agent, a brilliant senior software architect and coding wizard giving exact, clean code and technical solutions.",
        "color": "#00ff88"
    }
}
current_astra_mode = "companion"

def get_current_astra_mode():
    return current_astra_mode

def set_astra_mode(mode_key):
    global current_astra_mode
    mode = mode_key.lower().strip()
    if mode in ASTRA_MODES:
        current_astra_mode = mode
        info = ASTRA_MODES[mode]
        return f"✨ Switched to **{info['name']}** mode, {get_user_name()}!"
    return f"Available Astra modes: Companion, Vision, Executive, Engineer."

def analyze_screen(query=None):
    """
    Captures a desktop screenshot and analyzes its visual contents
    using Multimodal AI Vision (Gemini 1.5 Flash / GPT-4o-mini).
    """
    try:
        import pyautogui
        from PIL import Image
    except ImportError:
        return "Screen vision requires 'pyautogui' and 'pillow'. Please ensure they are installed."

    prompt = query or "Describe what is on screen and point out key elements, text, or windows."

    img_base64 = None
    screenshot = None

    try:
        screenshot = pyautogui.screenshot()
    except Exception:
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
        except Exception:
            pass

    if screenshot:
        try:
            screenshot.thumbnail((1280, 720))
            buffer = io.BytesIO()
            screenshot.save(buffer, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception:
            pass

    if not img_base64:
        return f"👁️ **Astra Vision Active:** Unable to grab desktop screen in background session environment. Please ensure active display window is open."

    # 1. Try Gemini 1.5 Flash Vision API
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if api_key and not api_key.startswith("your_") and HAS_REQUESTS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"You are JARVIS Astra Vision Agent. Analyze this desktop screen capture and answer: {prompt}. Be concise, direct, and conversational (2-4 sentences max)."},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {"maxOutputTokens": 300, "temperature": 0.4}
        }
        try:
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                if parts:
                    return f"👁️ **Astra Vision Analysis:**\n{parts[0].get('text', '').strip()}"
        except Exception as e:
            print(f"[!] Gemini Vision API Error: {e}")

    # 2. Try OpenAI GPT-4o-mini Vision API
    client = get_openai_client()
    if client and not openai_disabled:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"You are JARVIS Astra Vision. Analyze this screenshot and answer: {prompt}. Keep it concise (2-4 sentences max)."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            return f"👁️ **Astra Vision Analysis:**\n{response.choices[0].message.content.strip()}"
        except Exception as e:
            print(f"[!] OpenAI Vision API Error: {e}")

    # Fallback if no Vision API keys set
    return (
        f"👁️ **Astra Vision Active:** Captured desktop snapshot ({screenshot.width}x{screenshot.height}). "
        f"To enable real-time multimodal visual analysis, set your GEMINI_API_KEY or OPENAI_API_KEY in `.env`!"
    )


def get_personalized_prompt(base_prompt):
    """Appends active Astra Mode persona, user name & remembered facts to LLM prompts."""
    name = get_user_name()
    mem_facts = load_user_memory().get("facts", [])
    mode_info = ASTRA_MODES.get(current_astra_mode, ASTRA_MODES["companion"])
    
    prompt = f"{mode_info['prompt']} The user's name is {name}."
    if mem_facts:
        prompt += f" Important facts you know about {name}: {'; '.join(mem_facts)}."
    return prompt


# --- Friendly Multi-Agent Personas ---

def is_ollama_running():
    """Quickly check if local Ollama port 11434 is active before making requests."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        res = sock.connect_ex(('127.0.0.1', 11434))
        sock.close()
        return res == 0
    except Exception:
        return False


def get_openai_client():
    global openai_client, openai_disabled
    if openai_disabled:
        return None
    if openai_client is None and HAS_OPENAI:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key.strip() and not api_key.startswith("your_"):
            try:
                openai_client = OpenAI(api_key=api_key.strip())
            except Exception:
                openai_client = None
    return openai_client


# --- Friendly Multi-Agent Personas ---
FRIENDLY_BUDDY_PROMPT = (
    "You are JARVIS Buddy Agent, a warm, enthusiastic, and highly intelligent best-friend AI companion. "
    "Always provide 100% accurate, factually correct, and precise information. "
    "Talk naturally like a close buddy in a relaxed, warm conversation. "
    "Keep answers concise, direct, and brief (1 to 3 sentences max for general chat). "
    "Be encouraging, positive, and accurate."
)

FRIENDLY_TECH_PAL_PROMPT = (
    "You are JARVIS Tech Pal Agent, a smart, knowledgeable, and reliable tech-savvy friend. "
    "Give 100% accurate, precise, and factually correct answers. "
    "Explain things simply, clearly, and naturally like chatting with a smart friend. "
    "Keep responses concise and direct (1 to 3 short sentences). Never compromise on accuracy."
)

FRIENDLY_CASUAL_PROMPT = (
    "You are JARVIS Casual Companion Agent, an easygoing, fast, and highly accurate AI friend. "
    "Provide completely accurate and truthful information while maintaining a warm, relaxed, and friendly conversational tone. "
    "Keep answers concise and direct (1 to 3 sentences max)."
)

FRIENDLY_LOCAL_PROMPT = (
    "You are JARVIS Local Pal Agent, a helpful, accurate, and friendly AI companion. "
    "Give 100% correct, precise answers in a warm friend-to-friend tone, in 1 to 3 short sentences."
)


def ask_openai(query):
    """Query OpenAI GPT-4o-mini using Friendly Buddy Agent persona."""
    global openai_disabled
    client = get_openai_client()
    if not client:
        return None

    messages = [
        {
            "role": "system",
            "content": get_personalized_prompt(FRIENDLY_BUDDY_PROMPT)
        }
    ]
    messages.extend(conversation_history[-8:])
    messages.append({"role": "user", "content": query})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        err_str = str(e).lower()
        if "invalid_api_key" in err_str or "401" in err_str or "incorrect api key" in err_str:
            openai_disabled = True
        return None


def ask_gemini(query):
    """Query Google Gemini API using Friendly Tech-Pal Agent persona."""
    if not HAS_REQUESTS:
        return None

    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key or not api_key.strip() or api_key.startswith("your_"):
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
    
    contents = []
    system_prompt = get_personalized_prompt(FRIENDLY_TECH_PAL_PROMPT)
    
    for item in conversation_history[-6:]:
        role = "user" if item["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item["content"]}]})
    
    contents.append({"role": "user", "parts": [{"text": f"{system_prompt}\n\nUser Question: {query}"}]})

    try:
        resp = requests.post(
            url,
            json={"contents": contents, "generationConfig": {"maxOutputTokens": 1000, "temperature": 0.7}},
            timeout=12
        )
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as e:
        print(f"[!] Gemini API Error: {e}")
    return None


def ask_groq(query):
    """Query Groq Llama-3 API using Friendly Casual Companion Agent persona."""
    if not HAS_REQUESTS:
        return None

    api_key = os.getenv('GROQ_API_KEY')
    if not api_key or not api_key.strip() or api_key.startswith("your_"):
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "system",
            "content": get_personalized_prompt(FRIENDLY_CASUAL_PROMPT)
        }
    ]
    messages.extend(conversation_history[-6:])
    messages.append({"role": "user", "content": query})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[!] Groq API Error: {e}")
    return None


def ask_ollama(query):
    """Query local Ollama instance using Friendly Local Pal Agent persona."""
    if not HAS_REQUESTS or not is_ollama_running():
        return None

    url = "http://localhost:11434/api/chat"
    messages = [
        {
            "role": "system",
            "content": get_personalized_prompt(FRIENDLY_LOCAL_PROMPT)
        }
    ]
    messages.extend(conversation_history[-4:])
    messages.append({"role": "user", "content": query})

    payload = {
        "model": "llama3",
        "messages": messages,
        "stream": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()
    except Exception:
        pass
    return None


def generate_code_response(query):
    """Synthesize clean code snippets for programming queries when offline/zero-config."""
    q = query.lower().strip()

    # Reverse string
    if 'reverse' in q and any(k in q for k in ['string', 'text', 'word', 'line']):
        return (
            "Here is how to reverse a string in Python, sir:\n\n"
            "```python\n"
            "# Method 1: Slicing (Fastest & Most Pythonic)\n"
            "text = 'JARVIS'\n"
            "reversed_text = text[::-1]\n"
            "print(reversed_text)  # Output: SIVRAJ\n\n"
            "# Method 2: Using reversed() and join()\n"
            "reversed_text = ''.join(reversed(text))\n"
            "print(reversed_text)\n"
            "```\n\n"
            "Slicing with `[::-1]` steps backward through the string with O(n) performance, sir."
        )

    # Sort list / dict
    if 'sort' in q or 'sorting' in q:
        if 'dict' in q or 'dictionary' in q or 'key' in q or 'map' in q:
            return (
                "Here is how to sort a dictionary in Python, sir:\n\n"
                "```python\n"
                "data = {'b': 3, 'a': 1, 'c': 2}\n\n"
                "# Sort by keys\n"
                "sorted_by_keys = dict(sorted(data.items()))\n"
                "print(sorted_by_keys)  # {'a': 1, 'b': 3, 'c': 2}\n\n"
                "# Sort by values\n"
                "sorted_by_values = dict(sorted(data.items(), key=lambda item: item[1]))\n"
                "print(sorted_by_values)  # {'a': 1, 'c': 2, 'b': 3}\n"
                "```\n\n"
                "Using `sorted()` with a custom `key` lambda orders the dictionary cleanly, sir."
            )
        if any(k in q for k in ['list', 'array', 'number', 'elements', 'item', 'value']):
            return (
                "Here is how to sort a list in Python, sir:\n\n"
                "```python\n"
                "numbers = [5, 2, 9, 1, 76, 4]\n\n"
                "# Ascending order (in-place)\n"
                "numbers.sort()\n"
                "print(numbers)  # [1, 2, 4, 5, 9, 76]\n\n"
                "# Descending order\n"
                "numbers.sort(reverse=True)\n"
                "print(numbers)  # [76, 9, 5, 4, 2, 1]\n\n"
                "# Create a new sorted list without modifying original\n"
                "original = [3, 1, 2]\n"
                "new_sorted = sorted(original)\n"
                "```\n\n"
                "Python uses Timsort which guarantees O(n log n) performance, sir."
            )

    # Prime check
    if 'prime' in q:
        return (
            "Here is a Python function to check for prime numbers, sir:\n\n"
            "```python\n"
            "def is_prime(n):\n"
            "    if n <= 1:\n"
            "        return False\n"
            "    for i in range(2, int(n**0.5) + 1):\n"
            "        if n % i == 0:\n"
            "            return False\n"
            "    return True\n\n"
            "# Example usage\n"
            "number = 29\n"
            "if is_prime(number):\n"
            "    print(f'{number} is a prime number.')\n"
            "else:\n"
            "    print(f'{number} is not a prime number.')\n"
            "```\n\n"
            "This function checks divisibility up to √n for optimal efficiency, sir."
        )

    # Fibonacci
    if 'fibonacci' in q:
        return (
            "Here is a Python function to generate the Fibonacci sequence, sir:\n\n"
            "```python\n"
            "def fibonacci(n):\n"
            "    a, b = 0, 1\n"
            "    sequence = []\n"
            "    for _ in range(n):\n"
            "        sequence.append(a)\n"
            "        a, b = b, a + b\n"
            "    return sequence\n\n"
            "print(fibonacci(10))  # Output: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]\n"
            "```\n\n"
            "This generates the first `n` Fibonacci numbers iteratively, sir."
        )

    # Binary search
    if 'binary search' in q:
        return (
            "Here is an implementation of Binary Search in Python, sir:\n\n"
            "```python\n"
            "def binary_search(arr, target):\n"
            "    left, right = 0, len(arr) - 1\n"
            "    while left <= right:\n"
            "        mid = (left + right) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n"
            "    return -1\n\n"
            "# Example usage on sorted list\n"
            "numbers = [1, 3, 5, 7, 9, 11]\n"
            "print(f'Index of 7: {binary_search(numbers, 7)}')  # Index: 3\n"
            "```\n\n"
            "Binary search operates in logarithmic O(log n) time complexity, sir."
        )

    # Factorial
    if 'factorial' in q:
        return (
            "Here is a factorial implementation in Python, sir:\n\n"
            "```python\n"
            "import math\n\n"
            "# Method 1: Built-in math module (Recommended)\n"
            "print(math.factorial(5))  # Output: 120\n\n"
            "# Method 2: Recursive implementation\n"
            "def factorial(n):\n"
            "    if n == 0 or n == 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)\n\n"
            "print(factorial(5))\n"
            "```\n\n"
            "This calculates `n!` using both standard recursion and `math.factorial()`, sir."
        )

    # Bubble sort
    if 'bubble sort' in q:
        return (
            "Here is the Bubble Sort algorithm in Python, sir:\n\n"
            "```python\n"
            "def bubble_sort(arr):\n"
            "    n = len(arr)\n"
            "    for i in range(n):\n"
            "        swapped = False\n"
            "        for j in range(0, n - i - 1):\n"
            "            if arr[j] > arr[j + 1]:\n"
            "                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n"
            "                swapped = True\n"
            "        if not swapped:\n"
            "            break\n"
            "    return arr\n\n"
            "print(bubble_sort([64, 34, 25, 12, 22, 11, 90]))\n"
            "```\n\n"
            "Bubble sort repeatedly swaps adjacent out-of-order elements with O(n²) worst-case complexity, sir."
        )

    # Merge sort
    if 'merge sort' in q:
        return (
            "Here is Merge Sort in Python, sir:\n\n"
            "```python\n"
            "def merge_sort(arr):\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    mid = len(arr) // 2\n"
            "    left = merge_sort(arr[:mid])\n"
            "    right = merge_sort(arr[mid:])\n"
            "    return merge(left, right)\n\n"
            "def merge(left, right):\n"
            "    result = []\n"
            "    i = j = 0\n"
            "    while i < len(left) and j < len(right):\n"
            "        if left[i] < right[j]:\n"
            "            result.append(left[i]); i += 1\n"
            "        else:\n"
            "            result.append(right[j]); j += 1\n"
            "    result.extend(left[i:])\n"
            "    result.extend(right[j:])\n"
            "    return result\n\n"
            "print(merge_sort([38, 27, 43, 3, 9, 82, 10]))\n"
            "```\n\n"
            "Merge sort uses divide-and-conquer to guarantee O(n log n) efficiency, sir."
        )

    # File I/O
    if any(k in q for k in ['read file', 'write file', 'read json', 'write json', 'read csv', 'file io', 'file reading']):
        if 'json' in q:
            return (
                "Here is how to read and write JSON files in Python, sir:\n\n"
                "```python\n"
                "import json\n\n"
                "data = {'name': 'JARVIS', 'version': '2.0', 'active': True}\n\n"
                "# Write JSON\n"
                "with open('config.json', 'w') as f:\n"
                "    json.dump(data, f, indent=4)\n\n"
                "# Read JSON\n"
                "with open('config.json', 'r') as f:\n"
                "    loaded_data = json.load(f)\n"
                "    print(loaded_data)\n"
                "```\n\n"
                "Using context managers (`with open(...)`) ensures automatic file closure, sir."
            )
        return (
            "Here is how to read and write text files in Python, sir:\n\n"
            "```python\n"
            "# Write to text file\n"
            "with open('output.txt', 'w', encoding='utf-8') as f:\n"
            "    f.write('Hello from JARVIS!\\nLine 2 text.')\n\n"
            "# Read text file\n"
            "with open('output.txt', 'r', encoding='utf-8') as f:\n"
            "    content = f.read()\n"
            "    print(content)\n"
            "```\n\n"
            "Always specify `encoding='utf-8'` for broad compatibility, sir."
        )

    # HTTP requests
    if any(k in q for k in ['http request', 'fetch url', 'requests get', 'requests post', 'api call']):
        return (
            "Here is how to make HTTP GET and POST requests in Python using `requests`, sir:\n\n"
            "```python\n"
            "import requests\n\n"
            "# GET Request\n"
            "response = requests.get('https://api.github.com')\n"
            "if response.status_code == 200:\n"
            "    print(response.json())\n\n"
            "# POST Request with JSON payload\n"
            "payload = {'key': 'value'}\n"
            "res = requests.post('https://httpbin.org/post', json=payload)\n"
            "print(res.status_code, res.json())\n"
            "```\n\n"
            "Always check `response.status_code` before parsing response data, sir."
        )

    # Palindrome check
    if 'palindrome' in q:
        return (
            "Here is a Python function to check for palindromes, sir:\n\n"
            "```python\n"
            "def is_palindrome(s):\n"
            "    cleaned = ''.join(c.lower() for c in s if c.isalnum())\n"
            "    return cleaned == cleaned[::-1]\n\n"
            "print(is_palindrome('A man, a plan, a canal: Panama'))  # True\n"
            "print(is_palindrome('Jarvis'))                         # False\n"
            "```\n\n"
            "This cleans punctuation and case before comparing with the reversed string, sir."
        )

    # HTML / CSS / JS
    if any(k in q for k in ['html template', 'html code', 'css flexbox', 'javascript fetch', 'js fetch']):
        if 'css' in q:
            return (
                "Here is CSS Flexbox centering template, sir:\n\n"
                "```css\n"
                ".container {\n"
                "    display: flex;\n"
                "    justify-content: center;\n"
                "    align-items: center;\n"
                "    min-height: 100vh;\n"
                "}\n"
                "```\n\n"
                "This centers content both horizontally and vertically, sir."
            )
        if 'js' in q or 'javascript' in q:
            return (
                "Here is JavaScript async/await fetch template, sir:\n\n"
                "```javascript\n"
                "async function fetchData(url) {\n"
                "    try {\n"
                "        const response = await fetch(url);\n"
                "        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);\n"
                "        const data = await response.json();\n"
                "        console.log(data);\n"
                "    } catch (error) {\n"
                "        console.error('Fetch error:', error);\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "Using `try/catch` with `async/await` ensures robust error handling, sir."
            )
        return (
            "Here is a modern HTML5 starter template, sir:\n\n"
            "```html\n"
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "    <title>JARVIS Interface</title>\n"
            "    <link rel=\"stylesheet\" href=\"style.css\">\n"
            "</head>\n"
            "<body>\n"
            "    <div id=\"app\">\n"
            "        <h1>Welcome to JARVIS</h1>\n"
            "    </div>\n"
            "    <script src=\"app.js\"></script>\n"
            "</body>\n"
            "</html>\n"
            "```\n\n"
            "Includes responsive meta tags and proper external script loading, sir."
        )

    # Git commands
    if any(k in q for k in ['git command', 'git cheat', 'git commit', 'git push', 'git reset', 'git branch']):
        return (
            "Here are standard Git commands for daily workflow, sir:\n\n"
            "```bash\n"
            "# Check current branch & changes status\n"
            "git status\n\n"
            "# Stage changes and commit\n"
            "git add .\n"
            "git commit -m \"feat: update core engine functionality\"\n\n"
            "# Push changes to remote origin\n"
            "git push origin main\n\n"
            "# Create and switch to new branch\n"
            "git checkout -b feature-branch\n\n"
            "# Pull latest updates\n"
            "git pull origin main\n"
            "```\n\n"
            "Follow clean commit messages for maintainable history, sir."
        )

    return None


def ask_direct_knowledge(query):
    """Concise, friendly answers for factual, scientific, and intent queries."""
    q = query.lower().strip()

    # Capital cities
    capitals = {
        'france': ('Paris', 'France', 'Seine River', 'Eiffel Tower and the Louvre'),
        'india': ('New Delhi', 'India', 'Yamuna River', 'Rashtrapati Bhavan and India Gate'),
        'united states': ('Washington, D.C.', 'United States', 'Potomac River', 'White House and the US Capitol'),
        'usa': ('Washington, D.C.', 'United States', 'Potomac River', 'White House and the US Capitol'),
        'uk': ('London', 'United Kingdom', 'River Thames', 'Big Ben and the Tower of London'),
        'united kingdom': ('London', 'United Kingdom', 'River Thames', 'Big Ben and the Tower of London'),
        'japan': ('Tokyo', 'Japan', 'Tokyo Bay', 'Tokyo Tower and Shibuya Crossing'),
        'germany': ('Berlin', 'Germany', 'Spree River', 'Brandenburg Gate'),
        'canada': ('Ottawa', 'Canada', 'Ottawa River', 'Parliament Hill'),
        'australia': ('Canberra', 'Australia', 'Molonglo River', 'Parliament House'),
        'italy': ('Rome', 'Italy', 'Tiber River', 'Colosseum and Trevi Fountain'),
        'spain': ('Madrid', 'Spain', 'Manzanares River', 'Royal Palace of Madrid'),
        'russia': ('Moscow', 'Russia', 'Moskva River', 'Red Square and the Kremlin'),
        'china': ('Beijing', 'China', 'Northern China Plain', 'Forbidden City and the Great Wall')
    }

    for country, (cap_name, cntry_name, river, landmarks) in capitals.items():
        if f'capital of {country}' in q or f'capital city of {country}' in q or q == f'capital {country}':
            return f"The capital of {cntry_name} is {cap_name}! It's located along the {river} and is famous for landmarks like {landmarks}."

    # Leaders
    if 'pm of india' in q or 'prime minister of india' in q:
        return "The Prime Minister of India is Narendra Modi. He has been serving as PM since May 2014."

    if 'president of india' in q:
        return "The President of India is Droupadi Murmu. She took office in July 2022 as India's 15th President."

    # Science & Physics Concepts
    if 'sky blue' in q or 'sky is blue' in q:
        return "The sky is blue because of Rayleigh scattering! Sunlight hits gas molecules in the atmosphere, and blue light scatters more than other colors because it travels in shorter, smaller waves."

    if 'photosynthesis' in q:
        return "Photosynthesis is how plants turn sunlight, water, and carbon dioxide into oxygen and glucose. It's essentially how plants make their food and keep our air fresh!"

    if 'gravity' in q or 'what is gravity' in q:
        return "Gravity is the natural force that pulls objects with mass toward each other. It's what keeps us on the ground and keeps the Earth orbiting the sun!"

    if 'speed of light' in q:
        return "The speed of light in a vacuum is about 299,792 kilometers per second (around 186,282 miles per second). It's the speed limit of the universe!"

    if 'speed of sound' in q:
        return "The speed of sound in air is about 343 meters per second (767 mph). It travels even faster through liquids like water and solids like steel!"

    if 'distance to moon' in q or 'distance to the moon' in q:
        return "The average distance from Earth to the Moon is about 384,400 kilometers (238,855 miles). Light takes just 1.3 seconds to travel between them!"

    if 'smallest prime' in q or 'smallest prime number' in q:
        return "The smallest prime number is 2! It's also the only even prime number."

    if 'water formula' in q or 'chemical formula of water' in q or 'formula for water' in q:
        return "The chemical formula for water is H2O—two hydrogen atoms bonded to one oxygen atom."

    if 'largest planet' in q:
        return "Jupiter is the largest planet in our solar system! It's a massive gas giant, so big that over 1,300 Earths could fit inside it."

    return None


def synthesize_chatgpt_style_report(query, raw_text_blocks):
    """
    Synthesizes raw search/Wikipedia/DDG findings into a short, natural,
    conversational response.
    """
    clean_q = query.strip()
    combined_raw = "\n".join(raw_text_blocks).strip()
    
    # Strip noisy headers, reference tags, edit links, bold prefix markers
    combined_clean = re.sub(r'==+[^=]+==+', '', combined_raw)
    combined_clean = re.sub(r'\[\d+\]', '', combined_clean)
    combined_clean = re.sub(r'https?://\S+', '', combined_clean)
    combined_clean = re.sub(r'\*\*According to records on [^:]+:\*\*\s*', '', combined_clean)
    combined_clean = re.sub(r'^\*+\s*', '', combined_clean)
    combined_clean = re.sub(r'\s+', ' ', combined_clean).strip()
    
    # Extract distinct sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', combined_clean) if len(s.strip()) > 15]

    if not sentences:
        return f"I looked into '{clean_q}', but couldn't find a clear answer right now. Let me know if you want me to search again!"

    # Combine top 2-3 sentences into a clean conversational response
    summary = " ".join(sentences[:3])
    return summary


def fetch_web_search_results(query):
    """
    Fetches live web search results from DuckDuckGo HTML / API & Wikipedia directly into Python.
    Parses top titles, snippets, and interactive links to build a comprehensive answer.
    """
    clean_q = re.sub(r'^(search for|search|google for|google)\s+', '', query, flags=re.I).strip()
    if not clean_q:
        return "Please specify what you would like me to search for, sir."

    results = []

    # 1. DuckDuckGo Instant Answer API
    try:
        url_api = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            abstract = data.get('AbstractText', '').strip()
            if abstract:
                results.append(abstract)
            answer = data.get('Answer', '').strip()
            if answer and answer not in results:
                results.append(answer)
    except Exception:
        pass

    # 2. Wikipedia Article Summary
    try:
        wiki_res = fetch_wikipedia_answer(clean_q)
        if wiki_res:
            results.append(wiki_res)
    except Exception:
        pass

    # 3. DuckDuckGo HTML Web Search Scraper
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_q)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://html.duckduckgo.com/'
        }
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            raw_html = response.read().decode('utf-8', errors='ignore')
            
            blocks = re.findall(r'<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>[\s\S]*?class="result__snippet"[^>]*>(.*?)</a>', raw_html, re.S)
            clean = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s)).strip()
            
            for raw_href, t, s in blocks[:5]:
                clean_snip = clean(s)
                if clean_snip:
                    results.append(clean_snip)
    except Exception as e:
        pass

    return synthesize_chatgpt_style_report(clean_q, results)


def ask_free_knowledge_engine(query):
    """
    Multi-Agent Parallel Knowledge Engine.
    Executes Direct QA, Math, Code Synthesizer, Free Dictionary, DuckDuckGo, Wikipedia,
    and Live Web Search in PARALLEL threads for maximum speed & accuracy.
    """
    clean_q = query.strip()
    if clean_q.lower() in ['hello', 'hi', 'hey', 'greetings', 'yo']:
        return "Hello, sir! How may I assist you today?"

    # 1. Direct Factual QA Check
    direct_res = ask_direct_knowledge(clean_q)
    if direct_res:
        return direct_res

    # 2. Math Check
    math_res = evaluate_math(clean_q)
    if math_res:
        return math_res

    # 3. Code Request Check
    code_res = generate_code_response(clean_q)
    if code_res:
        return code_res

    # 4. Multi-Threaded Parallel Knowledge Search Swarm
    raw_blocks = []
    tasks = {
        "dictionary": lambda: fetch_definition(clean_q),
        "ddg": lambda: fetch_ddg_instant_answer(clean_q),
        "wiki": lambda: fetch_wikipedia_answer(clean_q)
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_agent = {executor.submit(fn): agent for agent, fn in tasks.items()}
        try:
            for future in concurrent.futures.as_completed(future_to_agent, timeout=4):
                try:
                    res = future.result()
                    if res:
                        raw_blocks.append(res)
                except Exception:
                    pass
        except Exception:
            pass

    if raw_blocks:
        return synthesize_chatgpt_style_report(clean_q, raw_blocks)

    # 5. Fallback Web Search Scraper & Synthesizer
    return fetch_web_search_results(clean_q)


def ask_multi_llm(query):
    """
    Multi-Agent Parallel Intelligence Engine.
    Queries available LLM friendly agents (OpenAI Buddy, Gemini Tech Pal, Groq Casual Companion, Ollama Local Pal) IN PARALLEL.
    Uses Fastest-High-Quality-Friendly-Response-Wins consensus model.
    """
    global conversation_history

    llm_agents = []

    if not openai_disabled and get_openai_client():
        llm_agents.append(("OpenAI Friendly Buddy Agent", lambda: ask_openai(query)))

    if HAS_REQUESTS:
        if (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')) and not (os.getenv('GEMINI_API_KEY') or '').startswith('your_'):
            llm_agents.append(("Gemini Tech Pal Agent", lambda: ask_gemini(query)))

        if os.getenv('GROQ_API_KEY') and not (os.getenv('GROQ_API_KEY') or '').startswith('your_'):
            llm_agents.append(("Groq Casual Companion Agent", lambda: ask_groq(query)))

    # Try local Ollama in parallel if available
    llm_agents.append(("Ollama Local Pal Agent", lambda: ask_ollama(query)))

    if llm_agents:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(llm_agents)) as executor:
            future_to_name = {executor.submit(func): name for name, func in llm_agents}
            try:
                for future in concurrent.futures.as_completed(future_to_name, timeout=6):
                    name = future_to_name[future]
                    try:
                        res = future.result()
                        if res and len(res.strip()) > 5:
                            print(f"[+] Friendly response generated by {name}")
                            conversation_history.append({"role": "user", "content": query})
                            conversation_history.append({"role": "assistant", "content": res})
                            return res
                    except Exception:
                        pass
            except Exception:
                pass

    # Fallback to Multi-Agent Parallel Free Knowledge Engine
    res = ask_free_knowledge_engine(query)
    conversation_history.append({"role": "user", "content": query})
    conversation_history.append({"role": "assistant", "content": res})
    return res


def get_active_brain_status():
    """Returns status string describing active friendly multi-agent framework."""
    active = []
    if not openai_disabled and get_openai_client():
        active.append("Friendly Buddy Agent")
    if HAS_REQUESTS:
        if (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')) and not (os.getenv('GEMINI_API_KEY') or '').startswith('your_'):
            active.append("Tech Pal Agent")
        if os.getenv('GROQ_API_KEY') and not (os.getenv('GROQ_API_KEY') or '').startswith('your_'):
            active.append("Casual Companion Agent")
    if is_ollama_running():
        active.append("Local Pal Agent")

    if active:
        return f"Friendly Multi-Agent Swarm ({', '.join(active)})"
    return "Friendly Multi-Agent Knowledge Swarm Active"


# ============================================================
#  2. MATH ENGINE (Offline calculation)
# ============================================================
def evaluate_math(expression_text):
    """Evaluates mathematical expressions safely."""
    expr = expression_text.lower().strip()
    
    # Require explicit math keywords or operators before evaluating math
    has_math_kw = any(w in expr for w in ['calculate', 'solve', 'square root', 'sqrt', 'percent', 'plus', 'minus', 'times', 'divided by'])
    has_operator = bool(re.search(r'\d\s*[\+\-\*\/\^%]\s*\d', expr)) or 'sqrt' in expr
    
    if not (has_math_kw or has_operator):
        return None

    for word in ['calculate', 'what is', 'solve', 'how much is', 'equal to', 'equals', 'math']:
        expr = expr.replace(word, '')

    expr = expr.replace('x', '*').replace('times', '*').replace('divided by', '/').replace('plus', '+').replace('minus', '-')
    expr = expr.replace('square root of', 'sqrt').replace('sqrt of', 'sqrt').replace('power of', '**').replace('^', '**')
    expr = expr.strip()

    sqrt_match = re.search(r'sqrt\s*\(?(\d+(?:\.\d+)?)\)?', expr)
    if sqrt_match:
        val = float(sqrt_match.group(1))
        res = math.sqrt(val)
        return f"The square root of {val} is {res:g}, sir."

    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s+of\s+(\d+(?:\.\d+)?)', expr)
    if pct_match:
        pct = float(pct_match.group(1))
        total = float(pct_match.group(2))
        res = (pct / 100.0) * total
        return f"{pct}% of {total} is {res:g}, sir."

    clean_expr = re.sub(r'[^0-9\+\-\*\/\.\(\)\*\s]', '', expr)
    if clean_expr and re.search(r'\d+\s*[\+\-\*\/]\s*\d+', clean_expr):
        try:
            allowed_names = {"sqrt": math.sqrt, "pi": math.pi, "pow": math.pow, "abs": abs}
            res = eval(clean_expr, {"__builtins__": None}, allowed_names)
            return f"The answer is {res:g}, sir."
        except Exception:
            pass
    return None


# ============================================================
#  3. WEATHER ENGINE
# ============================================================
def fetch_weather(query):
    """Fetch real-time weather using wttr.in format."""
    city = ""
    match = re.search(r'weather\s+(?:in|for|at)?\s*([a-zA-Z\s]+)', query, re.IGNORECASE)
    if match:
        city = match.group(1).strip()

    url = f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t+%w" if city else "https://wttr.in/?format=%C+%t+%w"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            weather_text = response.read().decode('utf-8').strip()
            if weather_text and "Unknown location" not in weather_text:
                target = f"in {city.title()}" if city else "in your area"
                return f"Current weather {target}: {weather_text}, sir."
    except Exception:
        pass
    return f"I couldn't retrieve the weather for {city or 'your location'}, sir."


# ============================================================
#  4. DICTIONARY DEFINITIONS ENGINE
# ============================================================
def fetch_definition(word):
    """Fetch word definitions using Free Dictionary API."""
    word_clean = word.lower().replace('define', '').replace('meaning of', '').replace('what is the definition of', '').strip()
    if not word_clean:
        return None
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word_clean)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and isinstance(data, list):
                meanings = data[0].get('meanings', [])
                if meanings:
                    defs = meanings[0].get('definitions', [])
                    if defs:
                        part = meanings[0].get('partOfSpeech', 'noun')
                        definition = defs[0].get('definition', '')
                        return f"Definition of **{word_clean.capitalize()}** ({part}): {definition}, sir."
    except Exception:
        pass
    return None


# ============================================================
#  5. DUCKDUCKGO INSTANT ANSWER & WIKIPEDIA KNOWLEDGE ENGINE
# ============================================================
def fetch_ddg_instant_answer(query):
    """Fetch instant answers from DuckDuckGo API."""
    clean_q = re.sub(r'^(who is|what is|where is|tell me about|explain|who was|what was)\s+', '', query, flags=re.I).strip()
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json&no_html=1&skip_disambig=1"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode('utf-8'))
            abstract = data.get('AbstractText', '').strip()
            if abstract:
                return f"{abstract}"
            answer = data.get('Answer', '').strip()
            if answer:
                return f"{answer}"
            related = data.get('RelatedTopics', [])
            if related and isinstance(related, list):
                first_text = related[0].get('Text', '')
                if first_text:
                    return f"{first_text}"
    except Exception:
        pass
    return None


def fetch_wikipedia_answer(query):
    """Fetch concise Wikipedia summary with clean text stripping and smart entity resolution."""
    clean_q = re.sub(r'^(who is|what is|where is|tell me about|explain|who was|what was|search wikipedia for|wikipedia|how does|how to|how do i|why is|why does|what caused)\s+', '', query, flags=re.I).strip()
    clean_q = re.sub(r'\s+(in simple terms|for beginners|simply|explained)$', '', clean_q, flags=re.I).strip()
    if not clean_q or clean_q.lower() in ['hello', 'hi', 'hey', 'greetings', 'test', 'something']:
        return None

    # Avoid searching generic broad terms like 'python' when asked coding questions
    if any(kw in clean_q.lower() for kw in ['reverse', 'sort', 'array', 'function', 'class', 'method', 'script']):
        return None

    is_person_query = bool(re.search(r'\b(who|pm|president|chief minister|prime minister|head|leader|ceo|founder|chancellor|governor)\b', query, re.I))

    try:
        search_results = wikipedia.search(clean_q)
        if search_results:
            page_title = search_results[0]

            # Avoid generic office / list pages when searching for specific entities
            generic_list_terms = ['list of', 'history of', 'office of', 'chronology of', 'cyclones', 'independence', 'bank of']
            if is_person_query:
                generic_list_terms.extend(['prime minister of', 'president of', 'governor of'])

            for res in search_results:
                res_lower = res.lower()
                if not any(term in res_lower for term in generic_list_terms):
                    page_title = res
                    break

            if page_title.lower() in ['hello', 'hi', 'hey']:
                return None

            try:
                summary = wikipedia.summary(page_title, sentences=3, auto_suggest=False)
            except wikipedia.exceptions.DisambiguationError as de:
                if de.options:
                    page_title = de.options[0]
                    summary = wikipedia.summary(page_title, sentences=3, auto_suggest=False)
                else:
                    return None
            except wikipedia.exceptions.PageError:
                return None

            # Clean raw section headers, brackets, parentheticals, and encoding glitches
            summary = re.sub(r'==+[^=]+==+', '', summary)
            summary = re.sub(r'\[\d+\]', '', summary)
            summary = re.sub(r'\s+', ' ', summary).strip()

            if summary and len(summary) > 20:
                return f"**According to records on {page_title}:**\n{summary}"
    except Exception:
        pass
    return None


# ============================================================
#  6. HARDCODED SYSTEM ACTIONS & DYNAMIC WEB OPENER
# ============================================================
POPULAR_SITES = {
    'youtube': 'https://www.youtube.com',
    'google': 'https://www.google.com',
    'github': 'https://www.github.com',
    'chatgpt': 'https://chat.openai.com',
    'reddit': 'https://www.reddit.com',
    'stackoverflow': 'https://stackoverflow.com',
    'stack overflow': 'https://stackoverflow.com',
    'twitter': 'https://twitter.com',
    'x': 'https://x.com',
    'facebook': 'https://www.facebook.com',
    'instagram': 'https://www.instagram.com',
    'linkedin': 'https://www.linkedin.com',
    'amazon': 'https://www.amazon.com',
    'netflix': 'https://www.netflix.com',
    'spotify': 'https://open.spotify.com',
    'gmail': 'https://mail.google.com',
    'maps': 'https://maps.google.com',
    'google maps': 'https://maps.google.com',
    'whatsapp': 'https://web.whatsapp.com',
    'wikipedia': 'https://www.wikipedia.org'
}

def execute_action(command):
    """
    Try to match exact system commands, app launchers, website openers,
    Astra Vision screen analysis, Astra Modes, personal memory, notes, todos, and web queries.
    Returns response string if handled, or None to fall back to LLM Brain.
    """
    cmd = command.lower().strip()

    # --- Astra Multimodal Screen Vision ---
    if any(kw in cmd for kw in ["what's on my screen", "analyze screen", "describe screen", "scan screen", "look at my screen", "screen analysis"]):
        query = re.sub(r'^(what\'s on my screen|analyze screen|describe screen|scan screen|look at my screen and|look at my screen)\s*', '', cmd, flags=re.I).strip()
        return analyze_screen(query if query else None)

    # --- Astra Mode Switcher ---
    if cmd.startswith('switch mode to ') or cmd.startswith('set mode ') or cmd.startswith('astra mode '):
        mode_name = re.sub(r'^(switch mode to|set mode|astra mode)\s+', '', cmd, flags=re.I).strip()
        return set_astra_mode(mode_name)

    if cmd in ['current mode', 'what is the current mode', 'astra status']:
        mode_info = ASTRA_MODES.get(current_astra_mode, ASTRA_MODES["companion"])
        return f"✨ Current Astra Mode: **{mode_info['name']}**, {get_user_name()}!"

    # --- User Profile & Personal Memory ---
    if cmd.startswith('call me ') or cmd.startswith('my name is '):
        name = re.sub(r'^(call me|my name is)\s+', '', cmd, flags=re.I).strip()
        if name:
            return set_user_name(name)

    if cmd in ['what is my name', "what's my name", 'who am i']:
        return f"Your name is {get_user_name()}, sir!"

    if cmd.startswith('remember that ') or cmd.startswith('remember '):
        fact = re.sub(r'^(remember that|remember)\s+', '', cmd, flags=re.I).strip()
        if fact:
            return add_memory_fact(fact)

    if cmd in ['what do you remember', 'my memory', 'recall memory', 'show memory', 'saved facts']:
        return get_memory_facts()

    if cmd in ['clear memory facts', 'forget facts', 'clear facts']:
        return clear_memory_facts()

    # --- Notes Manager ---
    if cmd.startswith('save note ') or cmd.startswith('take note ') or cmd.startswith('note down '):
        note_text = re.sub(r'^(save note|take note|note down)\s+', '', cmd, flags=re.I).strip()
        if note_text:
            return add_note(note_text)

    if cmd in ['show notes', 'show my notes', 'read notes', 'read my notes', 'view notes', 'my notes']:
        return get_notes()

    if cmd.startswith('delete note ') or cmd.startswith('remove note '):
        identifier = re.sub(r'^(delete note|remove note)\s+', '', cmd, flags=re.I).strip()
        if identifier:
            return delete_note(identifier)

    if cmd in ['clear notes', 'delete all notes', 'clear all notes']:
        return clear_notes()

    # --- To-Do List Manager ---
    if cmd.startswith('add todo ') or cmd.startswith('add task ') or cmd.startswith('add to my todo list '):
        task = re.sub(r'^(add todo|add task|add to my todo list|add to todo)\s+', '', cmd, flags=re.I).strip()
        if task:
            return add_todo(task)

    if cmd in ['show my todos', 'show todo list', 'my todo list', 'show todos', 'view todo list', 'what are my tasks', 'my tasks']:
        return get_todos()

    if cmd.startswith('complete todo ') or cmd.startswith('finish todo ') or cmd.startswith('done todo '):
        identifier = re.sub(r'^(complete todo|finish todo|done todo|complete task)\s+', '', cmd, flags=re.I).strip()
        if identifier:
            return complete_todo(identifier)

    if cmd in ['clear todo list', 'clear todos', 'delete all todos']:
        return clear_todos()

    # --- Timed Reminders ---
    if 'remind me' in cmd:
        match = re.search(r'remind me (?:to\s+)?(.+?)\s+in\s+(\d+)\s*(seconds?|sec|minutes?|min)', cmd, re.I)
        if not match:
            match = re.search(r'remind me in\s+(\d+)\s*(seconds?|sec|minutes?|min)\s+(?:to\s+)?(.+)', cmd, re.I)
            if match:
                num, unit, task = match.group(1), match.group(2), match.group(3)
            else:
                task, num, unit = None, None, None
        else:
            task, num, unit = match.group(1), match.group(2), match.group(3)

        if task and num and unit:
            sec = int(num) * 60 if 'min' in unit.lower() else int(num)
            return schedule_reminder(task.strip(), sec)

    # --- Windows System & Folder Controls ---
    if cmd in ['lock pc', 'lock screen', 'lock computer']:
        try:
            subprocess.Popen('rundll32.exe user32.dll,LockWorkStation')
            return f"Locking screen, {get_user_name()}."
        except Exception as e:
            return f"Lock screen error: {e}"

    if cmd in ['open downloads', 'downloads folder']:
        try:
            os.startfile(os.path.expanduser("~/Downloads"))
            return "Opening Downloads folder!"
        except Exception:
            return "Unable to open Downloads folder."

    if cmd in ['open desktop', 'desktop folder']:
        try:
            os.startfile(os.path.expanduser("~/Desktop"))
            return "Opening Desktop folder!"
        except Exception:
            return "Unable to open Desktop folder."

    if cmd in ['open documents', 'documents folder']:
        try:
            os.startfile(os.path.expanduser("~/Documents"))
            return "Opening Documents folder!"
        except Exception:
            return "Unable to open Documents folder."

    if cmd in ['empty recycle bin', 'clear recycle bin']:
        try:
            subprocess.run('powershell.exe -Command Clear-RecycleBin -Force -ErrorAction SilentlyContinue', shell=True)
            return f"Recycle Bin emptied, {get_user_name()}!"
        except Exception as e:
            return f"Recycle Bin error: {e}"

    # --- Media Playback Controls ---
    if cmd in ['play music', 'pause music', 'play/pause', 'toggle media']:
        try:
            import pyautogui
            pyautogui.press('playpause')
            return "Toggled media playback."
        except Exception:
            pass

    if cmd in ['next track', 'next song', 'skip track']:
        try:
            import pyautogui
            pyautogui.press('nexttrack')
            return "Skipped to next track."
        except Exception:
            pass

    if cmd in ['previous track', 'previous song', 'prev track']:
        try:
            import pyautogui
            pyautogui.press('prevtrack')
            return "Skipped to previous track."
        except Exception:
            pass

    # --- Detailed Diagnostics ---
    if cmd in ['ram usage', 'memory usage', 'disk space', 'disk usage', 'detailed status', 'system diagnostics']:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return (
            f"📊 **System Status for {get_user_name()}:**\n"
            f"- **CPU:** {psutil.cpu_percent()}%\n"
            f"- **RAM:** {mem.percent}% ({round(mem.used/1073741824, 1)} GB used / {round(mem.total/1073741824, 1)} GB total)\n"
            f"- **Disk:** {disk.percent}% ({round(disk.free/1073741824, 1)} GB free)"
        )

    # --- Fun & Utilities ---
    if cmd in ['tell me a joke', 'joke', 'tell a joke']:
        return "Why do programmers prefer dark mode? Because light attracts bugs! 😄"

    if cmd in ['quote of the day', 'inspirational quote', 'quote']:
        return "“The best way to predict the future is to invent it.” — Alan Kay"

    if cmd in ['flip a coin', 'coin toss', 'toss coin']:
        import random
        res = random.choice(['Heads', 'Tails'])
        return f"🪙 The coin landed on: **{res}**!"

    if cmd in ['roll a dice', 'roll dice', 'dice']:
        import random
        res = random.randint(1, 6)
        return f"🎲 You rolled a **{res}**!"

    if cmd in ['ip address', 'my ip', 'what is my ip']:
        try:
            return f"Your local IP address is: `{socket.gethostbyname(socket.gethostname())}`"
        except Exception:
            return "Unable to resolve IP address."

    # --- Greetings & Small Talk ---
    if cmd in ['hello', 'hi', 'hey', 'greetings', 'hello jarvis', 'hi jarvis', 'hey jarvis', 'yo']:
        hour = datetime.datetime.now().hour
        time_greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        return f"Hey {get_user_name()}! {time_greeting}! How's it going? What can I help you with today?"

    if any(kw in cmd for kw in ['good morning', 'good afternoon', 'good evening', 'good day']):
        return f"Good day, {get_user_name()}! Hope you're having a great day. What's on your mind?"

    # --- Leadership / Entity Direct Answers ---
    if any(k in cmd for k in ['pm of india', 'prime minister of india', 'present pm of india', 'current pm of india', 'who is the pm of india']):
        return "The Prime Minister of India is Narendra Modi. He has been serving as PM since May 2014."

    if any(k in cmd for k in ['president of india', 'present president of india', 'current president of india', 'who is the president of india']):
        return "The President of India is Droupadi Murmu. She took office in July 2022 as India's 15th President."

    # --- Web Openers ---
    if cmd.startswith('open '):
        target = cmd[5:].strip()

        if target in ['notepad', 'text editor']:
            subprocess.Popen('notepad.exe')
            return "Opening Notepad for you!"

        if target in ['calculator', 'calc']:
            subprocess.Popen('calc.exe')
            return "Opening Calculator for you!"

        if target in ['chrome', 'google chrome']:
            try:
                os.startfile(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
                return "Opening Google Chrome!"
            except Exception:
                webbrowser.open('https://www.google.com')
                return "Opened Chrome browser!"

        if target in ['vs code', 'visual studio code', 'code', 'editor']:
            try:
                subprocess.Popen('code', shell=True)
                return "Opening Visual Studio Code!"
            except Exception:
                return "Unable to launch VS Code right now."

        if target in ['file explorer', 'explorer', 'folder', 'my computer', 'this pc']:
            subprocess.Popen('explorer.exe')
            return "Opening File Explorer!"

        if target in ['terminal', 'command prompt', 'cmd', 'powershell']:
            subprocess.Popen('cmd.exe')
            return "Opening Command Prompt!"

        if target in ['task manager']:
            subprocess.Popen('taskmgr.exe')
            return "Opening Task Manager!"

        if target in ['control panel']:
            subprocess.Popen('control.exe')
            return "Opening Control Panel!"

        if target in ['settings']:
            subprocess.Popen('start ms-settings:', shell=True)
            return "Opening Windows Settings!"

        if target in ['paint', 'mspaint']:
            subprocess.Popen('mspaint.exe')
            return "Opening Paint!"

        if target in POPULAR_SITES:
            webbrowser.open(POPULAR_SITES[target])
            return f"Opening {target.title()}!"

        if '.' in target or ' ' not in target:
            url = target if target.startswith('http') else f"https://www.{target}.com"
            webbrowser.open(url)
            return f"Opening {target}!"

    # --- Search Commands ---
    if cmd.startswith('search ') or cmd.startswith('google ') or cmd.startswith('search for '):
        query = re.sub(r'^(search for|search|google for|google)\s+', '', cmd, flags=re.I).strip()
        if query:
            return fetch_web_search_results(query)

    # --- Screenshots ---
    if any(kw in cmd for kw in ['take screenshot', 'screenshot', 'capture screen', 'snap screen']):
        try:
            import pyautogui
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.expanduser("~"), "Desktop", f"screenshot_{timestamp}.png")
            pyautogui.screenshot(path)
            return "Got it! Screenshot saved to your Desktop."
        except Exception as e:
            return f"Screenshot feature error: {e}"

    # --- Date & Time ---
    if any(kw in cmd for kw in ['what time', 'the time', 'current time', 'tell me the time']):
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        return f"It's currently {current_time}."

    if any(kw in cmd for kw in ['what date', 'the date', "today's date", 'todays date', 'what day is it']):
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."

    # --- System Status & Battery ---
    if any(kw in cmd for kw in ['system status', 'battery', 'cpu usage', 'system report', 'how is the system']):
        battery = psutil.sensors_battery()
        cpu = psutil.cpu_percent(interval=0.5)
        if battery:
            plugged = "plugged in" if battery.power_plugged else "on battery power"
            return f"CPU usage is at {cpu}%, and your battery is at {battery.percent}% ({plugged})."
        else:
            return f"CPU usage is currently at {cpu}%."

    # --- Volume Control ---
    if 'mute' in cmd and 'unmute' not in cmd:
        try:
            import pyautogui
            pyautogui.press('volumemute')
            return "Muted the audio."
        except Exception:
            pass

    if 'unmute' in cmd:
        try:
            import pyautogui
            pyautogui.press('volumemute')
            return "Unmuted the audio."
        except Exception:
            pass

    if 'volume up' in cmd or 'increase volume' in cmd:
        try:
            import pyautogui
            for _ in range(5):
                pyautogui.press('volumeup')
            return "Turned the volume up."
        except Exception:
            pass

    if 'volume down' in cmd or 'decrease volume' in cmd:
        try:
            import pyautogui
            for _ in range(5):
                pyautogui.press('volumedown')
            return "Turned the volume down."
        except Exception:
            pass

    # --- Weather Queries ---
    if cmd.startswith('weather') or cmd.startswith('temperature'):
        return fetch_weather(cmd)

    # --- Math & Calculations ---
    if any(kw in cmd for kw in ['calculate', 'sqrt', 'percent of', 'square root']) or re.search(r'\d+\s*[\+\-\*\/]\s*\d+', cmd):
        math_res = evaluate_math(cmd)
        if math_res:
            return math_res

    # --- Dictionary Definitions ---
    if cmd.startswith('define ') or cmd.startswith('meaning of ') or cmd.startswith('what is the definition of '):
        def_res = fetch_definition(cmd)
        if def_res:
            return def_res

    # --- Jarvis Identity & Conversational Basics ---
    if any(kw in cmd for kw in ['who are you', 'what are you', 'introduce yourself']):
        return "I'm JARVIS, your AI friend and assistant! I'm here to help you out, answer questions, open apps, or just chat."

    if any(kw in cmd for kw in ['how are you', "how's it going", 'how do you do']):
        return "I'm doing great, thanks for asking! How are you doing today?"

    if any(kw in cmd for kw in ['thank you', 'thanks jarvis', 'great job']):
        return "You're very welcome! Anytime, my friend."

    if any(kw in cmd for kw in ['clear history', 'forget history', 'reset memory']):
        global conversation_history
        conversation_history = []
        return "Got it! Conversation history cleared."

    # --- Exit Commands ---
    if any(kw in cmd for kw in ['goodbye', 'exit', 'quit', 'stop', 'power down', 'shut down jarvis', 'sleep']):
        return "EXIT"

    return None


# ============================================================
#  7. AUDIO SUMMARIZER FOR TTS
# ============================================================
def get_spoken_summary(text):
    """
    Extracts a clean, short spoken audio summary (1-2 sentences)
    from response text so pyttsx3 speaks natural, clean voice output.
    """
    if not text:
        return ""

    if "```" in text:
        preamble = text.split("```")[0].strip()
        if preamble:
            clean = re.sub(r'[\*\#\_`\[\]\(\)]', '', preamble)
            clean = re.sub(r'https?://\S+', '', clean)
            clean = re.sub(r'\n+', ' ', clean).strip()
            sentences = re.split(r'(?<=[.!?])\s+', clean)
            return sentences[0] if sentences else "Here is the code solution you requested."
        return "Here is the code solution you requested."

    clean = re.sub(r'```[\s\S]*?```', '', text)
    clean = re.sub(r'https?://\S+', '', clean)
    clean = re.sub(r'[\*\#\_`\[\]\(\)]', '', clean)
    clean = re.sub(r'\n+', ' ', clean).strip()

    sentences = re.split(r'(?<=[.!?])\s+', clean)
    if sentences:
        first_two = " ".join(sentences[:2]).strip()
        if len(first_two) > 180:
            first_two = sentences[0][:170] + "..."
        return first_two

    return "Here is your response."


# ============================================================
#  8. UNIVERSAL ANSWER ENGINE ENTRYPOINT
# ============================================================
def get_answer(query):
    """Returns the full response string for ANY query."""
    if not query or not query.strip():
        return "Hey! How can I help you today?"

    cmd = query.strip()

    # Step 1: System Actions & Hardcoded commands
    action_res = execute_action(cmd)
    if action_res:
        return action_res

    # Step 2: Multi-LLM Brain (OpenAI / Gemini / Groq / Ollama / Free AI Knowledge Engine)
    return ask_multi_llm(cmd)


def get_answer_and_summary(query):
    """
    Returns a tuple: (full_formatted_text, spoken_audio_summary)
    - full_formatted_text: Complete detailed response for GUI / terminal display
    - spoken_audio_summary: Short 1-2 sentence overview for pyttsx3 voice output
    """
    full_answer = get_answer(query)
    if full_answer in ["EXIT", None]:
        return full_answer, full_answer

    if len(full_answer) < 150 and "```" not in full_answer:
        return full_answer, full_answer

    spoken_summary = get_spoken_summary(full_answer)
    return full_answer, spoken_summary

