import time
import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Live Conversation Translator", layout="wide")

st.title("🎤 Version 7 - Live Conversation Translator")

language = st.selectbox("Target Language", ["hi", "es", "fr"])

chunk_seconds = st.slider("Chunk length seconds", 2, 6, 3)

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
    if st.button("▶ Start Live Translation"):
        st.session_state.running = True

with col2:
    if st.button("⏹ Stop"):
        st.session_state.running = False

placeholder = st.empty()

if st.session_state.running:
    st.info("Listening... speak now")

    samplerate = 16000

    audio = sd.rec(
        int(chunk_seconds * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    sf.write("live_chunk.wav", audio, samplerate)

    result = model.transcribe("live_chunk.wav", language="en")
    text = result["text"].strip()

    if text:
        translated = GoogleTranslator(
            source="auto",
            target=language
        ).translate(text)

        st.session_state.history.append((text, translated))

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