import streamlit as st
import sounddevice as sd
import soundfile as sf
import whisper
import librosa
import torch

from pyannote.audio import Pipeline
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Speaker AI Translator", layout="wide")

st.title("🎤 Speaker-Aware AI Voice Translator")

HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN"

language = st.selectbox(
    "Target Language",
    ["hi", "es", "fr"]
)

duration = st.slider(
    "Recording Duration (seconds)",
    5,
    30,
    10
)

@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

@st.cache_resource
def load_diarization():
    return Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=HF_TOKEN
    )

whisper_model = load_whisper()
diarization_model = load_diarization()

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

    sf.write("web_recording.wav", audio, samplerate)

    st.success("Recording saved")

    st.write("Transcribing with Whisper...")

    whisper_result = whisper_model.transcribe(
        "web_recording.wav",
        language="en"
    )

    segments = whisper_result["segments"]

    st.write("Running speaker detection...")

    audio_data, sr = librosa.load(
        "web_recording.wav",
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

    st.subheader("Final Conversation")

    for segment in segments:

        start = segment["start"]
        end = segment["end"]
        english_text = segment["text"].strip()

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

        if speaker_name == "SPEAKER_00":
            bg_color = "#dbeafe"
            text_color = "#1d4ed8"
        elif speaker_name == "SPEAKER_01":
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
                <b>{speaker_name}</b><br><br>
                <b>English:</b> {english_text}<br>
                <b>Translation:</b> {translated_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.success("Done")