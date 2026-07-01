import whisper
import librosa
import torch
from pyannote.audio import Pipeline
from deep_translator import GoogleTranslator

# ==========================

# CONFIG

# ==========================

AUDIO_FILE = "test_voice.wav"

HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN"

TARGET_LANGUAGE = "hi"   # hi=Hindi, es=Spanish

# ==========================

# LOAD WHISPER

# ==========================

print("Loading Whisper...")

whisper_model = whisper.load_model("base")

# ==========================

# TRANSCRIBE AUDIO

# ==========================

print("Transcribing audio...")

whisper_result = whisper_model.transcribe(
AUDIO_FILE,
language="en"
)

segments = whisper_result["segments"]
print(type(segments))
# ==========================

# LOAD AUDIO FOR DIARIZATION

# ==========================

print("Loading audio...")

audio, sr = librosa.load(
AUDIO_FILE,
sr=16000,
mono=True
)

waveform = torch.tensor(audio).unsqueeze(0)

# ==========================

# LOAD PYANNOTE

# ==========================

print("Loading diarization model...")

pipeline = Pipeline.from_pretrained(
"pyannote/speaker-diarization-3.1",
token=HF_TOKEN
)

print("Running diarization...")

diarization = pipeline(
{
"waveform": waveform,
"sample_rate": sr
}
)

annotation = diarization.speaker_diarization

# ==========================

# MATCH TEXT TO SPEAKERS

# ==========================

print("\nFINAL RESULT\n")

for segment in segments:

    start = segment["start"]
    end = segment["end"]
    text = segment["text"].strip()

    speaker_name = "UNKNOWN"
    best_overlap = 0

    for turn, _, speaker in annotation.itertracks(
        yield_label=True
    ):

        overlap_start = max(start, turn.start)
        overlap_end = min(end, turn.end)

        overlap = overlap_end - overlap_start

        if overlap > best_overlap:
            best_overlap = overlap
            speaker_name = speaker

    translated = GoogleTranslator(
        source="en",
        target=TARGET_LANGUAGE
    ).translate(text)

    print(f"[{speaker_name}]")
    print("English :", text)
    print("Translated :", translated)
    print()