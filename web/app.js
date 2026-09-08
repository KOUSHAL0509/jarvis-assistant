/* ============================================================
   JARVIS GUI — Frontend Logic
   Handles: Orb animation, Eel calls, messages, background particles
   ============================================================ */

// ============================================================
//  BACKGROUND PARTICLES
// ============================================================
(function initParticles() {
    const canvas = document.getElementById('bg-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    const PARTICLE_COUNT = 60;

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
            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                this.reset();
            }
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 195, 255, ${this.opacity})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle());
    }

    // Draw connecting lines between nearby particles
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
let orbState = 'idle'; // idle, listening, thinking, speaking
let orbTime = 0;

const ASTRA_MODE_COLORS = {
    companion: { r: 0, g: 195, b: 255 },
    vision:    { r: 157, g: 78, b: 221 },
    executive: { r: 240, g: 192, b: 64 },
    engineer:  { r: 0, g: 255, b: 136 }
};
let currentAstraModeTheme = 'companion';

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
    const baseRadius = 65;

    orbCtx.clearRect(0, 0, W, H);
    orbTime += 0.02;

    const baseColor = ASTRA_MODE_COLORS[currentAstraModeTheme] || ORB_COLORS.idle;
    const color = (orbState === 'idle' || orbState === 'speaking') ? baseColor : (ORB_COLORS[orbState] || baseColor);
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
    const ringCount = 3;
    for (let r = 0; r < ringCount; r++) {
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

    // Main orb body — radial gradient with pulse
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

    // Core bright dot
    const coreGrad = orbCtx.createRadialGradient(cx, cy, 0, cx, cy, 12);
    coreGrad.addColorStop(0, `rgba(255, 255, 255, ${0.7 * intensity})`);
    coreGrad.addColorStop(0.5, `rgba(${color.r}, ${color.g}, ${color.b}, ${0.5 * intensity})`);
    coreGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

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


// ============================================================
//  SET ORB STATE (called from Python via eel)
// ============================================================
function setOrbState(state) {
    orbState = state;
    orbLabel.textContent = state.toUpperCase();
    orbLabel.className = state;
    orbCanvas.className = state;
}
// Expose to Python
if (typeof eel !== 'undefined') {
    eel.expose(setOrbState);
}


// ============================================================
//  CLOCK
// ============================================================
function updateClock() {
    const now = new Date();
    const h = now.getHours().toString().padStart(2, '0');
    const m = now.getMinutes().toString().padStart(2, '0');
    const s = now.getSeconds().toString().padStart(2, '0');
    document.getElementById('clock').textContent = `${h}:${m}:${s}`;
}
setInterval(updateClock, 1000);
updateClock();


// ============================================================
//  MESSAGES WITH RICH FORMATTING
// ============================================================
const messagesContainer = document.getElementById('messages');

function addMessage(sender, text) {
    const div = document.createElement('div');
    const isJarvis = sender.toLowerCase() === 'jarvis';
    div.className = `message ${isJarvis ? 'jarvis-msg' : 'user-msg'}`;
    
    const formattedContent = formatMessageText(text);

    div.innerHTML = `
        <span class="msg-sender">${sender.toUpperCase()}</span>
        <div class="msg-text">${formattedContent}</div>
    `;
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatMessageText(text) {
    if (!text) return '';

    // First extract code blocks to protect them
    const codeBlocks = [];
    let placeholderText = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, lang, code) => {
        const idx = codeBlocks.length;
        codeBlocks.push({ lang, code: escapeHtml(code.trim()) });
        return `___CODE_BLOCK_${idx}___`;
    });

    // Escape HTML in the remaining text
    let escaped = escapeHtml(placeholderText);

    // Inline code: `code`
    escaped = escaped.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

    // Bold: **text**
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Markdown links: [title](url)
    escaped = escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, 
        '<a href="$2" target="_blank" rel="noopener noreferrer" class="chat-link">$1</a>');

    // Standalone URLs: https://...
    escaped = escaped.replace(/(?<!href="|">)(https?:\/\/[^\s<]+)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer" class="chat-link">$1</a>');

    // Convert newlines to <br>
    escaped = escaped.replace(/\n/g, '<br>');

    // Restore code blocks
    codeBlocks.forEach((item, idx) => {
        const langBadge = item.lang ? `<span class="code-lang">${escapeHtml(item.lang.toUpperCase())}</span>` : '';
        const blockHtml = `<div class="code-container">${langBadge}<pre class="code-block"><code>${item.code}</code></pre></div>`;
        escaped = escaped.replace(`___CODE_BLOCK_${idx}___`, blockHtml);
    });

    return escaped;
}

// Expose to Python
if (typeof eel !== 'undefined') {
    eel.expose(addMessage);
}


// ============================================================
//  UPDATE SYSTEM BAR (called from Python)
// ============================================================
function updateSystemBar(data) {
    if (data.cpu !== undefined) {
        document.getElementById('cpu-stat').textContent = `CPU: ${data.cpu}%`;
    }
    if (data.battery !== undefined) {
        document.getElementById('battery-stat').textContent = `BAT: ${data.battery}%`;
    }
    if (data.brain !== undefined) {
        const brainEl = document.getElementById('brain-status');
        brainEl.textContent = data.brain;
        if (data.brain.includes('Online')) {
            brainEl.style.color = 'var(--accent-green)';
        } else if (data.brain.includes('Active')) {
            brainEl.style.color = '#00c3ff';
        } else {
            brainEl.style.color = 'var(--accent-gold)';
        }
    }
}

if (typeof eel !== 'undefined') {
    eel.expose(updateSystemBar);
}



// ============================================================
//  TEXT INPUT — Send command on Enter
// ============================================================
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');

async function sendTextCommand() {
    const text = textInput.value.trim();
    if (!text) return;

    addMessage('You', text);
    textInput.value = '';
    setOrbState('thinking');

    if (typeof eel !== 'undefined') {
        await eel.execute_command(text)();
    } else {
        // Fallback for testing without Eel
        setTimeout(() => {
            addMessage('JARVIS', 'Eel backend is not connected. Running in preview mode.');
            setOrbState('idle');
        }, 1000);
    }
}

textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendTextCommand();
    }
});

sendBtn.addEventListener('click', sendTextCommand);


// ============================================================
//  MIC BUTTON — Toggle listening
// ============================================================
const micBtn = document.getElementById('mic-btn');
let isListening = false;

micBtn.addEventListener('click', async () => {
    if (isListening) return; // Prevent multiple clicks

    isListening = true;
    micBtn.classList.add('active');
    setOrbState('listening');

    if (typeof eel !== 'undefined') {
        await eel.start_listening()();
    } else {
        setTimeout(() => {
            addMessage('JARVIS', 'Mic test — Eel backend not connected.');
            micBtn.classList.remove('active');
            setOrbState('idle');
            isListening = false;
        }, 2000);
    }

    micBtn.classList.remove('active');
    isListening = false;
});


// ============================================================
//  QUICK ACTION BUTTONS
// ============================================================
document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const cmd = btn.dataset.cmd;
        if (!cmd) return;

        addMessage('You', cmd);
        setOrbState('thinking');

        // Add click ripple effect
        btn.style.transform = 'scale(0.95)';
        setTimeout(() => btn.style.transform = '', 150);

        if (typeof eel !== 'undefined') {
            await eel.execute_command(cmd)();
        } else {
            setTimeout(() => {
                addMessage('JARVIS', `Would execute: "${cmd}" (preview mode)`);
                setOrbState('idle');
            }, 500);
        }
    });
});


// ============================================================
//  ASTRA MODE BUTTONS
// ============================================================
document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const mode = btn.dataset.mode;
        currentAstraModeTheme = mode;
        if (typeof eel !== 'undefined') {
            await eel.set_astra_mode(mode)();
        } else {
            addMessage('JARVIS', `Switched to Astra ${mode.toUpperCase()} mode.`);
        }
    });
});


// ============================================================
//  SETTINGS TOGGLES
// ============================================================
document.getElementById('voice-toggle').addEventListener('change', (e) => {
    if (typeof eel !== 'undefined') {
        eel.toggle_voice(e.target.checked);
    }
});

document.getElementById('autolisten-toggle').addEventListener('change', (e) => {
    if (typeof eel !== 'undefined') {
        eel.toggle_autolisten(e.target.checked);
    }
});


// ============================================================
//  INIT — Fetch system status on load
// ============================================================
window.addEventListener('load', async () => {
    if (typeof eel !== 'undefined') {
        await eel.get_system_status()();
    }
});
