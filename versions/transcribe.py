from openai import OpenAI

# Paste your API key here
client = OpenAI(
    api_key=""YOUR_OPENAI_API_KEY""
)

with open("test_voice.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

print("\nTranscription:")
print(transcript.text)