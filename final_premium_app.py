import os
import time
import sqlite3
from datetime import datetime
import html

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None

import librosa
import torch

from pyannote.audio import Pipeline
from deep_translator import GoogleTranslator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# =========================
# CONFIG
# =========================

# Speaker diarization ke liye HuggingFace token optional hai.
# Fast Upload Mode aur normal transcription iske bina bhi chalega.
HF_TOKEN = os.getenv("HF_TOKEN", "YOUR_HUGGINGFACE_TOKEN")

DB_FILE = "conversation_history.db"

st.set_page_config(
    page_title="AI Voice Translator",
    layout="wide"
)


# =========================
# CSS
# =========================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

.stApp {
    background:
        radial-gradient(circle at top left, rgba(168,85,247,0.25), transparent 35%),
        radial-gradient(circle at top right, rgba(6,182,212,0.22), transparent 35%),
        linear-gradient(135deg, #020617 0%, #0f172a 45%, #111827 100%);
    color: #f8fafc;
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 28px;
    padding-left: 36px;
    padding-right: 36px;
    max-width: 1500px;
}

.hero {
    padding: 34px;
    border-radius: 26px;
    background: linear-gradient(135deg, rgba(88,28,135,0.65), rgba(15,23,42,0.82), rgba(8,47,73,0.65));
    border: 1px solid rgba(168,85,247,0.45);
    box-shadow: 0 0 45px rgba(168,85,247,0.25);
    margin-bottom: 28px;
}

.hero-badge {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 999px;
    background: rgba(15,23,42,0.75);
    border: 1px solid rgba(34,211,238,0.35);
    color: #22d3ee;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 16px;
}

.hero-title {
    font-size: 58px;
    line-height: 1.05;
    font-weight: 900;
    background: linear-gradient(90deg, #ffffff, #e879f9, #22d3ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    margin-top: 14px;
    font-size: 19px;
    color: #cbd5e1;
    max-width: 900px;
}

.neon-card {
    padding: 22px;
    border-radius: 20px;
    background: rgba(15,23,42,0.72);
    border: 1px solid rgba(148,163,184,0.18);
    box-shadow: inset 0 0 30px rgba(255,255,255,0.025), 0 12px 35px rgba(0,0,0,0.28);
    margin-bottom: 14px;
}

.metric-title {
    font-size: 13px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

.metric-value {
    font-size: 34px;
    font-weight: 900;
    margin-top: 8px;
    color: #ffffff;
}

.metric-good {
    color: #22c55e;
    font-size: 14px;
    margin-top: 6px;
}

.section-title {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-top: 30px;
    margin-bottom: 16px;
    font-size: 26px;
    font-weight: 900;
}

.section-icon {
    width: 46px;
    height: 46px;
    border-radius: 14px;
    background: linear-gradient(135deg, #a855f7, #ec4899);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 25px rgba(217,70,239,0.45);
}

.speaker-card {
    padding: 20px;
    border-radius: 20px;
    margin-bottom: 16px;
    border: 1px solid rgba(148,163,184,0.18);
    background: rgba(15,23,42,0.78);
}

.speaker-0 {
    border-color: rgba(168,85,247,0.45);
    background: linear-gradient(135deg, rgba(88,28,135,0.45), rgba(15,23,42,0.82));
}

.speaker-1 {
    border-color: rgba(34,211,238,0.45);
    background: linear-gradient(135deg, rgba(8,145,178,0.32), rgba(15,23,42,0.82));
}

.speaker-other {
    border-color: rgba(148,163,184,0.25);
    background: rgba(15,23,42,0.72);
}

.speaker-name {
    font-size: 18px;
    font-weight: 900;
    color: #e879f9;
    margin-bottom: 12px;
}

.text-label {
    color: #22d3ee;
    font-weight: 900;
}

div.stButton > button {
    border-radius: 14px;
    padding: 12px 24px;
    font-weight: 800;
    border: 1px solid rgba(168,85,247,0.45);
    background: linear-gradient(135deg, #7c3aed, #c026d3);
    color: white;
    box-shadow: 0 0 25px rgba(168,85,247,0.28);
}

div.stDownloadButton > button {
    border-radius: 14px;
    padding: 12px 24px;
    font-weight: 800;
    background: linear-gradient(135deg, #059669, #22c55e);
    color: white;
    border: 1px solid rgba(34,197,94,0.45);
}

input, textarea, select {
    border-radius: 14px !important;
}
</style>
""", unsafe_allow_html=True)


# =========================
# HERO
# =========================

st.markdown("""
<div class="hero">
    <div class="hero-badge">● IDLE · READY</div>
    <div class="hero-title">AI Voice<br>Translator.</div>
    <div class="hero-subtitle">
        Real-time speaker diarization, transcription, multilingual translation,
        AI summary, analytics, history, and one-click exports.
    </div>
</div>
""", unsafe_allow_html=True)


# =========================
# HELPER FUNCTIONS
# =========================

def clean_html(text):
    return html.escape(str(text))


def fix_transcription(text):
    corrections = {
        "Durgeesh Mali": "Durgesh Mali",
        "Durgaish Mali": "Durgesh Mali",
        "Durgaishmali": "Durgesh Mali",
        "Gashmali": "Durgesh Mali",
        "Tugeshmali": "Durgesh Mali",
        "Bokeh": "Dabok",
        "Devok": "Dabok",
        "Devoke": "Dabok",
        "AI modern": "AI model",
    }

    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    return text.strip()


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            speaker TEXT,
            english TEXT,
            translation TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_conversation_to_db(history):
    if not history:
        return

    init_db()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for item in history:
        cursor.execute("""
            SELECT id FROM conversations
            WHERE speaker = ? AND english = ? AND translation = ?
            LIMIT 1
        """, (
            item["speaker"],
            item["english"],
            item["translation"]
        ))

        existing = cursor.fetchone()

        if existing is None:
            cursor.execute("""
                INSERT INTO conversations
                (created_at, speaker, english, translation)
                VALUES (?, ?, ?, ?)
            """, (
                created_at,
                item["speaker"],
                item["english"],
                item["translation"]
            ))

    conn.commit()
    conn.close()


@st.cache_resource
def load_whisper():
    return whisper.load_model("small")


@st.cache_resource
def load_faster_whisper_upload():
    """Faster upload transcription backend. CPU int8 = stable for long files."""
    if WhisperModel is None:
        return None

    return WhisperModel(
        "base",
        device="cpu",
        compute_type="int8"
    )


@st.cache_resource
def load_pyannote():
    if not HF_TOKEN or HF_TOKEN == "YOUR_HUGGINGFACE_TOKEN":
        return None

    try:
        return Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=HF_TOKEN
        )
    except Exception:
        return None


def split_text_for_translation(text, max_chars=4000):
    chunks = []
    current = ""

    safe_text = text.replace("?", ".").replace("!", ".")

    for part in safe_text.split("."):
        part = part.strip()

        if not part:
            continue

        sentence = part + "."

        if len(current) + len(sentence) > max_chars:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
        else:
            current += " " + sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def translate_text_fast(text, language):
    if language == "en":
        return text

    translated_parts = []

    for chunk in split_text_for_translation(text):
        try:
            translated = GoogleTranslator(
                source="auto",
                target=language
            ).translate(chunk)

            translated_parts.append(translated if translated else chunk)

        except Exception:
            translated_parts.append(chunk)

    return " ".join(translated_parts).strip()


def normalize_audio(audio_data):
    if audio_data is None or len(audio_data) == 0:
        return audio_data

    audio_data = audio_data.astype(np.float32)

    max_amp = float(np.max(np.abs(audio_data)))

    if max_amp > 0:
        audio_data = audio_data / max_amp * 0.8

    return audio_data


def transcribe_numpy_audio(audio_data):
    """
    Whisper ko numpy audio pass karta hai.
    Short MP3 clips par file decoder crash avoid karne me help karta hai.
    """
    if audio_data is None or len(audio_data) == 0:
        return {"text": "", "segments": []}

    audio_data = normalize_audio(audio_data)

    try:
        result = whisper_model.transcribe(
            audio_data,
            language="en",
            task="transcribe",
            fp16=False,
            verbose=False,
            condition_on_previous_text=False,
            temperature=0
        )
        return result

    except RuntimeError as e:
        print("Whisper RuntimeError:", e)
        return {"text": "", "segments": []}

    except Exception as e:
        print("Whisper error:", e)
        return {"text": "", "segments": []}


def process_audio(audio_file, language, use_diarization=True):
    """
    Short/live audio processor.
    Diarization available hai to speaker detect karega, warna SPEAKER_00 fallback.
    """
    results = []

    try:
        audio_data, sr = librosa.load(audio_file, sr=16000, mono=True)
    except Exception as e:
        st.error(f"Audio read failed: {e}")
        return []

    if audio_data is None or len(audio_data) == 0:
        return []

    duration = len(audio_data) / sr

    # Very tiny audio ke liye padding, Whisper decoder crash avoid.
    audio_for_whisper = normalize_audio(audio_data)

    if duration < 3:
        padded_audio = np.zeros(int(30 * sr), dtype=np.float32)
        start_pos = int(1.0 * sr)
        end_pos = min(start_pos + len(audio_for_whisper), len(padded_audio))
        padded_audio[start_pos:end_pos] = audio_for_whisper[:end_pos - start_pos]
        audio_for_whisper = padded_audio

    whisper_result = transcribe_numpy_audio(audio_for_whisper)
    whisper_segments = whisper_result.get("segments", [])

    if not whisper_segments:
        text = fix_transcription(whisper_result.get("text", "").strip())
        if text:
            return [{
                "speaker": "SPEAKER_00",
                "english": text,
                "translation": translate_text_fast(text, language)
            }]
        return []

    annotation = None

    if use_diarization and duration >= 3:
        diarization_model = load_pyannote()

        if diarization_model is not None:
            try:
                waveform = torch.tensor(audio_data, dtype=torch.float32).unsqueeze(0)

                diarization = diarization_model(
                    {
                        "waveform": waveform,
                        "sample_rate": sr
                    }
                )

                annotation = (
                    diarization.speaker_diarization
                    if hasattr(diarization, "speaker_diarization")
                    else diarization
                )

            except Exception as e:
                print("Diarization skipped:", e)
                annotation = None

    for segment in whisper_segments:
        start = float(segment.get("start", 0))
        end = float(segment.get("end", start))
        english_text = fix_transcription(segment.get("text", "").strip())

        if not english_text or len(english_text) < 2:
            continue

        speaker_name = "SPEAKER_00"

        if annotation is not None:
            best_overlap = 0

            try:
                for turn, _, speaker in annotation.itertracks(yield_label=True):
                    overlap_start = max(start, turn.start)
                    overlap_end = min(end, turn.end)
                    overlap = overlap_end - overlap_start

                    if overlap > best_overlap:
                        best_overlap = overlap
                        speaker_name = speaker

            except Exception:
                speaker_name = "SPEAKER_00"

        translated_text = translate_text_fast(english_text, language)

        results.append(
            {
                "speaker": speaker_name,
                "english": english_text,
                "translation": translated_text
            }
        )

    return results


def process_uploaded_fast(audio_file, language, chunk_seconds=30):
    """
    Emergency stable upload processor.
    Uses faster-whisper for uploaded files only.
    No diarization. Best for short clips + long 8-minute audio.
    """
    final_results = []

    fast_model = load_faster_whisper_upload()

    if fast_model is None:
        st.error("faster-whisper is not installed. Run: pip install faster-whisper")
        return []

    status = st.empty()
    progress = st.progress(0)

    try:
        status.info("Fast upload engine started. Transcribing audio...")

        segments_generator, info = fast_model.transcribe(
            audio_file,
            language="en",
            task="transcribe",
            beam_size=1,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 300
            },
            condition_on_previous_text=False
        )

        segment_count = 0
        transcript_parts = []

        for segment in segments_generator:
            text = fix_transcription(segment.text.strip())

            if not text or len(text) < 2:
                continue

            segment_count += 1
            transcript_parts.append(text)

            status.info(f"Transcribed segment {segment_count}...")
            progress.progress(min(0.90, segment_count / 80))

        if not transcript_parts:
            progress.progress(1.0)
            status.warning("No clear speech found in uploaded audio.")
            return []

        # Conversation readable banane ke liye text ko sentence chunks me split karo.
        full_text = " ".join(transcript_parts).strip()
        readable_chunks = split_text_for_translation(full_text, max_chars=900)

        total = len(readable_chunks)

        for i, english_text in enumerate(readable_chunks):
            status.info(f"Translating part {i + 1} of {total}...")

            translation = translate_text_fast(english_text, language)

            final_results.append({
                "speaker": "SPEAKER_00",
                "english": english_text,
                "translation": translation
            })

            progress.progress(0.90 + (0.10 * ((i + 1) / total)))

        status.success("Fast upload processing complete.")
        progress.progress(1.0)
        return final_results

    except Exception as e:
        st.error(f"Fast upload processing failed: {e}")
        return []

def process_long_audio(audio_file, language, chunk_seconds=90):
    """
    Speaker Mode: long audio ko safe chunks me diarization ke saath process karta hai.
    Ye slow hai. Long files ke liye Fast Mode recommended hai.
    """
    all_results = []

    try:
        audio_data, sr = librosa.load(audio_file, sr=16000, mono=True)
    except Exception as e:
        st.error(f"Audio read failed: {e}")
        return []

    if audio_data is None or len(audio_data) == 0:
        st.error("Audio file empty ya unreadable hai.")
        return []

    total_samples = len(audio_data)
    chunk_size = int(chunk_seconds * sr)
    total_chunks = max(1, int(np.ceil(total_samples / chunk_size)))

    progress = st.progress(0)
    status = st.empty()

    for i in range(total_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, total_samples)

        chunk = audio_data[start:end]

        if len(chunk) < int(2 * sr):
            progress.progress((i + 1) / total_chunks)
            continue

        if float(np.max(np.abs(chunk))) < 0.0001:
            progress.progress((i + 1) / total_chunks)
            continue

        chunk_file = f"uploaded_speaker_chunk_{i}.wav"
        sf.write(chunk_file, chunk, sr)

        status.info(f"Speaker mode processing chunk {i + 1} of {total_chunks}...")

        try:
            chunk_results = process_audio(
                chunk_file,
                language,
                use_diarization=True
            )

            if chunk_results:
                all_results.extend(chunk_results)

        except Exception as e:
            st.warning(f"Chunk {i + 1} skipped.")
            print("Speaker chunk error:", e)

        progress.progress((i + 1) / total_chunks)

    status.success("Long audio processing complete.")
    return all_results


def run_live_chunk(language):
    chunk_seconds = 6
    silence_threshold = 0.003
    samplerate = 16000

    with st.spinner("🎙 Listening... speak now"):
        audio = sd.rec(
            int(chunk_seconds * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32"
        )
        sd.wait()

    volume = float(np.sqrt(np.mean(audio ** 2)))

    if volume < silence_threshold:
        st.session_state.last_live_message = "Silence detected. Listening again..."
        time.sleep(0.3)
        st.rerun()

    audio_file = "final_live_chunk.wav"
    sf.write(audio_file, audio, samplerate)

    with st.spinner("⚡ Transcribing + translating..."):
        new_results = process_audio(
            audio_file,
            language,
            use_diarization=True
        )

    if new_results:
        st.session_state.history.extend(new_results)
        st.session_state.last_live_message = f"Added {len(new_results)} new conversation line(s)."
    else:
        st.session_state.last_live_message = "No clear speech detected. Listening again..."

    time.sleep(0.2)
    st.rerun()


def calculate_analytics(history):
    analytics = {}

    for item in history:
        speaker = get_speaker_name(item["speaker"])

        if speaker not in analytics:
            analytics[speaker] = {
                "messages": 0
            }

        analytics[speaker]["messages"] += 1

    return analytics


def create_basic_summary(history):
    if not history:
        return "No conversation available to summarize."

    total_messages = len(history)
    speakers = sorted(set(get_speaker_name(item["speaker"]) for item in history))
    all_text = " ".join(item["english"] for item in history)

    summary = f"""
Conversation Summary

Total Messages: {total_messages}
Speakers Detected: {", ".join(speakers)}

Main Conversation Text:
{all_text[:800]}
"""

    return summary.strip()


def get_speaker_name(speaker):
    return st.session_state.speaker_names.get(speaker, speaker)


def show_conversation(history):
    if not history:
        st.markdown("""
        <div class="neon-card" style="text-align:center; padding:70px 20px;">
            <div style="font-size:42px; color:#94a3b8;">◇</div>
            <h2>No conversation yet</h2>
            <p style="color:#94a3b8;">
                Start recording, upload an audio file, or load demo conversation.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("""
    <div class="neon-card" style="padding:18px 22px; margin-bottom:18px;">
        <div style="
            display:grid;
            grid-template-columns:1fr 1fr;
            gap:20px;
            font-weight:900;
            font-size:18px;
        ">
            <div style="color:#e879f9;">English Original</div>
            <div style="color:#22d3ee;">Translation</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for item in history[-50:]:
        raw_speaker = item["speaker"]
        display_speaker = clean_html(get_speaker_name(raw_speaker))
        english = clean_html(item["english"])
        translation = clean_html(item["translation"])

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                <div class="speaker-card speaker-0">
                    <div class="speaker-name">{display_speaker} · English</div>
                    <div style="font-size:18px; line-height:1.7;">
                        {english}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div class="speaker-card speaker-1">
                    <div class="speaker-name" style="color:#22d3ee;">
                        {display_speaker} · Translation
                    </div>
                    <div style="font-size:18px; line-height:1.9;">
                        {translation}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


def build_transcript_text(history):
    transcript_text = ""

    for item in history:
        speaker = get_speaker_name(item["speaker"])
        transcript_text += f"{speaker}\n"
        transcript_text += f"English: {item['english']}\n"
        transcript_text += f"Translation: {item['translation']}\n"
        transcript_text += "-" * 40
        transcript_text += "\n\n"

    return transcript_text


def create_pdf_report(history):
    pdf_file = "conversation_report.pdf"

    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    y = height - 50

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "AI Voice Translator Report")

    y -= 40
    c.setFont("Helvetica", 10)

    for item in history:
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

        speaker = get_speaker_name(item["speaker"])

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, speaker[:90])
        y -= 18

        c.setFont("Helvetica", 10)
        c.drawString(50, y, "English: " + item["english"][:90])
        y -= 18

        c.drawString(50, y, "Translation: See TXT transcript for Hindi text")
        y -= 28

    c.save()

    return pdf_file


def show_history_section():
    st.markdown("---")
    st.markdown("""
    <div class="section-title">
        <div class="section-icon">📚</div>
        Conversation History
    </div>
    """, unsafe_allow_html=True)

    search_text = st.text_input(
        "🔍 Search Conversations",
        placeholder="Search by speaker, English text, or translation...",
        key="history_search_box"
    )

    if st.button("🗑 Delete All History", key="delete_history_button"):
        init_db()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM conversations")

        conn.commit()
        conn.close()

        st.success("All history deleted.")
        st.rerun()

    init_db()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if search_text:
        cursor.execute("""
            SELECT created_at, speaker, english, translation
            FROM conversations
            WHERE speaker LIKE ?
               OR english LIKE ?
               OR translation LIKE ?
            ORDER BY id DESC
        """, (
            f"%{search_text}%",
            f"%{search_text}%",
            f"%{search_text}%"
        ))
    else:
        cursor.execute("""
            SELECT created_at, speaker, english, translation
            FROM conversations
            ORDER BY id DESC
            LIMIT 20
        """)

    rows = cursor.fetchall()
    conn.close()

    if rows:
        for row in rows:
            created_at, speaker, english, translation = row

            st.markdown(
                f"""
                <div class="neon-card">
                    <b>{clean_html(created_at)}</b><br><br>
                    <b>{clean_html(speaker)}</b><br>
                    English: {clean_html(english)}<br>
                    Translation: {clean_html(translation)}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No saved conversations found.")


def load_demo_history():
    return [
        {
            "speaker": "SPEAKER_00",
            "english": "Hello, how are you today?",
            "translation": "नमस्ते, आज आप कैसे हैं?"
        },
        {
            "speaker": "SPEAKER_01",
            "english": "I am good, thank you. How about you?",
            "translation": "मैं अच्छा हूँ, धन्यवाद। आप कैसे हैं?"
        },
        {
            "speaker": "SPEAKER_00",
            "english": "I am preparing my AI Voice Translator project presentation.",
            "translation": "मैं अपने एआई वॉयस ट्रांसलेटर प्रोजेक्ट की प्रस्तुति की तैयारी कर रहा हूँ।"
        },
        {
            "speaker": "SPEAKER_01",
            "english": "That sounds amazing. It can detect speakers and translate speech in real time.",
            "translation": "यह बहुत अच्छा लगता है। यह वक्ताओं की पहचान कर सकता है और भाषण का वास्तविक समय में अनुवाद कर सकता है।"
        },
        {
            "speaker": "SPEAKER_00",
            "english": "Yes, it also saves conversation history and creates PDF reports.",
            "translation": "हाँ, यह बातचीत का इतिहास भी सहेजता है और पीडीएफ रिपोर्ट बनाता है।"
        }
    ]


# =========================
# LOAD MODELS
# =========================

with st.spinner("Loading Whisper model..."):
    whisper_model = load_whisper()


# =========================
# SESSION STATE
# =========================

if "history" not in st.session_state:
    st.session_state.history = []

if "running" not in st.session_state:
    st.session_state.running = False

if "speaker_names" not in st.session_state:
    st.session_state.speaker_names = {}

if "last_live_message" not in st.session_state:
    st.session_state.last_live_message = "Ready."


# =========================
# CONTROLS
# =========================

LANGUAGE_OPTIONS = {
    "English - EN": "en",
    "Hindi - HI": "hi",
    "Spanish - ES": "es",
    "French - FR": "fr",
    "German - DE": "de",
    "Italian - IT": "it",
    "Portuguese - PT": "pt",
    "Russian - RU": "ru",
    "Japanese - JA": "ja",
    "Korean - KO": "ko",
    "Chinese Simplified - ZH-CN": "zh-CN",
    "Arabic - AR": "ar",
    "Bengali - BN": "bn",
    "Tamil - TA": "ta",
    "Telugu - TE": "te",
    "Marathi - MR": "mr",
    "Gujarati - GU": "gu",
    "Punjabi - PA": "pa",
    "Urdu - UR": "ur",
    "Nepali - NE": "ne",
}

st.markdown("""
<div class="section-title">
    <div class="section-icon">🎛</div>
    Control Deck
</div>
""", unsafe_allow_html=True)

control_col1, control_col2, control_col3 = st.columns([1.4, 1.4, 1])

with control_col1:
    language_label = st.selectbox(
        "Target Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=1
    )
    language = LANGUAGE_OPTIONS[language_label]

with control_col2:
    mode = st.radio(
        "Choose Input Mode",
        ["Record from Microphone", "Upload Audio File", "Demo Mode"]
    )

with control_col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🧹 Clear Conversation", key="clear_conversation_button"):
        st.session_state.history = []
        st.session_state.running = False
        st.session_state.last_live_message = "Ready."
        st.rerun()


# =========================
# DEMO MODE
# =========================

if mode == "Demo Mode":
    st.markdown("""
    <div class="neon-card">
        <div style="font-size:18px; font-weight:900; color:#22d3ee;">
            ⚡ Demo Mode
        </div>
        <div style="color:#94a3b8; margin-top:8px;">
            Use this if microphone or model processing is slow during presentation.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ Load Demo Conversation", key="load_demo_conversation"):
        st.session_state.history = load_demo_history()
        st.session_state.running = False
        st.success("Demo conversation loaded successfully.")
        st.rerun()


# =========================
# MODE 1: MICROPHONE - AUTO LIVE MODE
# =========================

if mode == "Record from Microphone":

    st.markdown("""
    <div class="neon-card" style="margin-top:20px; margin-bottom:20px;">
        <div style="font-size:18px; font-weight:900; color:#22d3ee;">
            🎙 Auto Live Speaker Translation
        </div>
        <div style="color:#94a3b8; margin-top:8px;">
            Click start once. The app records hidden 6-second chunks and updates the conversation until you press stop.
        </div>
    </div>
    """, unsafe_allow_html=True)

    live_col1, live_col2 = st.columns(2)

    with live_col1:
        if st.button("▶ Start Live Speaker Translation", key="start_live_translation"):
            st.session_state.running = True
            st.session_state.last_live_message = "Live translation started."
            st.rerun()

    with live_col2:
        if st.button("⏹ Stop Live Translation", key="stop_live_translation"):
            st.session_state.running = False
            st.session_state.last_live_message = "Live translation stopped."
            st.rerun()

    if st.session_state.running:
        st.markdown("""
        <div class="neon-card" style="border-color:rgba(34,197,94,0.45); margin-top:18px;">
            <div style="color:#22c55e; font-size:18px; font-weight:900;">
                🔴 Live mode active
            </div>
            <div style="color:#94a3b8; margin-top:6px;">
                Speak naturally. For best results, use short sentences with small pauses.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.info(st.session_state.get("last_live_message", "Ready."))


# =========================
# MODE 2: UPLOAD AUDIO FILE
# =========================

if mode == "Upload Audio File":

    uploaded_file = st.file_uploader(
        "Upload Audio File",
        type=["wav", "mp3", "m4a", "flac"],
        key="upload_audio_file"
    )

    if uploaded_file is not None:

        file_ext = uploaded_file.name.split(".")[-1].lower()
        audio_file = f"uploaded_audio_file.{file_ext}"

        with open(audio_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.audio(audio_file)
        st.success(f"Uploaded: {uploaded_file.name}")

        upload_processing_mode = st.radio(
            "Upload Processing Mode",
            [
                "Fast Mode - No Speaker Detection",
                "Speaker Mode - Slow but Diarized"
            ],
            index=0,
            key="upload_processing_mode"
        )

        st.info(
            "Use Fast Mode for short clips and long audio. "
            "Use Speaker Mode only for clear multi-speaker audio."
        )

        if st.button("⚡ Process Uploaded Audio", key="process_uploaded_audio"):
            with st.spinner("Processing uploaded audio..."):

                if upload_processing_mode == "Fast Mode - No Speaker Detection":
                    new_results = process_uploaded_fast(
                        audio_file,
                        language,
                        chunk_seconds=30
                    )
                else:
                    new_results = process_long_audio(
                        audio_file,
                        language,
                        chunk_seconds=90
                    )

            if new_results:
                st.session_state.history.extend(new_results)
                st.success(f"Added {len(new_results)} conversation line(s).")
                st.rerun()
            else:
                st.warning(
                    "No clear speech detected or audio could not be processed. "
                    "Try a normal 5-10 sec voice recording for testing."
                )


# =========================
# LIVE DASHBOARD
# =========================

speakers_now = set(item["speaker"] for item in st.session_state.history)
messages_now = len(st.session_state.history)

total_words_now = 0
for item in st.session_state.history:
    total_words_now += len(item["english"].split())

avg_words_now = round(total_words_now / messages_now, 1) if messages_now > 0 else 0

status_now = "LIVE" if st.session_state.running else "IDLE"
status_color = "#22c55e" if status_now == "LIVE" else "#22d3ee"

st.markdown("""
<div class="section-title">
    <div class="section-icon">📊</div>
    Live Dashboard
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="neon-card">
        <div class="metric-title">Total Messages</div>
        <div class="metric-value">{messages_now}</div>
        <div class="metric-good">Conversation count</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="neon-card">
        <div class="metric-title">Total Speakers</div>
        <div class="metric-value">{len(speakers_now)}</div>
        <div class="metric-good">Detected speakers</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="neon-card">
        <div class="metric-title">Avg Words / Msg</div>
        <div class="metric-value">{avg_words_now}</div>
        <div class="metric-good">{total_words_now} total words</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="neon-card">
        <div class="metric-title">Status</div>
        <div class="metric-value" style="color:{status_color};">{status_now}</div>
        <div class="metric-good">System ready</div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# SPEAKER MANAGEMENT
# =========================

raw_speakers = sorted(set(item["speaker"] for item in st.session_state.history))

if raw_speakers:
    st.markdown("""
    <div class="section-title">
        <div class="section-icon">👥</div>
        Speaker Management
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(min(len(raw_speakers), 3))

    for i, speaker in enumerate(raw_speakers):
        with cols[i % len(cols)]:
            new_name = st.text_input(
                f"Rename {speaker}",
                value=st.session_state.speaker_names.get(speaker, ""),
                placeholder="Example: Durgesh",
                key=f"rename_{speaker}"
            )

            if new_name.strip():
                st.session_state.speaker_names[speaker] = new_name.strip()


# =========================
# ANALYTICS
# =========================

st.markdown("---")
st.markdown("""
<div class="section-title">
    <div class="section-icon">📈</div>
    Conversation Analytics
</div>
""", unsafe_allow_html=True)

analytics = calculate_analytics(st.session_state.history)

if analytics:
    total_messages_analytics = sum(
        data["messages"]
        for data in analytics.values()
    )

    metric_cols = st.columns(len(analytics))

    for idx, (speaker, data) in enumerate(analytics.items()):
        percentage = (
            data["messages"] /
            total_messages_analytics
        ) * 100

        with metric_cols[idx]:
            st.metric(
                speaker,
                data["messages"]
            )

            st.caption(
                f"{percentage:.1f}% of conversation"
            )

    most_active = max(
        analytics,
        key=lambda x: analytics[x]["messages"]
    )

    st.success(
        f"🏆 Most Active Speaker: {most_active}"
    )

    chart_data = []

    for speaker, data in analytics.items():
        chart_data.append(
            {
                "Speaker": speaker,
                "Messages": data["messages"]
            }
        )

    df = pd.DataFrame(chart_data)

    st.subheader("🥧 Speaker Distribution")

    pie_fig = px.pie(
        df,
        names="Speaker",
        values="Messages",
        hole=0.4
    )

    st.plotly_chart(
        pie_fig,
        use_container_width=True
    )

    st.subheader("📊 Messages Per Speaker")

    bar_fig = px.bar(
        df,
        x="Speaker",
        y="Messages",
        text="Messages"
    )

    st.plotly_chart(
        bar_fig,
        use_container_width=True
    )

else:
    st.info("No analytics yet. Start recording, upload audio, or load demo first.")


# =========================
# AI SUMMARY
# =========================

st.markdown("---")
st.markdown("""
<div class="section-title">
    <div class="section-icon">🧠</div>
    AI Conversation Summary
</div>
""", unsafe_allow_html=True)

if st.session_state.history:
    summary_text = create_basic_summary(st.session_state.history)

    st.markdown(
        f"""
        <div class="speaker-card speaker-other">
            <pre style="white-space: pre-wrap; font-size:16px;">{clean_html(summary_text)}</pre>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.download_button(
        label="⬇ Download Summary",
        data=summary_text,
        file_name="conversation_summary.txt",
        mime="text/plain",
        key="download_summary"
    )
else:
    st.info("No summary yet. Record, upload, or load demo first.")


# =========================
# CONVERSATION OUTPUT
# =========================

st.markdown("---")
st.markdown("""
<div class="section-title">
    <div class="section-icon">💬</div>
    Live Conversation · Dual Pane
</div>
""", unsafe_allow_html=True)

show_conversation(st.session_state.history)


# =========================
# EXPORTS AND SAVE
# =========================

if st.session_state.history:
    transcript_text = build_transcript_text(st.session_state.history)

    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        st.download_button(
            label="📥 Download Transcript",
            data=transcript_text,
            file_name="conversation_transcript.txt",
            mime="text/plain",
            key="download_txt"
        )

    with export_col2:
        if st.button("💾 Save Conversation", key="save_history_button"):
            save_conversation_to_db(st.session_state.history)
            st.success("Conversation saved to conversation_history.db")

    with export_col3:
        if st.button("📄 Create PDF Report", key="create_pdf_button"):
            pdf_file = create_pdf_report(st.session_state.history)

            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="⬇ Download PDF Report",
                    data=f,
                    file_name="conversation_report.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )


# =========================
# HISTORY VIEWER
# =========================

show_history_section()


# =========================
# FOOTER
# =========================

st.markdown("""
<hr style="border:1px solid rgba(148,163,184,0.18); margin-top:40px;">

<div style="
    text-align:center;
    color:#94a3b8;
    font-size:14px;
    padding:18px;
    letter-spacing:1px;
">
    ⚡ AI Voice Translator · Cyberpunk Edition · Built by Durgesh Mali · Whisper × PyAnnote × Streamlit
</div>
""", unsafe_allow_html=True)


# =========================
# AUTO LIVE RUNNER
# =========================

if st.session_state.running and mode == "Record from Microphone":
    run_live_chunk(language)
