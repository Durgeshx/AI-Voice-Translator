import time
import numpy as np
import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper
import librosa
import torch

from pyannote.audio import Pipeline
from deep_translator import GoogleTranslator

# =========================
# CONFIG
# =========================

HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN"

st.set_page_config(
    page_title="AI Voice Translator",
    layout="wide"
)

st.title("🎤 AI Voice Translator - Final App")

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


def show_conversation(history):
    for item in history[-50:]:
        speaker = item["speaker"]
        english = item["english"]
        translation = item["translation"]

        if speaker == "SPEAKER_00":
            bg_color = "#dbeafe"
            text_color = "#1d4ed8"
        elif speaker == "SPEAKER_01":
            bg_color = "#dcfce7"
            text_color = "#15803d"
        else:
            bg_color = "#f3f4f6"
            text_color = "#111827"

        st.markdown(
            f"""
            <div style="
                background-color:{bg_color};
                color:{text_color};
                padding:15px;
                border-radius:12px;
                margin-bottom:12px;
                font-size:18px;">
                <b>{speaker}</b><br><br>
                <b>English:</b> {english}<br>
                <b>Translation:</b> {translation}
            </div>
            """,
            unsafe_allow_html=True
        )


def download_transcript(history):
    if history:
        transcript_text = ""

        for item in history:
            transcript_text += f"{item['speaker']}\n"
            transcript_text += f"English: {item['english']}\n"
            transcript_text += f"Translation: {item['translation']}\n"
            transcript_text += "-" * 40
            transcript_text += "\n\n"

        st.download_button(
            label="📥 Download Transcript",
            data=transcript_text,
            file_name="conversation_transcript.txt",
            mime="text/plain"
        )


# =========================
# LOAD MODELS
# =========================

with st.spinner("Loading AI models..."):
    whisper_model = load_whisper()
    diarization_model = load_pyannote()

# =========================
# UI STATE
# =========================

if "history" not in st.session_state:
    st.session_state.history = []

if "running" not in st.session_state:
    st.session_state.running = False

# =========================
# SIDEBAR / CONTROLS
# =========================

language = st.selectbox(
    "Target Language",
    ["hi", "es", "fr"]
)

mode = st.radio(
    "Choose Input Mode",
    ["Record from Microphone", "Upload Audio File"]
)

if st.button("🧹 Clear Conversation"):
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
        if st.button("▶ Start Live Speaker Translation"):
            st.session_state.running = True

    with col2:
        if st.button("⏹ Stop"):
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
        type=["wav", "mp3", "m4a"]
    )

    if uploaded_file is not None:
        audio_file = "uploaded_audio_file"

        file_extension = uploaded_file.name.split(".")[-1]
        audio_file = f"uploaded_audio.{file_extension}"

        with open(audio_file, "wb") as f:
            f.write(uploaded_file.read())

        st.success(f"Uploaded: {uploaded_file.name}")

        if st.button("Process Uploaded Audio"):
            with st.spinner("Processing uploaded audio..."):
                new_results = process_audio(audio_file, language)

            st.session_state.history.extend(new_results)

# =========================
# DISPLAY RESULTS
# =========================

st.subheader("Conversation Output")

show_conversation(st.session_state.history)

download_transcript(st.session_state.history)