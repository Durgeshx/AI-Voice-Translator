import streamlit as st
import whisper
from deep_translator import GoogleTranslator

st.set_page_config(page_title="AI Translator")

st.title("🎤 AI Voice Translator")

language = st.selectbox(
    "Target Language",
    ["hi", "es", "fr", "de"]
)

uploaded_file = st.file_uploader(
    "Upload WAV File",
    type=["wav"]
)

if uploaded_file:

    with open("temp.wav", "wb") as f:
        f.write(uploaded_file.read())

    st.success("File uploaded!")

    if st.button("Transcribe & Translate"):

        st.write("Loading Whisper...")

        model = whisper.load_model("base")

        result = model.transcribe("temp.wav")

        text = result["text"]

        translated = GoogleTranslator(
            source="auto",
            target=language
        ).translate(text)

        st.subheader("Original")

        st.write(text)

        st.subheader("Translated")

        st.write(translated)