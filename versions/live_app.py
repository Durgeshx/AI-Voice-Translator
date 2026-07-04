import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Voice Translator")

st.title("🎤 AI Voice Translator")

language_map = {
    "Hindi": "hi",
    "Spanish": "es",
    "French": "fr"
}

selected_language = st.selectbox(
    "Choose Translation Language",
    list(language_map.keys())
)

TARGET_LANGUAGE = language_map[selected_language]

@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

if st.button("🎙 Record 5 Seconds"):

    st.info("Recording... Speak now")

    samplerate = 16000
    duration = 5

    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    sf.write(
        "recorded.wav",
        audio,
        samplerate
    )

    st.success("Recording Complete")

    with st.spinner("Transcribing..."):

        result = model.transcribe(
            "recorded.wav",
            language="en"
        )

        english_text = result["text"]

    with st.spinner("Translating..."):

        translated_text = GoogleTranslator(
            source="en",
            target=TARGET_LANGUAGE
        ).translate(english_text)

    st.subheader("English")

    st.write(english_text)

    st.subheader("Translated")

    st.write(translated_text)