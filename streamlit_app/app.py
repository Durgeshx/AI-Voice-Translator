"""
AI Voice Translator · Gen-Z Cyberpunk Edition
=============================================
- Real-time speaker diarization + Whisper transcription (when models available)
- AI-powered summary + sentiment (Emergent Universal LLM key)
- Dual-pane WhatsApp-style chat bubbles
- Interactive Plotly analytics
- One-click PDF / TXT / JSON export
- Graceful DEMO mode when audio hardware / heavy models absent
"""
from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from ai_utils import (
    ai_summary,
    ai_translate,
    analyze_sentiment_batch,
    stream_ai_summary,
    _has_key,
)
from analytics import (
    bar_messages_per_speaker,
    donut_talking_share,
    line_sentiment_over_time,
    metric_strip,
)
from audio_utils import (
    build_demo_history,
    capabilities,
    fix_transcription,
    process_audio,
    record_microphone,
)
from db import clear_history, init_db, load_history, save_history
from exports import to_json, to_pdf, to_txt
from styles import inject_css, render_empty, render_hero, render_section, render_waveform, speaker_style

load_dotenv(Path(__file__).parent / ".env")

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Voice Translator · Gen-Z Edition",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
init_db()


# ──────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "running" not in st.session_state:
    st.session_state.running = False
if "known_speakers" not in st.session_state:
    st.session_state.known_speakers = []
if "last_summary" not in st.session_state:
    st.session_state.last_summary = ""
if "speaker_names" not in st.session_state:
    st.session_state.speaker_names = {}


def display_name(speaker_id: str) -> str:
    """Resolve raw speaker id → user-friendly name (if renamed)."""
    return st.session_state.speaker_names.get(speaker_id, speaker_id) or speaker_id


def apply_names(history: list[dict]) -> list[dict]:
    """Return a copy of history with speaker replaced by display name."""
    return [
        {**h, "speaker": display_name(h["speaker"]), "raw_speaker": h["speaker"]}
        for h in history
    ]


LANGUAGES = {
    "hi": "Hindi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "zh-CN": "Chinese (Simplified)",
    "ar": "Arabic",
    "pt": "Portuguese",
    "ru": "Russian",
    "ko": "Korean",
}


# ──────────────────────────────────────────────────────────────
# TRANSLATION WRAPPER
# ──────────────────────────────────────────────────────────────
def translate(text: str, target_code: str) -> str:
    """Try deep-translator first (fast, free), fall back to LLM."""
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="auto", target=target_code).translate(text) or ""
    except Exception:
        return ai_translate(text, LANGUAGES.get(target_code, target_code)) or "[translation unavailable]"


# ──────────────────────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────────────────────
speakers_set = {display_name(h["speaker"]) for h in st.session_state.history}
status = "LIVE" if st.session_state.running else "IDLE"
render_hero(
    total_messages=len(st.session_state.history),
    total_speakers=len(speakers_set),
    status=status,
)


# ──────────────────────────────────────────────────────────────
# CONTROL PANEL
# ──────────────────────────────────────────────────────────────
render_section("◆", "Control Deck", testid="control-deck")

col_a, col_b, col_c = st.columns([1.2, 1.2, 1])
with col_a:
    lang_code = st.selectbox(
        "Target Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda k: f"{k.upper()} · {LANGUAGES[k]}",
        key="lang_select",
    )
with col_b:
    mode = st.radio(
        "Input Mode",
        ["◉ Record Microphone", "▲ Upload Audio", "◆ Demo Mode"],
        horizontal=True,
        key="mode_radio",
    )
with col_c:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹 Reset Session", key="reset-btn", use_container_width=True):
        st.session_state.history = []
        st.session_state.running = False
        st.session_state.known_speakers = []
        st.session_state.last_summary = ""
        st.rerun()

caps = capabilities()
cap_bits = []
cap_bits.append(("MIC", caps["microphone"]))
cap_bits.append(("WHISPER", caps["whisper"]))
cap_bits.append(("DIARIZATION", caps["diarization"]))
cap_bits.append(("LLM KEY", _has_key()))
badges = "".join(
    f'<span class="vt-speaker-chip"><span class="swatch" style="background:{"#7DFFC3" if ok else "#FF5A5F"};color:{"#7DFFC3" if ok else "#FF5A5F"};"></span>{name}</span>'
    for name, ok in cap_bits
)
st.markdown(f'<div style="margin:8px 0 4px 0;">{badges}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# MODE HANDLERS
# ──────────────────────────────────────────────────────────────
if mode == "◉ Record Microphone":
    if not caps["microphone"]:
        st.markdown(
            '<div class="vt-card" style="border-color:rgba(255,90,95,0.4);background:rgba(255,90,95,0.06);">'
            '<b style="color:#FCA5A5;">Microphone unavailable in this environment.</b><br>'
            '<span style="color:var(--text-mute);font-size:13px;">Install <code>sounddevice</code>, '
            '<code>soundfile</code> and run locally. Meanwhile switch to <b>Demo Mode</b> to explore the UI.</span>'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        c1, c2 = st.columns(2)
        with c1:
            chunk = st.slider("Recording Chunk (s)", 4, 20, 8, key="chunk-slider")
        with c2:
            threshold = st.slider("Silence Threshold", 0.001, 0.050, 0.010, step=0.001, key="silence-slider")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("▶ Start Live Translation", key="start-live", use_container_width=True):
                st.session_state.running = True
                st.rerun()
        with b2:
            if st.button("⏹ Stop", key="stop-live", use_container_width=True):
                st.session_state.running = False
                st.rerun()

        render_waveform(active=st.session_state.running)

        if st.session_state.running:
            try:
                audio_path, vol = record_microphone(seconds=chunk)
                if vol < threshold:
                    st.warning(f"◇ Silence detected (rms={vol:.4f}). Skipping.")
                    time.sleep(0.4)
                    st.rerun()
                with st.spinner("Processing audio · diarizing · translating…"):
                    new = process_audio(audio_path, lang_code, translate)
                if new:
                    sentiments = analyze_sentiment_batch([n["english"] for n in new])
                    for item, (lab, sc) in zip(new, sentiments):
                        item["sentiment"] = lab
                        item["score"] = sc
                    st.session_state.history.extend(new)
                time.sleep(0.4)
                st.rerun()
            except Exception as e:
                st.error(f"Recording error: {e}")
                st.session_state.running = False

elif mode == "▲ Upload Audio":
    if not caps["whisper"]:
        st.markdown(
            '<div class="vt-card" style="border-color:rgba(255,184,0,0.4);background:rgba(255,184,0,0.06);">'
            '<b style="color:#FDE68A;">Whisper model not installed.</b><br>'
            '<span style="color:var(--text-mute);font-size:13px;">Uncomment the heavy AI packages in <code>requirements.txt</code> '
            'and reinstall to enable local transcription. Try <b>Demo Mode</b> in the meantime.</span>'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        upl = st.file_uploader("Drop a WAV / MP3 / M4A file", type=["wav", "mp3", "m4a"], key="upl")
        if upl is not None:
            ext = upl.name.split(".")[-1]
            path = str(Path(__file__).parent / f"_uploaded.{ext}")
            with open(path, "wb") as f:
                f.write(upl.read())
            st.success(f"◆ Uploaded: {upl.name}")

            if st.button("▶ Process Uploaded File", key="process-upload"):
                with st.spinner("Transcribing · diarizing · translating…"):
                    new = process_audio(path, lang_code, translate)
                sentiments = analyze_sentiment_batch([n["english"] for n in new])
                for item, (lab, sc) in zip(new, sentiments):
                    item["sentiment"] = lab
                    item["score"] = sc
                st.session_state.history.extend(new)
                st.rerun()

else:  # Demo mode
    st.markdown(
        '<div class="vt-card" style="border-color:rgba(0,229,255,0.3);background:rgba(0,229,255,0.05);">'
        '<b style="color:#67E8F9;">◆ Demo Mode</b><br>'
        '<span style="color:var(--text-mute);font-size:13px;">Loads a realistic bilingual sample so you can '
        'explore the full UI without hardware. Sentiment is computed via LLM if key is configured.</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("◆ Load Demo Conversation", key="demo-btn"):
        demo = build_demo_history(LANGUAGES.get(lang_code, "Hindi"))
        with st.spinner("Scoring sentiment via LLM…"):
            sentiments = analyze_sentiment_batch([d["english"] for d in demo])
            for item, (lab, sc) in zip(demo, sentiments):
                item["sentiment"] = lab
                item["score"] = sc
        st.session_state.history = demo
        st.rerun()


# ──────────────────────────────────────────────────────────────
# SPEAKER RENAME PANEL
# ──────────────────────────────────────────────────────────────
raw_speakers_in_history = list(dict.fromkeys(h["speaker"] for h in st.session_state.history))
if raw_speakers_in_history:
    with st.expander(f"◐ Rename Speakers ({len(raw_speakers_in_history)} detected)", expanded=False):
        st.markdown(
            '<div style="font-size:12px;color:var(--text-mute);font-family:JetBrains Mono,monospace;'
            'letter-spacing:0.08em;margin-bottom:10px;">'
            "GIVE EACH SPEAKER A HUMAN NAME · APPLIED ACROSS BUBBLES · ANALYTICS · SUMMARY · EXPORTS"
            "</div>",
            unsafe_allow_html=True,
        )
        rename_cols = st.columns(min(len(raw_speakers_in_history), 4))
        for i, raw in enumerate(raw_speakers_in_history):
            with rename_cols[i % len(rename_cols)]:
                new_name = st.text_input(
                    raw,
                    value=st.session_state.speaker_names.get(raw, ""),
                    key=f"rename-{raw}",
                    placeholder=f"e.g. {'Alice' if i == 0 else 'Bob' if i == 1 else f'Speaker {i+1}'}",
                    label_visibility="visible",
                )
                clean = (new_name or "").strip()
                if clean:
                    st.session_state.speaker_names[raw] = clean
                elif raw in st.session_state.speaker_names:
                    del st.session_state.speaker_names[raw]
        rc1, rc2 = st.columns([1, 3])
        with rc1:
            if st.button("↺ Reset Names", key="reset-names", use_container_width=True):
                st.session_state.speaker_names = {}
                st.rerun()


# ──────────────────────────────────────────────────────────────
# TOP METRICS
# ──────────────────────────────────────────────────────────────
strip = metric_strip(st.session_state.history)
named_history = apply_names(st.session_state.history)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Messages", len(st.session_state.history))
m2.metric("Total Words", strip["total_words"])
m3.metric("Avg Words / Msg", strip["avg_words"])
m4.metric(
    "Positivity Index",
    f"{strip['positivity']:+.2f}",
    delta="Good" if strip["positivity"] > 0.15 else "Tense" if strip["positivity"] < -0.15 else "Neutral",
)


# ──────────────────────────────────────────────────────────────
# ANALYTICS
# ──────────────────────────────────────────────────────────────
render_section("▲", "Conversation Analytics", testid="analytics-section")

if not st.session_state.history:
    render_empty(
        "No analytics yet",
        "Load a demo conversation or record from the microphone to unlock live charts.",
        icon="▲",
    )
else:
    ac1, ac2 = st.columns([1.2, 1])
    with ac1:
        st.plotly_chart(donut_talking_share(named_history), use_container_width=True)
    with ac2:
        st.plotly_chart(bar_messages_per_speaker(named_history), use_container_width=True)
    st.plotly_chart(line_sentiment_over_time(named_history), use_container_width=True)


# ──────────────────────────────────────────────────────────────
# AI SUMMARY
# ──────────────────────────────────────────────────────────────
render_section("◇", "AI Conversation Summary", testid="summary-section")

if not st.session_state.history:
    render_empty("No summary yet", "Once messages arrive, GPT-5.4 will synthesize an executive brief.", icon="◇")
else:
    sc1, sc2 = st.columns([3, 1])
    with sc2:
        gen_clicked = st.button("↻ Stream Summary", key="gen-summary", use_container_width=True)
    with sc1:
        if gen_clicked:
            st.markdown(
                '<div class="vt-card" data-testid="summary-card" style="animation:fadeUp .3s ease;">',
                unsafe_allow_html=True,
            )
            placeholder = st.empty()
            streamed = placeholder.write_stream(stream_ai_summary(named_history))
            st.markdown("</div>", unsafe_allow_html=True)
            st.session_state.last_summary = streamed if isinstance(streamed, str) else "".join(streamed)
        elif st.session_state.last_summary:
            st.markdown(
                f'<div class="vt-card" data-testid="summary-card">{st.session_state.last_summary}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="vt-empty" data-testid="summary-empty"><h4>Ready to stream</h4>'
                '<p>Click <b>Stream Summary</b> — GPT-5.4 will write out TL;DR, key topics, speaker highlights, '
                'sentiment vibe and action items token-by-token.</p></div>',
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────
# EXPORT ROW
# ──────────────────────────────────────────────────────────────
render_section("↓", "Instant Exports", testid="export-section")

if not st.session_state.history:
    render_empty("Nothing to export yet", "Exports unlock as soon as your first message lands.", icon="↓")
else:
    ec1, ec2, ec3, ec4 = st.columns(4)
    with ec1:
        st.download_button(
            "📄 Download PDF",
            data=to_pdf(named_history),
            file_name=f"voice-translator-{datetime.now().strftime('%Y%m%d-%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="dl-pdf",
        )
    with ec2:
        st.download_button(
            "📝 Download TXT",
            data=to_txt(named_history),
            file_name=f"voice-translator-{datetime.now().strftime('%Y%m%d-%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="dl-txt",
        )
    with ec3:
        st.download_button(
            "◆ Download JSON",
            data=to_json(named_history),
            file_name=f"voice-translator-{datetime.now().strftime('%Y%m%d-%H%M')}.json",
            mime="application/json",
            use_container_width=True,
            key="dl-json",
        )
    with ec4:
        if st.button("💾 Save to History DB", key="save-db", use_container_width=True):
            n = save_history(named_history)
            st.success(f"Saved {n} new message(s) to local DB.")


# ──────────────────────────────────────────────────────────────
# DUAL-PANE CHAT
# ──────────────────────────────────────────────────────────────
render_section("◈", "Live Conversation · Dual Pane", testid="conversation-section")

if not st.session_state.history:
    render_empty(
        "No conversation yet",
        "Start recording, upload an audio file, or load Demo Mode to see color-coded, dual-pane bubbles here.",
        icon="◈",
    )
else:
    known = st.session_state.known_speakers
    target_name = LANGUAGES.get(lang_code, lang_code.upper())
    for idx, item in enumerate(st.session_state.history[-30:]):
        raw_sp = item["speaker"]
        sp = display_name(raw_sp)
        sty = speaker_style(raw_sp, known)
        sentiment = item.get("sentiment", "NEU").upper()
        score = item.get("score", 0.0)
        sent_class = "pos" if sentiment == "POS" else "neg" if sentiment == "NEG" else "neu"
        ts = datetime.now().strftime("%H:%M")

        speaker_chip = (
            f'<span class="vt-speaker-chip" style="color:{sty["chip"]};">'
            f'<span class="swatch" style="background:{sty["chip"]};color:{sty["chip"]};"></span>{sp}</span>'
        )
        sentiment_pill = f'<span class="vt-sentiment {sent_class}">{sentiment} · {score:+.2f}</span>'

        st.markdown(
            f"""
<div class="vt-chat-row" data-testid="chat-row-{idx}">
    <div class="vt-bubble original">
        <div class="vt-bubble-header">
            {speaker_chip}
            <span class="vt-bubble-label">EN · Original</span>
            <span class="vt-bubble-time">{ts}</span>
        </div>
        <div class="vt-bubble-text">{item['english']}</div>
        <div style="margin-top:8px;">{sentiment_pill}</div>
    </div>
    <div class="vt-bubble translated">
        <div class="vt-bubble-header">
            <span class="vt-bubble-label">{lang_code.upper()} · {target_name}</span>
            <span class="vt-bubble-time">{ts}</span>
        </div>
        <div class="vt-bubble-text">{item['translation']}</div>
        <div style="margin-top:8px;">
            <span class="vt-bubble-lang">TRANSLATION · AUTO</span>
        </div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────
# HISTORY VIEWER
# ──────────────────────────────────────────────────────────────
render_section("▣", "Conversation History", testid="history-section")

hc1, hc2 = st.columns([3, 1])
with hc1:
    search = st.text_input(
        "◇ Search",
        placeholder="Search by speaker, English text or translation…",
        key="history-search",
        label_visibility="collapsed",
    )
with hc2:
    if st.button("🗑 Clear All History", key="clear-history", use_container_width=True):
        clear_history()
        st.success("History cleared.")
        st.rerun()

rows = load_history(search=search, limit=30)
if not rows:
    render_empty("No saved conversations", "Use “Save to History DB” above to persist a session.", icon="▣")
else:
    for r in rows:
        st.markdown(
            f"""
<div class="vt-card" style="padding:16px 18px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <span class="vt-speaker-chip" style="color:#00E5FF;">
            <span class="swatch" style="background:#00E5FF;color:#00E5FF;"></span>{r['speaker']}
        </span>
        <span style="font-family:JetBrains Mono,monospace;font-size:11px;color:var(--text-mute);">{r['created_at']}</span>
    </div>
    <div style="font-size:14px;color:#F1F5F9;margin-bottom:6px;"><b style="color:#67E8F9;">EN:</b> {r['english']}</div>
    <div style="font-size:14px;color:#F1F5F9;"><b style="color:#F0ABFC;">TR:</b> {r['translation']}</div>
</div>
""",
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
<div style="margin-top:40px;padding-top:20px;border-top:1px solid rgba(255,255,255,0.08);
     text-align:center;color:var(--text-mute);font-family:JetBrains Mono,monospace;font-size:11px;
     letter-spacing:0.14em;text-transform:uppercase;">
     ◆ AI Voice Translator · Gen-Z Edition · Whisper × pyannote × GPT-5.4 ◆
</div>
""",
    unsafe_allow_html=True,
)
