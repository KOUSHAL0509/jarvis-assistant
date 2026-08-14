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
import datetime
import urllib.parse
import urllib.request
import html
import subprocess
import webbrowser
import psutil
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
#  1. MULTI-LLM BRAIN PROVIDERS
# ============================================================

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


def ask_openai(query):
    """Query OpenAI GPT-4o-mini / GPT-4o."""
    global openai_disabled
    client = get_openai_client()
    if not client:
        return None

    messages = [
        {
            "role": "system",
            "content": (
                "You are JARVIS, Tony Stark's advanced AI assistant. You are witty, polite, highly intelligent, "
                "and provide complete, helpful, accurate ChatGPT-level responses. Use clear formatting, code blocks, "
                "or bullet points where relevant. Address the user as 'sir'."
            )
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
            print("[!] OpenAI API Key is invalid or expired. Switching to Free AI Engine.")
            openai_disabled = True
        else:
            print(f"[!] OpenAI API Error: {e}")
        return None


def ask_gemini(query):
    """Query Google Gemini API if GEMINI_API_KEY or GOOGLE_API_KEY is available."""
    if not HAS_REQUESTS:
        return None

    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key or not api_key.strip() or api_key.startswith("your_"):
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
    
    contents = []
    system_prompt = (
        "You are JARVIS, Tony Stark's AI assistant. You are witty, polite, highly intelligent, "
        "and provide comprehensive, accurate ChatGPT-style answers with clear formatting and code blocks when needed. "
        "Address the user as 'sir'."
    )
    
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
    """Query Groq Llama-3 API if GROQ_API_KEY is available."""
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
            "content": (
                "You are JARVIS, Tony Stark's AI assistant. You are witty, polite, highly intelligent, "
                "and provide complete, helpful, accurate ChatGPT-level responses. Address the user as 'sir'."
            )
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
    """Query local Ollama instance if running on localhost:11434."""
    if not HAS_REQUESTS:
        return None

    url = "http://localhost:11434/api/chat"
    messages = [
        {
            "role": "system",
            "content": "You are JARVIS, Tony Stark's AI assistant. Answer concisely and accurately, sir."
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
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()
    except Exception:
        pass
    return None


def generate_code_response(query):
    """Synthesize clean code snippets for programming queries when offline/zero-config."""
    q = query.lower()
    if not any(k in q for k in ['code', 'script', 'python', 'function', 'program', 'java', 'html', 'css', 'cpp', 'algorithm']):
        return None

    if 'prime' in q:
        return (
            "Here is a Python script to check for prime numbers, sir:\n\n"
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
            "This function checks divisibility up to the square root of `n` for efficiency, sir."
        )

    if 'fibonacci' in q:
        return (
            "Here is a Python function to generate Fibonacci numbers, sir:\n\n"
            "```python\n"
            "def fibonacci(n):\n"
            "    a, b = 0, 1\n"
            "    sequence = []\n"
            "    for _ in range(n):\n"
            "        sequence.append(a)\n"
            "        a, b = b, a + b\n"
            "    return sequence\n\n"
            "print(fibonacci(10))\n"
            "```\n\n"
            "This returns the first `n` numbers of the Fibonacci sequence, sir."
        )

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
            "# Example usage\n"
            "numbers = [1, 3, 5, 7, 9, 11]\n"
            "print(f'Index: {binary_search(numbers, 7)}')\n"
            "```\n\n"
            "Binary search operates in O(log n) time complexity, sir."
        )

    if 'factorial' in q:
        return (
            "Here is a recursive factorial function in Python, sir:\n\n"
            "```python\n"
            "def factorial(n):\n"
            "    if n == 0 or n == 1:\n"
            "        return 1\n"
            "    return n * factorial(n - 1)\n\n"
            "print(factorial(5))\n"
            "```\n\n"
            "This calculates n! using recursion, sir."
        )

    return None


def fetch_web_search_results(query):
    """
    Fetches live web search results from DuckDuckGo HTML / API & Wikipedia directly into Python.
    Parses top titles and snippets to build a comprehensive answer directly inside Jarvis
    WITHOUT opening any external web browser.
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
                results.append(f"**Overview:**\n{abstract}")
            answer = data.get('Answer', '').strip()
            if answer and answer not in results:
                results.append(f"**Quick Answer:**\n{answer}")
    except Exception:
        pass

    # 2. Wikipedia Article Summary
    try:
        search_results = wikipedia.search(clean_q)
        if search_results:
            summary = wikipedia.summary(search_results[0], sentences=3)
            summary = re.sub(r'\([^)]*\)', '', summary).strip()
            if summary and summary not in results:
                results.append(f"**From Wikipedia ({search_results[0]}):**\n{summary}")
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
        with urllib.request.urlopen(req, timeout=5) as response:
            raw_html = response.read().decode('utf-8', errors='ignore')
            titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', raw_html, re.S)
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', raw_html, re.S)
            
            clean = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s)).strip()
            
            extracted = []
            for t, s in zip(titles[:4], snippets[:4]):
                clean_title = clean(t)
                clean_snip = clean(s)
                if clean_title and clean_snip and clean_title not in extracted:
                    extracted.append(f"• **{clean_title}**\n  {clean_snip}")
            
            if extracted:
                results.append("**Top Web Search Findings:**\n" + "\n\n".join(extracted))
    except Exception as e:
        print(f"[!] Live search scraper error: {e}")

    if results:
        full_text = f"Here is the information I gathered for **'{clean_q}'**, sir:\n\n" + "\n\n".join(results)
        if not full_text.lower().endswith("sir."):
            full_text += "\n\nI hope this answers your query, sir."
        return full_text

    return (
        f"I searched for **'{clean_q}'**, sir, but could not retrieve matching entries at this moment. "
        f"Please check your internet connection or try rephrasing."
    )


def ask_free_knowledge_engine(query):
    """
    Zero-config free AI & knowledge engine fallback.
    Combines DuckDuckGo Instant Answers, Wikipedia, Free Dictionary, Math Engine, Code Synthesizer,
    and Live Web Search Scraping to generate detailed ChatGPT-style responses directly in Jarvis!
    """
    clean_q = query.strip()
    sections = []

    # 1. Math Check
    math_res = evaluate_math(clean_q)
    if math_res:
        return math_res

    # 2. Code Request Check
    code_res = generate_code_response(clean_q)
    if code_res:
        return code_res

    # 3. Dictionary Definition Check
    def_res = fetch_definition(clean_q)
    if def_res:
        sections.append(def_res)

    # 4. DuckDuckGo Instant Answer
    ddg_res = fetch_ddg_instant_answer(clean_q)
    if ddg_res and ddg_res not in sections:
        sections.append(ddg_res)

    # 5. Wikipedia Summary / Deep Content
    wiki_res = fetch_wikipedia_answer(clean_q)
    if wiki_res and wiki_res not in sections:
        sections.append(wiki_res)

    if sections:
        response = "\n\n".join(sections)
        if not response.lower().endswith("sir."):
            response += "\n\nI hope this answers your query, sir."
        return response

    # 6. Fallback Web Search Scraper (Delivers results inside Jarvis UI, NO browser launch!)
    return fetch_web_search_results(clean_q)


def ask_multi_llm(query):
    """
    Unified multi-LLM brain dispatcher.
    Tries OpenAI -> Gemini -> Groq -> Ollama -> Free Knowledge Engine.
    """
    global conversation_history

    # Try OpenAI (if enabled & configured)
    if not openai_disabled:
        res = ask_openai(query)
        if res:
            conversation_history.append({"role": "user", "content": query})
            conversation_history.append({"role": "assistant", "content": res})
            return res

    # Try Gemini
    res = ask_gemini(query)
    if res:
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": res})
        return res

    # Try Groq
    res = ask_groq(query)
    if res:
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": res})
        return res

    # Try Local Ollama
    res = ask_ollama(query)
    if res:
        conversation_history.append({"role": "user", "content": query})
        conversation_history.append({"role": "assistant", "content": res})
        return res

    # Free Knowledge Engine fallback
    res = ask_free_knowledge_engine(query)
    conversation_history.append({"role": "user", "content": query})
    conversation_history.append({"role": "assistant", "content": res})
    return res


def get_active_brain_status():
    """Returns status string describing which brain provider is active."""
    if not openai_disabled and get_openai_client():
        return "GPT-4o Online"
    if HAS_REQUESTS:
        if (os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')) and not (os.getenv('GEMINI_API_KEY') or '').startswith('your_'):
            return "Gemini Online"
        if os.getenv('GROQ_API_KEY') and not (os.getenv('GROQ_API_KEY') or '').startswith('your_'):
            return "Groq Online"
    return "Free AI Brain Active"


# ============================================================
#  2. MATH ENGINE (Offline calculation)
# ============================================================
def evaluate_math(expression_text):
    """Evaluates mathematical expressions safely."""
    expr = expression_text.lower()
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
    if clean_expr and re.search(r'\d', clean_expr):
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
    """Fetch concise Wikipedia summary."""
    clean_q = re.sub(r'^(who is|what is|where is|tell me about|explain|who was|what was|search wikipedia for|wikipedia)\s+', '', query, flags=re.I).strip()
    if not clean_q:
        return None
    try:
        search_results = wikipedia.search(clean_q)
        if search_results:
            summary = wikipedia.summary(search_results[0], sentences=3)
            summary = re.sub(r'\([^)]*\)', '', summary).strip()
            return f"**According to records on {search_results[0]}:**\n{summary}"
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
    math, weather, identity, and system status queries.
    Returns response string if handled, or None to fall back to LLM Brain.
    """
    cmd = command.lower().strip()

    # --- Web Openers ---
    if cmd.startswith('open '):
        target = cmd[5:].strip()

        if target in ['notepad', 'text editor']:
            subprocess.Popen('notepad.exe')
            return "Opening Notepad, sir."

        if target in ['calculator', 'calc']:
            subprocess.Popen('calc.exe')
            return "Opening Calculator, sir."

        if target in ['chrome', 'google chrome']:
            try:
                os.startfile(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
                return "Opening Google Chrome, sir."
            except Exception:
                webbrowser.open('https://www.google.com')
                return "Opened Chrome browser, sir."

        if target in ['vs code', 'visual studio code', 'code', 'editor']:
            try:
                subprocess.Popen('code', shell=True)
                return "Opening Visual Studio Code, sir."
            except Exception:
                return "Unable to launch VS Code, sir."

        if target in ['file explorer', 'explorer', 'folder', 'my computer', 'this pc']:
            subprocess.Popen('explorer.exe')
            return "Opening File Explorer, sir."

        if target in ['terminal', 'command prompt', 'cmd', 'powershell']:
            subprocess.Popen('cmd.exe')
            return "Opening Command Prompt, sir."

        if target in ['task manager']:
            subprocess.Popen('taskmgr.exe')
            return "Opening Task Manager, sir."

        if target in ['control panel']:
            subprocess.Popen('control.exe')
            return "Opening Control Panel, sir."

        if target in ['settings']:
            subprocess.Popen('start ms-settings:', shell=True)
            return "Opening Windows Settings, sir."

        if target in ['paint', 'mspaint']:
            subprocess.Popen('mspaint.exe')
            return "Opening Paint, sir."

        if target in POPULAR_SITES:
            webbrowser.open(POPULAR_SITES[target])
            return f"Opening {target.title()}, sir."

        if '.' in target or ' ' not in target:
            url = target if target.startswith('http') else f"https://www.{target}.com"
            webbrowser.open(url)
            return f"Opening {target}, sir."

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
            return f"Screenshot saved to your Desktop, sir."
        except Exception as e:
            return f"Screenshot feature error: {e}"

    # --- Date & Time ---
    if any(kw in cmd for kw in ['what time', 'the time', 'current time', 'tell me the time']):
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}, sir."

    if any(kw in cmd for kw in ['what date', 'the date', "today's date", 'todays date', 'what day is it']):
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}, sir."

    # --- System Status & Battery ---
    if any(kw in cmd for kw in ['system status', 'battery', 'cpu usage', 'system report', 'how is the system']):
        battery = psutil.sensors_battery()
        cpu = psutil.cpu_percent(interval=0.5)
        if battery:
            plugged = "plugged in" if battery.power_plugged else "on battery power"
            return f"System CPU is at {cpu}%. Battery is at {battery.percent}%, currently {plugged}, sir."
        else:
            return f"System CPU usage is at {cpu}%, sir."

    # --- Volume Control ---
    if 'mute' in cmd and 'unmute' not in cmd:
        try:
            import pyautogui
            pyautogui.press('volumemute')
            return "Audio muted, sir."
        except Exception:
            pass

    if 'unmute' in cmd:
        try:
            import pyautogui
            pyautogui.press('volumemute')
            return "Audio unmuted, sir."
        except Exception:
            pass

    if 'volume up' in cmd or 'increase volume' in cmd:
        try:
            import pyautogui
            for _ in range(5):
                pyautogui.press('volumeup')
            return "Volume increased, sir."
        except Exception:
            pass

    if 'volume down' in cmd or 'decrease volume' in cmd:
        try:
            import pyautogui
            for _ in range(5):
                pyautogui.press('volumedown')
            return "Volume decreased, sir."
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
        return "I am JARVIS, your personal AI assistant. Designed to answer any question, execute system commands, and assist you, sir."

    if any(kw in cmd for kw in ['how are you', "how's it going", 'how do you do']):
        return "All systems operational and running smoothly, sir. How can I assist you today?"

    if any(kw in cmd for kw in ['thank you', 'thanks jarvis', 'great job']):
        return "Always a pleasure to be of service, sir."

    if any(kw in cmd for kw in ['clear history', 'forget history', 'reset memory']):
        global conversation_history
        conversation_history = []
        return "Conversation history reset, sir."

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
    from a detailed ChatGPT response so pyttsx3 doesn't speak long code blocks.
    """
    if not text:
        return ""

    if "```" in text:
        preamble = text.split("```")[0].strip()
        if preamble:
            clean = re.sub(r'[\*\#\_`]', '', preamble)
            sentences = re.split(r'(?<=[.!?])\s+', clean)
            return sentences[0] if sentences else "Here is the code solution you requested, sir."
        return "Here is the code solution you requested, sir."

    clean = re.sub(r'```[\s\S]*?```', '', text)
    clean = re.sub(r'[\*\#\_`\[\]\(\)]', '', clean)
    clean = re.sub(r'\n+', ' ', clean).strip()

    sentences = re.split(r'(?<=[.!?])\s+', clean)
    if sentences:
        first_two = " ".join(sentences[:2]).strip()
        if len(first_two) > 200:
            first_two = sentences[0][:180] + "..."
        if not first_two.lower().endswith("sir.") and not first_two.lower().endswith("sir!"):
            first_two += ", sir."
        return first_two

    return "Here is your response, sir."


# ============================================================
#  8. UNIVERSAL ANSWER ENGINE ENTRYPOINT
# ============================================================
def get_answer(query):
    """Returns the full ChatGPT-level response string for ANY query."""
    if not query or not query.strip():
        return "At your service, sir. How can I help?"

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

