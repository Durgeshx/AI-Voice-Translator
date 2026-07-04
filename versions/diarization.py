from pyannote.audio import Pipeline

HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN"

print("Loading diarization model...")

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=HF_TOKEN
)

print("Analyzing audio...")

diarization = pipeline("test_voice.wav")

for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"{speaker}: {turn.start:.1f}s - {turn.end:.1f}s")