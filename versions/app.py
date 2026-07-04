import streamlit as st
from deep_translator import GoogleTranslator

st.set_page_config(
    page_title="AI Voice Translator",
    layout="wide"
)

st.title("🎤 AI Voice Translator")

language = st.selectbox(
    "Select Target Language",
    ["hi", "es"]
)

if st.button("Start Recording"):

    st.success("Processing audio...")

    # Example output
    conversation = [
        ("SPEAKER_00", "Hello, how are you?"),
        ("SPEAKER_01", "I am fine."),
        ("SPEAKER_00", "What are you doing?"),
        ("SPEAKER_01", "Testing the AI project.")
    ]

    for speaker, text in conversation:

        translated = GoogleTranslator(
            source="en",
            target=language
        ).translate(text)

        if speaker == "SPEAKER_00":
            st.markdown(
                f"<p style='color:blue'><b>{speaker}</b>: {translated}</p>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<p style='color:green'><b>{speaker}</b>: {translated}</p>",
                unsafe_allow_html=True
            )