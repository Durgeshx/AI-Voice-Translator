import whisper
import librosa
import torch
from pyannote.audio import Pipeline

HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN"

print("Loading Whisper...")

whisper_model = whisper.load_model("base")

print("Transcribing audio...")

result = whisper_model.transcribe(
    "test_voice.wav",
    language="en"
)

segments = result["segments"]

print("Loading audio for diarization...")

audio, sr = librosa.load(
    "test_voice.wav",
    sr=16000,
    mono=True
)

waveform = torch.tensor(audio).unsqueeze(0)

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

print("\nFINAL TRANSCRIPT\n")

for segment in segments:

    start = segment["start"]
    end = segment["end"]
    text = segment["text"]

    speaker_name = "UNKNOWN"
    best_overlap = 0

    for turn, _, speaker in annotation.itertracks(yield_label=True):

        overlap_start = max(start, turn.start)
        overlap_end = min(end, turn.end)

        overlap = overlap_end - overlap_start

        if overlap > best_overlap:
            best_overlap = overlap
            speaker_name = speaker

    print(f"[{speaker_name}] {text}")
