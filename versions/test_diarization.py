import librosa
import torch
from pyannote.audio import Pipeline

HF_TOKEN = "YOUR_TOKEN"

print("Loading audio...")

audio, sr = librosa.load(
    "test_voice.wav",
    sr=16000,
    mono=True
)

waveform = torch.tensor(audio).unsqueeze(0)

print("Loading model...")

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

print("\nResults:\n")

annotation = diarization.speaker_diarization

for segment, track, speaker in annotation.itertracks(yield_label=True):
    print(
        f"Speaker {speaker}: "
        f"{segment.start:.2f}s -> {segment.end:.2f}s"
    )