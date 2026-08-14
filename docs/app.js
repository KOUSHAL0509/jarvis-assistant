/* ============================================================
   JARVIS WEB — Standalone Frontend (No Python Backend)
   Uses: Web Speech API, SpeechSynthesis, OpenAI API (browser)
   ============================================================ */

// ============================================================
//  BACKGROUND PARTICLES
// ============================================================
(function initParticles() {
    const canvas = document.getElementById('bg-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    const PARTICLE_COUNT = 50;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    class Particle {
        constructor() { this.reset(); }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 1.5 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            this.opacity = Math.random() * 0.4 + 0.1;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 195, 255, ${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle());

    function drawLines() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 195, 255, ${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        drawLines();
        requestAnimationFrame(animate);
    }
    animate();
})();


// ============================================================
//  ORB ANIMATION
// ============================================================
const orbCanvas = document.getElementById('orb-canvas');
const orbCtx = orbCanvas.getContext('2d');
const orbLabel = document.getElementById('orb-label');
let orbState = 'idle';
let orbTime = 0;

const ORB_COLORS = {
    idle:      { r: 0, g: 195, b: 255 },
    listening: { r: 0, g: 255, b: 136 },
    thinking:  { r: 240, g: 192, b: 64 },
    speaking:  { r: 0, g: 195, b: 255 }
};

function drawOrb() {
    const W = orbCanvas.width;
    const H = orbCanvas.height;
    const cx = W / 2;
    const cy = H / 2;
    const baseRadius = Math.min(W, H) * 0.3;

    orbCtx.clearRect(0, 0, W, H);
    orbTime += 0.02;

    const color = ORB_COLORS[orbState] || ORB_COLORS.idle;
    const intensity = orbState === 'idle' ? 0.6 : 1.0;
    const pulseSpeed = orbState === 'listening' ? 3 : orbState === 'thinking' ? 5 : 1.5;
    const pulseAmp = orbState === 'thinking' ? 8 : orbState === 'listening' ? 5 : 3;

    // Outer glow rings
    for (let i = 3; i >= 0; i--) {
        const glowR = baseRadius + 15 + i * 12;
        const alpha = 0.02 * (4 - i) * intensity;
        orbCtx.beginPath();
        orbCtx.arc(cx, cy, glowR + Math.sin(orbTime * 1.5 + i) * 3, 0, Math.PI * 2);
        orbCtx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`;
        orbCtx.fill();
    }

    // Rotating ring segments
    for (let r = 0; r < 3; r++) {
        const ringRadius = baseRadius + 8 + r * 14;
        const segments = 6 + r * 2;
        const segmentAngle = (Math.PI * 2) / segments;
        const gapAngle = segmentAngle * 0.3;
        const rotationSpeed = (r % 2 === 0 ? 1 : -1) * (0.3 + r * 0.15);

        orbCtx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${(0.15 + 0.1 * intensity) * (1 - r * 0.2)})`;
        orbCtx.lineWidth = 1.5;

        for (let s = 0; s < segments; s++) {
            const startAngle = orbTime * rotationSpeed + s * segmentAngle + gapAngle / 2;
            const endAngle = startAngle + segmentAngle - gapAngle;
            orbCtx.beginPath();
            orbCtx.arc(cx, cy, ringRadius, startAngle, endAngle);
            orbCtx.stroke();
        }
    }

    // Main orb pulse
    const pulse = Math.sin(orbTime * pulseSpeed) * pulseAmp;
    const orbR = baseRadius + pulse;

    const grad = orbCtx.createRadialGradient(cx, cy, 0, cx, cy, orbR);
    grad.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.25 * intensity})`);
    grad.addColorStop(0.5, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.1 * intensity})`);
    grad.addColorStop(1, `rgba(${color.r}, ${color.g}, ${color.b}, 0.02)`);
    orbCtx.beginPath();
    orbCtx.arc(cx, cy, orbR, 0, Math.PI * 2);
    orbCtx.fillStyle = grad;
    orbCtx.fill();

    // Core
    const coreGrad = orbCtx.createRadialGradient(cx, cy, 0, cx, cy, 12);
    coreGrad.addColorStop(0, `rgba(255,255,255, ${0.7 * intensity})`);
    coreGrad.addColorStop(0.5, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.5 * intensity})`);
    coreGrad.addColorStop(1, 'rgba(0,0,0,0)');
    orbCtx.beginPath();
    orbCtx.arc(cx, cy, 12, 0, Math.PI * 2);
    orbCtx.fillStyle = coreGrad;
    orbCtx.fill();

    // Inner ring
    orbCtx.beginPath();
    orbCtx.arc(cx, cy, baseRadius - 5, 0, Math.PI * 2);
    orbCtx.strokeStyle = `rgba(${color.r}, ${color.g}, ${color.b}, ${0.15 * intensity})`;
    orbCtx.lineWidth = 1;
    orbCtx.stroke();

    requestAnimationFrame(drawOrb);
}
drawOrb();

function setOrbState(state) {
    orbState = state;
    orbLabel.textContent = state.toUpperCase();
    orbLabel.className = state;
    orbCanvas.className = state;
}


// ============================================================
//  CLOCK
// ============================================================
function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent =
        now.getHours().toString().padStart(2, '0') + ':' +
        now.getMinutes().toString().padStart(2, '0') + ':' +
        now.getSeconds().toString().padStart(2, '0');
}
setInterval(updateClock, 1000);
updateClock();


// ============================================================
//  MESSAGES
// ============================================================
const messagesContainer = document.getElementById('messages');

function addMessage(sender, text) {
    const div = document.createElement('div');
    const isJarvis = sender.toLowerCase() === 'jarvis';
    div.className = `message ${isJarvis ? 'jarvis-msg' : 'user-msg'}`;

    const senderSpan = document.createElement('span');
    senderSpan.className = 'msg-sender';
    senderSpan.textContent = sender.toUpperCase();

    const textSpan = document.createElement('span');
    textSpan.className = 'msg-text';
    textSpan.textContent = text;

    div.appendChild(senderSpan);
    div.appendChild(textSpan);
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


// ============================================================
//  TEXT-TO-SPEECH (Browser SpeechSynthesis API)
// ============================================================
let voiceEnabled = true;

function speak(text) {
    if (!voiceEnabled || !text) return;
    if (!('speechSynthesis' in window)) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 0.9;
    utterance.volume = 1;

    // Try to pick a male English voice
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v =>
        v.lang.startsWith('en') && v.name.toLowerCase().includes('male')
    ) || voices.find(v =>
        v.lang.startsWith('en') && v.name.toLowerCase().includes('david')
    ) || voices.find(v => v.lang.startsWith('en'));

    if (preferred) utterance.voice = preferred;

    utterance.onstart = () => setOrbState('speaking');
    utterance.onend = () => setOrbState('idle');
    window.speechSynthesis.speak(utterance);
}

// Load voices
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}


// ============================================================
//  OPENAI GPT (Direct browser API call)
// ============================================================
let apiKey = localStorage.getItem('jarvis_openai_key') || '';
let conversationHistory = [];

async function askGPT(query) {
    if (!apiKey) {
        return "My AI brain is offline, sir. Please set your OpenAI API key using the Settings panel.";
    }

    const messages = [
        { role: "system", content: "You are JARVIS, Tony Stark's AI assistant from Iron Man. You are witty, intelligent, and speak concisely in 1-2 sentences max. Address the user as 'sir'." },
        ...conversationHistory.slice(-6),
        { role: "user", content: query }
    ];

    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: 'gpt-4o-mini',
                messages: messages,
                max_tokens: 150,
                temperature: 0.7
            })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            return `Error from OpenAI: ${err.error?.message || response.statusText}`;
        }

        const data = await response.json();
        const result = data.choices[0].message.content.trim();
        conversationHistory.push({ role: "user", content: query });
        conversationHistory.push({ role: "assistant", content: result });
        return result;
    } catch (e) {
        return `Connection error, sir: ${e.message}`;
    }
}

function updateBrainStatus() {
    const el = document.getElementById('brain-status');
    if (apiKey) {
        el.textContent = 'GPT-4o Ready';
        el.style.color = 'var(--accent-green)';
    } else {
        el.textContent = 'Set API Key';
        el.style.color = 'var(--accent-gold)';
    }
}


// ============================================================
//  ACTIONS — Execute commands in the browser
// ============================================================
function executeAction(command) {
    // Web links
    if (command.includes('open youtube') || command === 'youtube') {
        window.open('https://www.youtube.com', '_blank');
        return "Opening YouTube, sir.";
    }
    if (command.includes('open google') || command === 'google') {
        window.open('https://www.google.com', '_blank');
        return "Opening Google, sir.";
    }
    if (command.includes('open github') || command === 'github') {
        window.open('https://www.github.com', '_blank');
        return "Opening GitHub, sir.";
    }
    if (command.includes('open chatgpt') || command.includes('chat gpt')) {
        window.open('https://chat.openai.com', '_blank');
        return "Opening ChatGPT, sir.";
    }
    if (command.startsWith('search ') || command.startsWith('google ')) {
        const query = command.replace(/^(search|google)\s+/i, '').replace('for ', '').trim();
        if (query) {
            return `I have processed your search query for **'${query}'**, sir. Multi-brain intelligence systems are active inside your Jarvis console.`;
        }
    }

    // Date & Time
    if (['what time', 'the time', 'current time', 'tell me the time'].some(k => command.includes(k))) {
        const t = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        return `The current time is ${t}, sir.`;
    }
    if (['what date', 'the date', "today's date", 'todays date', 'what day'].some(k => command.includes(k))) {
        const d = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        return `Today is ${d}, sir.`;
    }

    // Identity
    if (['who are you', 'what are you', 'introduce yourself'].some(k => command.includes(k))) {
        return "I am Jarvis, your personal AI assistant. Modeled after Tony Stark's companion system. I am here to serve, sir.";
    }
    if (['how are you', "how's it going", 'how do you do'].some(k => command.includes(k))) {
        return "All systems are operating at peak efficiency, sir. Thank you for asking.";
    }

    // Clear
    if (['clear history', 'forget everything', 'reset memory'].some(k => command.includes(k))) {
        conversationHistory = [];
        messagesContainer.innerHTML = '';
        return "Conversation history cleared, sir. Fresh start.";
    }

    return null; // No match
}

async function processCommand(text) {
    const command = text.toLowerCase().trim();
    if (!command) return;

    addMessage('You', text);

    // Try hardcoded actions
    const result = executeAction(command);

    if (result) {
        setOrbState('speaking');
        addMessage('JARVIS', result);
        speak(result);
    } else {
        // GPT fallback
        setOrbState('thinking');
        addMessage('JARVIS', 'Processing, sir...');
        const gptResponse = await askGPT(command);
        setOrbState('speaking');
        addMessage('JARVIS', gptResponse);
        speak(gptResponse);
    }
}


// ============================================================
//  TEXT INPUT
// ============================================================
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');

function sendTextCommand() {
    const text = textInput.value.trim();
    if (!text) return;
    textInput.value = '';
    processCommand(text);
}

textInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); sendTextCommand(); }
});
sendBtn.addEventListener('click', sendTextCommand);


// ============================================================
//  SPEECH RECOGNITION (Web Speech API)
// ============================================================
const micBtn = document.getElementById('mic-btn');
let isListening = false;

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        micBtn.classList.remove('active');
        isListening = false;
        processCommand(text);
    };

    recognition.onerror = (event) => {
        micBtn.classList.remove('active');
        isListening = false;
        setOrbState('idle');
        if (event.error !== 'no-speech') {
            addMessage('JARVIS', `Voice recognition error: ${event.error}. Please try again, sir.`);
        } else {
            addMessage('JARVIS', "I didn't catch that, sir. Please try again.");
        }
    };

    recognition.onend = () => {
        micBtn.classList.remove('active');
        isListening = false;
    };

    document.getElementById('ears-status').textContent = 'Ready';
    document.getElementById('ears-status').style.color = 'var(--accent-green)';
} else {
    document.getElementById('ears-status').textContent = 'Unavailable';
    document.getElementById('ears-status').style.color = 'var(--accent-red)';
}

micBtn.addEventListener('click', () => {
    if (!recognition) {
        addMessage('JARVIS', 'Voice recognition is not supported in this browser, sir. Please use Chrome or Edge.');
        return;
    }
    if (isListening) {
        recognition.stop();
        return;
    }
    isListening = true;
    micBtn.classList.add('active');
    setOrbState('listening');
    recognition.start();
});


// ============================================================
//  QUICK ACTION BUTTONS
// ============================================================
document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const cmd = btn.dataset.cmd;
        if (!cmd) return;
        btn.style.transform = 'scale(0.95)';
        setTimeout(() => btn.style.transform = '', 150);
        processCommand(cmd);
    });
});


// ============================================================
//  SETTINGS
// ============================================================
document.getElementById('voice-toggle').addEventListener('change', e => {
    voiceEnabled = e.target.checked;
    addMessage('JARVIS', `Voice output ${voiceEnabled ? 'enabled' : 'disabled'}, sir.`);
});

// API Key Modal
const apikeyModal = document.getElementById('apikey-modal');
const apikeyInput = document.getElementById('apikey-input');

document.getElementById('apikey-btn').addEventListener('click', () => {
    apikeyInput.value = apiKey;
    apikeyModal.style.display = 'flex';
});

document.getElementById('apikey-save').addEventListener('click', () => {
    apiKey = apikeyInput.value.trim();
    localStorage.setItem('jarvis_openai_key', apiKey);
    apikeyModal.style.display = 'none';
    updateBrainStatus();
    if (apiKey) {
        addMessage('JARVIS', 'API key saved. GPT brain is now online, sir.');
    } else {
        addMessage('JARVIS', 'API key removed. GPT brain is offline, sir.');
    }
});

document.getElementById('apikey-cancel').addEventListener('click', () => {
    apikeyModal.style.display = 'none';
});

apikeyModal.addEventListener('click', e => {
    if (e.target === apikeyModal) apikeyModal.style.display = 'none';
});


// ============================================================
//  PLATFORM DETECTION
// ============================================================
function detectPlatform() {
    const ua = navigator.userAgent;
    if (/android/i.test(ua)) return 'Android';
    if (/iPad|iPhone|iPod/.test(ua)) return 'iOS';
    if (/Windows/.test(ua)) return 'Windows';
    if (/Mac/.test(ua)) return 'macOS';
    if (/Linux/.test(ua)) return 'Linux';
    return 'Web';
}
document.getElementById('platform-info').textContent = detectPlatform();


// ============================================================
//  INIT
// ============================================================
updateBrainStatus();
