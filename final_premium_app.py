
import time
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper
import librosa
import torch

from pyannote.audio import Pipeline
from deep_translator import GoogleTranslator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# =========================
# CONFIG
# =========================

HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN"

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
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #111827 45%, #1e1b4b 100%);
    color: white;
}

.hero {
    padding: 35px;
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(59,130,246,0.25), rgba(168,85,247,0.25));
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
    margin-bottom: 25px;
}

.hero-title {
    font-size: 52px;
    font-weight: 900;
    margin-bottom: 8px;
}

.hero-subtitle {
    font-size: 20px;
    color: #cbd5e1;
}

.speaker-card {
    padding: 22px;
    border-radius: 22px;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 12px 35px rgba(0,0,0,0.25);
}

.speaker-0 {
    background: linear-gradient(135deg, rgba(37,99,235,0.30), rgba(96,165,250,0.18));
    color: #dbeafe;
}

.speaker-1 {
    background: linear-gradient(135deg, rgba(22,163,74,0.30), rgba(74,222,128,0.18));
    color: #dcfce7;
}

.speaker-other {
    background: rgba(255,255,255,0.10);
    color: white;
}

.speaker-name {
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 12px;
}

.text-label {
    font-weight: 800;
    color: #fbbf24;
}

.block-container {
    padding-top: 35px;
}

div.stButton > button {
    border-radius: 14px;
    padding: 12px 24px;
    font-weight: 700;
    border: 1px solid rgba(255,255,255,0.2);
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: white;
}

div.stDownloadButton > button {
    border-radius: 14px;
    padding: 12px 24px;
    font-weight: 700;
    background: linear-gradient(135deg, #16a34a, #22c55e);
    color: white;
}
</style>
""", unsafe_allow_html=True)


# =========================
# HERO
# =========================

st.markdown("""
<div class="hero">
    <div class="hero-title">🎤 AI Voice Translator</div>
    <div class="hero-subtitle">
        Real-time speaker detection, transcription, translation, analytics, history, and reports.
    </div>
</div>
""", unsafe_allow_html=True)


# =========================
# HELPER FUNCTIONS
# =========================

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

    return text


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
def load_pyannote():
    return Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=HF_TOKEN
    )


def process_audio(audio_file, language):
    whisper_result = whisper_model.transcribe(
        audio_file,
        language="en",
        fp16=False
    )

    whisper_segments = whisper_result["segments"]

    audio_data, sr = librosa.load(
        audio_file,
        sr=16000,
        mono=True
    )

    waveform = torch.tensor(audio_data).unsqueeze(0)

    diarization = diarization_model(
        {
            "waveform": waveform,
            "sample_rate": sr
        }
    )

    annotation = diarization.speaker_diarization

    results = []

    for segment in whisper_segments:
        start = segment["start"]
        end = segment["end"]
        english_text = fix_transcription(segment["text"].strip())

        if not english_text:
            continue

        speaker_name = "UNKNOWN"
        best_overlap = 0

        for turn, _, speaker in annotation.itertracks(yield_label=True):
            overlap_start = max(start, turn.start)
            overlap_end = min(end, turn.end)
            overlap = overlap_end - overlap_start

            if overlap > best_overlap:
                best_overlap = overlap
                speaker_name = speaker

        translated_text = GoogleTranslator(
            source="auto",
            target=language
        ).translate(english_text)

        results.append(
            {
                "speaker": speaker_name,
                "english": english_text,
                "translation": translated_text
            }
        )

    return results


def calculate_analytics(history):
    analytics = {}

    for item in history:
        speaker = item["speaker"]

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
    speakers = sorted(set(item["speaker"] for item in history))

    all_text = " ".join(item["english"] for item in history)

    summary = f"""
Conversation Summary

Total Messages: {total_messages}
Speakers Detected: {", ".join(speakers)}

Main Conversation Text:
{all_text[:800]}
"""

    return summary

def show_conversation(history):
    if not history:
        st.markdown("""
        <div class="speaker-card speaker-other">
            <div class="speaker-name">No conversation yet</div>
            Start recording or upload an audio file to see translated conversation here.
        </div>
        """, unsafe_allow_html=True)
        return

    for item in history[-50:]:
        speaker = item["speaker"]
        english = item["english"]
        translation = item["translation"]

        if speaker == "SPEAKER_00":
            speaker_class = "speaker-0"
        elif speaker == "SPEAKER_01":
            speaker_class = "speaker-1"
        else:
            speaker_class = "speaker-other"

        st.markdown(
            f"""
            <div class="speaker-card {speaker_class}">
                <div class="speaker-name">{speaker}</div>
                <div><span class="text-label">English:</span> {english}</div>
                <br>
                <div><span class="text-label">Translation:</span> {translation}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


def build_transcript_text(history):
    transcript_text = ""

    for item in history:
        transcript_text += f"{item['speaker']}\n"
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

        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, item["speaker"])
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
    st.header("📚 Conversation History")

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
                <div style="
                    background: rgba(255,255,255,0.08);
                    padding:15px;
                    border-radius:12px;
                    margin-bottom:10px;
                    border:1px solid rgba(255,255,255,0.15);
                ">
                    <b>{created_at}</b><br><br>
                    <b>{speaker}</b><br>
                    English: {english}<br>
                    Translation: {translation}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No saved conversations found.")


# =========================
# LOAD MODELS
# =========================

with st.spinner("Loading AI models..."):
    whisper_model = load_whisper()
    diarization_model = load_pyannote()


# =========================
# SESSION STATE
# =========================

if "history" not in st.session_state:
    st.session_state.history = []

if "running" not in st.session_state:
    st.session_state.running = False


# =========================
# CONTROLS
# =========================

language = st.selectbox(
    "Target Language",
    ["hi", "es", "fr"]
)

mode = st.radio(
    "Choose Input Mode",
    ["Record from Microphone", "Upload Audio File"]
)

if st.button("🧹 Clear Conversation", key="clear_conversation_button"):
    st.session_state.history = []
    st.session_state.running = False
    st.rerun()


# =========================
# MODE 1: MICROPHONE
# =========================

if mode == "Record from Microphone":
    chunk_seconds = st.slider(
        "Recording Duration / Chunk Length",
        4,
        20,
        8
    )

    silence_threshold = st.slider(
        "Silence threshold",
        0.001,
        0.050,
        0.010,
        step=0.001
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶ Start Live Speaker Translation", key="start_live_button"):
            st.session_state.running = True

    with col2:
        if st.button("⏹ Stop", key="stop_live_button"):
            st.session_state.running = False

    if st.session_state.running:
        st.info("Listening... speak clearly")

        samplerate = 16000

        audio = sd.rec(
            int(chunk_seconds * samplerate),
            samplerate=samplerate,
            channels=1,
            dtype="float32"
        )

        sd.wait()

        volume = float(np.sqrt(np.mean(audio ** 2)))
        st.write(f"Detected volume: {volume:.4f}")

        if volume < silence_threshold:
            st.warning("Silence/noise detected. Skipping this chunk.")
            time.sleep(0.5)
            st.rerun()

        audio_file = "final_live_chunk.wav"
        sf.write(audio_file, audio, samplerate)

        with st.spinner("Processing audio..."):
            new_results = process_audio(audio_file, language)

        st.session_state.history.extend(new_results)

        time.sleep(0.5)
        st.rerun()


# =========================
# MODE 2: UPLOAD AUDIO FILE
# =========================

if mode == "Upload Audio File":
    uploaded_file = st.file_uploader(
        "Upload WAV, MP3, or M4A file",
        type=["wav", "mp3", "m4a"],
        key="upload_audio_file"
    )

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1]
        audio_file = f"uploaded_audio.{file_extension}"

        with open(audio_file, "wb") as f:
            f.write(uploaded_file.read())

        st.success(f"Uploaded: {uploaded_file.name}")

        if st.button("Process Uploaded Audio", key="process_uploaded_audio"):
            with st.spinner("Processing uploaded audio..."):
                new_results = process_audio(audio_file, language)

            st.session_state.history.extend(new_results)


# =========================
# TOP METRICS
# =========================

speakers = set()

for item in st.session_state.history:
    speakers.add(item["speaker"])

total_messages_current = len(st.session_state.history)
total_speakers = len(speakers)

if st.session_state.running:
    app_status = "LIVE"
else:
    app_status = "STOPPED"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Speakers", total_speakers)

with col2:
    st.metric("Messages", total_messages_current)

with col3:
    st.metric("Language", language.upper())

with col4:
    st.metric("Status", app_status)


# =========================
# ANALYTICS
# =========================

st.markdown("---")
st.header("📊 Conversation Analytics")

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
    st.info("No analytics yet. Start recording or upload audio first.")


# =========================
# CONVERSATION OUTPUT
# =========================
st.markdown("---")
st.header("🧠 AI Conversation Summary")

if st.session_state.history:
    summary_text = create_basic_summary(st.session_state.history)

    st.markdown(
        f"""
        <div class="speaker-card speaker-other">
            <pre style="white-space: pre-wrap; font-size:16px;">{summary_text}</pre>
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
    st.info("No summary yet. Record or upload audio first.")
    
st.markdown("---")
st.header("Conversation Output")

show_conversation(st.session_state.history)


# =========================
# EXPORTS AND SAVE
# =========================

if st.session_state.history:
    transcript_text = build_transcript_text(st.session_state.history)

    st.download_button(
        label="📥 Download Transcript",
        data=transcript_text,
        file_name="conversation_transcript.txt",
        mime="text/plain",
        key="download_txt"
    )

    if st.button("💾 Save Conversation to History", key="save_history_button"):
        save_conversation_to_db(st.session_state.history)
        st.success("Conversation saved to conversation_history.db")

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

