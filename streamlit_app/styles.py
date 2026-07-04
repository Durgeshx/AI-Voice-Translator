"""
Gen-Z Cyberpunk Glassmorphism UI for AI Voice Translator.
Deep-space palette with neon violet / electric cyan / cyber-pink accents.
"""

import streamlit as st


PALETTE = {
    "bg_deep": "#050510",
    "bg_mid": "#0B0C10",
    "bg_soft": "#12131C",
    "violet": "#B026FF",
    "violet_soft": "#8A2BE2",
    "cyan": "#00E5FF",
    "cyan_soft": "#0EA5E9",
    "pink": "#FF2E9A",
    "pink_soft": "#F72585",
    "lime": "#C6F91F",
    "text": "#F1F5F9",
    "text_mute": "#94A3B8",
    "glass": "rgba(255,255,255,0.05)",
    "glass_edge": "rgba(255,255,255,0.10)",
}


# ── Speaker → color mapping (up to 8 speakers) ──
SPEAKER_PALETTE = [
    {"name": "Neon Violet", "grad": "linear-gradient(135deg, #B026FF 0%, #6C1FCE 100%)", "glow": "#B026FF", "chip": "#B026FF"},
    {"name": "Electric Cyan", "grad": "linear-gradient(135deg, #00E5FF 0%, #0369A1 100%)", "glow": "#00E5FF", "chip": "#00E5FF"},
    {"name": "Cyber Pink", "grad": "linear-gradient(135deg, #FF2E9A 0%, #C11868 100%)", "glow": "#FF2E9A", "chip": "#FF2E9A"},
    {"name": "Toxic Lime", "grad": "linear-gradient(135deg, #C6F91F 0%, #6BA10F 100%)", "glow": "#C6F91F", "chip": "#C6F91F"},
    {"name": "Amber Solar", "grad": "linear-gradient(135deg, #FFB800 0%, #B36F00 100%)", "glow": "#FFB800", "chip": "#FFB800"},
    {"name": "Blood Coral", "grad": "linear-gradient(135deg, #FF5A5F 0%, #9F1F23 100%)", "glow": "#FF5A5F", "chip": "#FF5A5F"},
    {"name": "Ice Mint", "grad": "linear-gradient(135deg, #7DFFC3 0%, #1FAE73 100%)", "glow": "#7DFFC3", "chip": "#7DFFC3"},
    {"name": "Deep Indigo", "grad": "linear-gradient(135deg, #6366F1 0%, #312E81 100%)", "glow": "#6366F1", "chip": "#6366F1"},
]


def speaker_style(speaker_id: str, known_speakers: list[str]) -> dict:
    """Return a stable style dict per speaker id."""
    if speaker_id not in known_speakers:
        known_speakers.append(speaker_id)
    idx = known_speakers.index(speaker_id) % len(SPEAKER_PALETTE)
    return SPEAKER_PALETTE[idx]


def inject_css():
    """Inject the full Gen-Z glassmorphism theme."""
    st.markdown(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=JetBrains+Mono:wght@400;500;700&family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
:root {
    --bg-deep: #050510;
    --bg-mid: #0B0C10;
    --bg-soft: #12131C;
    --violet: #B026FF;
    --cyan: #00E5FF;
    --pink: #FF2E9A;
    --lime: #C6F91F;
    --text: #F1F5F9;
    --text-mute: #94A3B8;
    --glass: rgba(255,255,255,0.05);
    --glass-strong: rgba(255,255,255,0.08);
    --glass-edge: rgba(255,255,255,0.12);
    --radius: 16px;
    --radius-lg: 22px;
}

/* Base */
html, body, [class*="css"], .stApp, .main {
    font-family: 'Manrope', -apple-system, sans-serif !important;
    color: var(--text) !important;
}
.stApp {
    background:
      radial-gradient(1200px 800px at 15% -10%, rgba(176,38,255,0.18), transparent 60%),
      radial-gradient(900px 600px at 90% 10%, rgba(0,229,255,0.12), transparent 60%),
      radial-gradient(700px 500px at 60% 100%, rgba(255,46,154,0.15), transparent 60%),
      linear-gradient(180deg, #050510 0%, #0B0C10 50%, #050510 100%);
    background-attachment: fixed;
    min-height: 100vh;
}
/* subtle grain */
.stApp::before {
    content: "";
    position: fixed; inset: 0;
    background-image:
      url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence baseFrequency='0.9' numOctaves='2' seed='7'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.06 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
    opacity: .35;
    pointer-events: none;
    mix-blend-mode: overlay;
    z-index: 0;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 5rem; max-width: 1300px;}

/* Headings */
h1, h2, h3, h4 {
    font-family: 'Bricolage Grotesque', sans-serif !important;
    letter-spacing: -0.02em;
    color: var(--text) !important;
    font-weight: 700 !important;
}
h1 { font-size: 2.5rem !important; }
h2 { font-size: 1.6rem !important; }
h3 { font-size: 1.2rem !important; }

/* Hero */
.vt-hero {
    position: relative;
    padding: 42px 46px;
    border-radius: 28px;
    background:
      linear-gradient(135deg, rgba(176,38,255,0.22) 0%, rgba(0,229,255,0.08) 40%, rgba(255,46,154,0.18) 100%),
      rgba(255,255,255,0.03);
    backdrop-filter: blur(24px) saturate(140%);
    -webkit-backdrop-filter: blur(24px) saturate(140%);
    border: 1px solid var(--glass-edge);
    box-shadow:
       0 30px 80px rgba(0,0,0,0.55),
       inset 0 1px 0 rgba(255,255,255,0.08);
    margin-bottom: 32px;
    overflow: hidden;
}
.vt-hero::after {
    content: "";
    position: absolute; inset: -1px;
    border-radius: 28px;
    background: linear-gradient(120deg, transparent 30%, rgba(255,255,255,0.06) 50%, transparent 70%);
    pointer-events: none;
    animation: shimmer 8s linear infinite;
}
@keyframes shimmer {
    0% { transform: translateX(-60%); }
    100% { transform: translateX(60%); }
}
.vt-hero-badge {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 14px;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--glass-edge);
    border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--cyan);
    text-transform: uppercase;
    letter-spacing: 0.16em;
    margin-bottom: 18px;
}
.vt-hero-badge .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--cyan);
    box-shadow: 0 0 12px var(--cyan);
    animation: pulse 1.6s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1);}
    50% { opacity: 0.5; transform: scale(0.85);}
}
.vt-hero-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.02;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #FFFFFF 0%, #C084FC 45%, #00E5FF 100%);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 12px 0;
}
.vt-hero-sub {
    font-size: 1.05rem;
    color: var(--text-mute);
    max-width: 720px;
    line-height: 1.55;
}
.vt-hero-stats {
    display: flex; gap: 16px; flex-wrap: wrap; margin-top: 22px;
}
.vt-hero-stat {
    padding: 10px 16px;
    border-radius: 12px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--glass-edge);
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-mute);
}
.vt-hero-stat b { color: var(--text); font-weight: 700;}

/* Glass card */
.vt-card {
    background: var(--glass);
    backdrop-filter: blur(16px) saturate(140%);
    -webkit-backdrop-filter: blur(16px) saturate(140%);
    border: 1px solid var(--glass-edge);
    border-radius: var(--radius);
    padding: 20px 22px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.35);
    transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
    margin-bottom: 14px;
}
.vt-card:hover {
    transform: translateY(-2px);
    border-color: rgba(255,255,255,0.20);
    box-shadow: 0 16px 60px rgba(0,0,0,0.45);
}

/* Section header */
.vt-section {
    display: flex; align-items: center; gap: 12px;
    margin: 28px 0 14px 0;
}
.vt-section-icon {
    width: 36px; height: 36px; border-radius: 12px;
    background: linear-gradient(135deg, var(--violet), var(--pink));
    display: grid; place-items: center;
    box-shadow: 0 6px 22px rgba(176,38,255,0.35);
    font-size: 18px;
}
.vt-section-title {
    font-family: 'Bricolage Grotesque', sans-serif;
    font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em;
    color: var(--text);
}
.vt-section-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, var(--glass-edge), transparent);
}

/* Streamlit primary buttons */
div.stButton > button, div.stDownloadButton > button {
    border-radius: var(--radius) !important;
    padding: 12px 22px !important;
    font-weight: 700 !important;
    font-family: 'Manrope', sans-serif !important;
    letter-spacing: 0.01em;
    border: 1px solid rgba(255,255,255,0.15) !important;
    background: linear-gradient(135deg, #B026FF 0%, #6C1FCE 100%) !important;
    color: #fff !important;
    box-shadow: 0 8px 30px rgba(176,38,255,0.35), inset 0 1px 0 rgba(255,255,255,0.15) !important;
    transition: transform .18s ease, box-shadow .18s ease, filter .18s ease !important;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.12);
    box-shadow: 0 14px 40px rgba(176,38,255,0.5), inset 0 1px 0 rgba(255,255,255,0.2) !important;
}
div.stButton > button:active { transform: translateY(0); }

/* Inputs (selectbox, text input, slider) */
.stSelectbox > div > div, .stTextInput > div > div > input, .stTextArea textarea, .stFileUploader > section {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid var(--glass-edge) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
}
.stSelectbox svg { color: var(--text-mute) !important; }
.stTextInput > div > div > input::placeholder { color: var(--text-mute) !important; }

/* Slider */
.stSlider [data-baseweb="slider"] > div > div > div > div {
    background: linear-gradient(90deg, var(--violet), var(--cyan)) !important;
    box-shadow: 0 0 12px rgba(176,38,255,0.6);
}
.stSlider [role="slider"] {
    background: #fff !important;
    box-shadow: 0 0 0 4px rgba(176,38,255,0.4), 0 6px 20px rgba(0,0,0,0.4) !important;
}

/* Radio pills */
div[role="radiogroup"] > label {
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--glass-edge);
    border-radius: 12px;
    padding: 8px 14px;
    margin-right: 8px;
    transition: all .2s ease;
}
div[role="radiogroup"] > label:hover {
    border-color: var(--violet);
    background: rgba(176,38,255,0.08);
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--glass);
    backdrop-filter: blur(14px);
    border: 1px solid var(--glass-edge);
    border-radius: var(--radius);
    padding: 18px 20px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.28);
}
[data-testid="stMetricLabel"] {
    color: var(--text-mute) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: var(--text) !important;
    font-family: 'Bricolage Grotesque', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #FFFFFF, #C084FC);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Alert / info boxes */
div[data-testid="stAlert"], .stAlert {
    background: rgba(0,229,255,0.06) !important;
    border: 1px solid rgba(0,229,255,0.25) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
}
div[data-testid="stAlert"] p { color: var(--text) !important; }

/* Chat bubbles (dual-pane) */
.vt-chat-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    align-items: start;
    margin: 12px 0;
    animation: fadeUp .4s ease;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px);}
    to { opacity: 1; transform: translateY(0);}
}
.vt-bubble {
    padding: 14px 16px;
    border-radius: var(--radius);
    border: 1px solid var(--glass-edge);
    backdrop-filter: blur(12px);
    position: relative;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
.vt-bubble.original {
    background: linear-gradient(135deg, rgba(0,229,255,0.10), rgba(14,165,233,0.06));
    border-color: rgba(0,229,255,0.30);
}
.vt-bubble.translated {
    background: linear-gradient(135deg, rgba(176,38,255,0.14), rgba(255,46,154,0.08));
    border-color: rgba(176,38,255,0.35);
}
.vt-bubble-header {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}
.vt-bubble-label {
    padding: 3px 8px;
    border-radius: 999px;
    background: rgba(255,255,255,0.08);
    color: var(--text-mute);
    font-weight: 600;
}
.vt-bubble.original .vt-bubble-label { color: var(--cyan); border: 1px solid rgba(0,229,255,0.3); }
.vt-bubble.translated .vt-bubble-label { color: #F0ABFC; border: 1px solid rgba(176,38,255,0.4); }
.vt-bubble-time { color: var(--text-mute); font-family: 'JetBrains Mono', monospace; font-size: 10px; margin-left: auto; }
.vt-bubble-text { font-size: 15px; line-height: 1.55; color: var(--text); font-weight: 500; }
.vt-bubble-lang {
    display: inline-block; padding: 2px 8px; margin-left: auto;
    background: rgba(255,255,255,0.08);
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    color: var(--text-mute);
}

/* Speaker chip */
.vt-speaker-chip {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--glass-edge);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-right: 8px;
}
.vt-speaker-chip .swatch {
    width: 10px; height: 10px; border-radius: 50%;
    box-shadow: 0 0 8px currentColor;
}

/* Sentiment pill */
.vt-sentiment {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    margin-left: 6px;
}
.vt-sentiment.pos { background: rgba(34,197,94,0.15); color: #86EFAC; border: 1px solid rgba(34,197,94,0.35);}
.vt-sentiment.neg { background: rgba(239,68,68,0.15); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.35);}
.vt-sentiment.neu { background: rgba(148,163,184,0.15); color: #CBD5E1; border: 1px solid rgba(148,163,184,0.35);}

/* Recording indicator with glow */
.vt-rec {
    display: inline-flex; align-items: center; gap: 12px;
    padding: 12px 18px;
    background: rgba(255,46,154,0.10);
    border: 1px solid rgba(255,46,154,0.35);
    border-radius: var(--radius);
    color: #FFB4D6;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    animation: recGlow 2s ease-in-out infinite;
}
.vt-rec .dot {
    width: 12px; height: 12px; border-radius: 50%;
    background: #FF2E9A;
    box-shadow: 0 0 14px #FF2E9A;
    animation: pulse 1s ease-in-out infinite;
}
@keyframes recGlow {
    0%, 100% { box-shadow: 0 0 0 rgba(255,46,154,0.0); }
    50% { box-shadow: 0 0 42px rgba(255,46,154,0.35); }
}

/* Waveform bars */
.vt-wave { display: flex; align-items: flex-end; gap: 4px; height: 90px; padding: 0 12px; }
.vt-wave .bar {
    flex: 1; min-width: 3px;
    background: linear-gradient(180deg, var(--violet) 0%, var(--pink) 100%);
    border-radius: 4px;
    box-shadow: 0 0 12px rgba(176,38,255,0.6);
    animation: wave 1.2s ease-in-out infinite;
}
@keyframes wave {
    0%, 100% { height: 20%; }
    50% { height: 100%; }
}

/* Export row */
.vt-export-row {
    display: flex; gap: 10px; flex-wrap: wrap;
    padding: 6px 0 4px;
}

/* Empty state */
.vt-empty {
    text-align: center; padding: 40px 20px;
    color: var(--text-mute);
    background: var(--glass);
    border: 1px dashed var(--glass-edge);
    border-radius: var(--radius);
}
.vt-empty h4 { color: var(--text); margin: 0 0 6px 0; font-family: 'Bricolage Grotesque', sans-serif;}
.vt-empty p { margin: 0; font-size: 14px; }

/* Custom scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--violet), var(--pink));
    border-radius: 8px;
}

/* Divider */
hr { border: none; border-top: 1px solid var(--glass-edge); margin: 24px 0; }

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--violet), var(--cyan)) !important;
}

/* Selection */
::selection { background: rgba(176,38,255,0.4); color: #fff; }
</style>
""",
        unsafe_allow_html=True,
    )


def render_hero(total_messages: int, total_speakers: int, status: str):
    dot_color = "#FF2E9A" if status == "LIVE" else "#00E5FF"
    status_label = "● LIVE SESSION" if status == "LIVE" else "● IDLE · READY"
    st.markdown(
        f"""
<div class="vt-hero" data-testid="hero-section">
    <div class="vt-hero-badge"><span class="dot" style="background:{dot_color};box-shadow:0 0 12px {dot_color};"></span> {status_label}</div>
    <div class="vt-hero-title">AI Voice<br>Translator<span style="color:var(--cyan);">.</span></div>
    <div class="vt-hero-sub">
        Real-time speaker diarization, transcription and multilingual translation —
        wrapped in a Gen-Z dark aesthetic with AI-powered analytics, sentiment scoring and one-click exports.
    </div>
    <div class="vt-hero-stats">
        <div class="vt-hero-stat">MESSAGES · <b>{total_messages}</b></div>
        <div class="vt-hero-stat">SPEAKERS · <b>{total_speakers}</b></div>
        <div class="vt-hero-stat">STATUS · <b style="color:{dot_color};">{status}</b></div>
        <div class="vt-hero-stat">MODEL · <b>WHISPER + GPT-5.4</b></div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_section(icon: str, title: str, testid: str = ""):
    st.markdown(
        f"""
<div class="vt-section" {f'data-testid="{testid}"' if testid else ''}>
    <div class="vt-section-icon">{icon}</div>
    <div class="vt-section-title">{title}</div>
    <div class="vt-section-line"></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_waveform(active: bool = False):
    if active:
        bars = "".join(
            f'<div class="bar" style="animation-delay:{i*0.08:.2f}s;height:{20+(i*7)%80}%;"></div>'
            for i in range(48)
        )
        st.markdown(
            f'<div class="vt-card" style="padding:14px;"><div class="vt-rec"><span class="dot"></span>RECORDING · MIC LIVE</div>'
            f'<div class="vt-wave">{bars}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        bars = "".join(
            f'<div class="bar" style="animation-play-state:paused;opacity:0.25;height:{18+(i*11)%70}%;"></div>'
            for i in range(48)
        )
        st.markdown(
            f'<div class="vt-card" style="padding:14px;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:11px;letter-spacing:0.16em;color:var(--text-mute);text-transform:uppercase;margin-bottom:10px;">◆ MIC INPUT · IDLE</div>'
            f'<div class="vt-wave">{bars}</div></div>',
            unsafe_allow_html=True,
        )


def render_empty(title: str, subtitle: str, icon: str = "◇"):
    st.markdown(
        f"""
<div class="vt-empty">
    <div style="font-size:34px;margin-bottom:8px;">{icon}</div>
    <h4>{title}</h4>
    <p>{subtitle}</p>
</div>
""",
        unsafe_allow_html=True,
    )
