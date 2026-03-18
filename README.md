# 🔵 JARVIS — AI Voice Assistant for Windows

A fully-featured, Iron Man-inspired AI voice assistant for **Windows** with ChatGPT brain, voice interaction, and system actions.

Inspired by [prudhviraj0310/jarvis-learning-server](https://github.com/prudhviraj0310/jarvis-learning-server) and ported to Windows.

---

## ✨ Features

- 🎤 **Voice Recognition**: Google Speech Recognition for fast, accurate command input
- 🧠 **ChatGPT Integration**: Powered by GPT-4o-mini for intelligent responses to any question
- 🔊 **Text-to-Speech**: Windows SAPI5 voice engine (offline, instant)
- ⚡ **System Actions**: Open apps, take screenshots, search Google, check system status, and more
- 💾 **Conversation Memory**: Remembers context across interactions
- 🔋 **System Monitoring**: Real-time CPU and battery status reports

---

## 📁 Project Structure

```
jarvis-assistant/
├── jarvis.py           # Main assistant script (all-in-one)
├── .env                # Your OpenAI API key (create from .env.example)
├── .env.example        # Template for API key
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🚀 Setup Instructions

### Step 1: Install Python
Download and install Python 3.10+ from [python.org](https://www.python.org/downloads/).

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Add Your OpenAI API Key (Optional — for smart responses)

```bash
copy .env.example .env
```

Edit `.env` and add your key:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

Get your key from: https://platform.openai.com/api-keys

> **Note:** Jarvis works without an API key — system commands, Wikipedia, time, etc. all work offline. The API key is only needed for the ChatGPT "brain" that answers general questions.

---

## ▶️ Running JARVIS

```bash
python jarvis.py
```

### Usage:
1. Wait for Jarvis to greet you
2. Speak naturally — no wake word needed
3. Jarvis will execute actions or respond with GPT
4. Say **"exit"** or **"goodbye"** to quit

---

## 🎮 Available Commands

### Web & Apps
- "Open YouTube / Google / GitHub / ChatGPT"
- "Open Chrome / Notepad / Calculator / VS Code / File Explorer"
- "Search [anything]" — searches Google

### System
- "Take a screenshot"
- "System status" / "Battery" / "CPU"
- "What time is it?" / "What's the date?"

### AI Brain (requires OpenAI API key)
- "Tell me a joke"
- "Explain quantum physics"
- Any question — goes to GPT-4o-mini

### Jarvis Control
- "Clear history" — reset conversation memory
- "Exit" / "Goodbye" / "Power down" — shut down

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Microphone not working | Check Windows Settings → Privacy → Microphone |
| Google API error | Check your internet connection |
| GPT not responding | Add your OpenAI API key to `.env` |

---

## 🎯 System Requirements

- Windows 10/11
- Python 3.10+
- Working microphone
- Internet connection (for speech recognition & GPT)

---

## 📜 License

MIT License — feel free to modify and enhance!

---

**Built with ❤️ for Windows**

🔵 *"Jarvis online. All systems operational."*
