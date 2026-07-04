import time
import numpy as np
import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Version 8 - Voice Activity Translator", layout="wide")

st.title("🎤 Version 8 - Voice Activity Translator")

language = st.selectbox("Target Language", ["hi", "es", "fr"])

chunk_seconds = st.slider("Chunk length seconds", 2, 8, 4)

silence_threshold = st.slider(
    "Silence threshold",
    0.001,
    0.050,
    0.010,
    step=0.001
)

if "running" not in st.session_state:
    st.session_state.running = False

if "history" not in st.session_state:
    st.session_state.history = []

@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Start"):
        st.session_state.running = True

with col2:
    if st.button("⏹ Stop"):
        st.session_state.running = False

status = st.empty()

if st.session_state.running:
    status.info("Listening... speak clearly")

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

    sf.write("vad_chunk.wav", audio, samplerate)

    result = model.transcribe(
        "vad_chunk.wav",
        language="en",
        fp16=False
    )

    text = result["text"].strip()

    if text:
        translated = GoogleTranslator(
            source="auto",
            target=language
        ).translate(text)

        st.session_state.history.append((text, translated))

    time.sleep(0.5)
    st.rerun()

for english, translated in st.session_state.history[-20:]:
    st.markdown(
        f"""
        <div style="
            background-color:#dbeafe;
            color:#1d4ed8;
            padding:15px;
            border-radius:12px;
            margin-bottom:12px;
            font-size:18px;">
            <b>English:</b> {english}<br>
            <b>Translation:</b> {translated}
        </div>
        """,
        unsafe_allow_html=True
    )