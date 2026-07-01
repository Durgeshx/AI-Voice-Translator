import sounddevice as sd
from scipy.io.wavfile import write

sample_rate = 44100
duration = 10

print("Recording starts in 3 seconds...")
sd.sleep(3000)

print("SPEAK NOW!")

audio = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype="int16",
    device=1
)

sd.wait()

write("test_voice.wav", sample_rate, audio)

print("Recording complete.")