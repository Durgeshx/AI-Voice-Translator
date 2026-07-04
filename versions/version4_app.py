import streamlit as st
import whisper
from deep_translator import GoogleTranslator

st.set_page_config(page_title="AI Voice Translator")

st.title("🎤 AI Voice Translator")

language = st.selectbox(
"Target Language",
["hi", "es", "fr"]
)

if st.button("Process test_voice.wav"):


 st.write("Loading Whisper...")

model = whisper.load_model("small")

result = model.transcribe("test_voice.wav")

text = result["text"]

translated = GoogleTranslator(
    source="auto",
    target=language
).translate(text)

with open("output.txt", "w", encoding="utf-8") as f:
    f.write("English:\n")
    f.write(text)
    f.write("\n\nTranslation:\n")
    f.write(translated)

st.subheader("English")
st.write(text)

st.subheader("Translation")
st.write(translated)

st.success("Saved to output.txt")

