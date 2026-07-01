import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper
from deep_translator import GoogleTranslator

st.set_page_config(page_title="AI Voice Translator")

st.title("🎤 AI Voice Translator - Version 5")

language = st.selectbox(
    "Target Language",
    ["hi", "es", "fr"]
)

duration = st.slider(
    "Recording Duration (seconds)",
    3,
    15,
    5
)

@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

model = load_whisper_model()

if st.button("🎙 Start Recording"):

    st.info("Recording... speak now")

    samplerate = 16000

    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    sf.write(
        "web_recording.wav",
        audio,
        samplerate
    )

    st.success("Recording saved as web_recording.wav")

    st.write("Transcribing...")

    result = model.transcribe(
        "web_recording.wav",
        language="en"
    )

    text = result["text"].strip()

    st.subheader("English")
    st.write(text)

    translated = GoogleTranslator(
        source="auto",
        target=language
    ).translate(text)

    st.subheader("Translation")
    st.write(translated)

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write("English:\n")
        f.write(text)
        f.write("\n\nTranslation:\n")
        f.write(translated)

    st.success("Saved result to output.txt")