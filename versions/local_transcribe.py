import whisper

print("Loading model...")
model = whisper.load_model("base")

print("Transcribing...")

result = model.transcribe(
    "test_voice.wav",
    language="en"
)

print("\nSegments:\n")

for segment in result["segments"]:
    print(
        f"{segment['start']:.2f}s -> "
        f"{segment['end']:.2f}s : "
        f"{segment['text']}"
    )