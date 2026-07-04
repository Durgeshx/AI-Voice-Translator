"""
Audio processing pipeline with graceful fallback.

- Heavy models (whisper, pyannote, torch, sounddevice) are OPTIONAL.
- If a model is unavailable (or hardware is missing), the app switches to
  DEMO MODE which loads a realistic sample conversation so the UI stays
  fully explorable.
"""
from __future__ import annotations

import os
from pathlib import Path

_HAS_WHISPER = False
_HAS_PYANNOTE = False
_HAS_SD = False

try:
    import whisper  # type: ignore

    _HAS_WHISPER = True
except Exception:
    whisper = None  # type: ignore

try:
    import torch  # type: ignore
    import librosa  # type: ignore
    from pyannote.audio import Pipeline  # type: ignore

    _HAS_PYANNOTE = True
except Exception:
    torch = None  # type: ignore
    librosa = None  # type: ignore
    Pipeline = None  # type: ignore

try:
    import sounddevice as sd  # type: ignore
    import soundfile as sf  # type: ignore

    _HAS_SD = True
except Exception:
    sd = None  # type: ignore
    sf = None  # type: ignore


def capabilities() -> dict:
    return {
        "whisper": _HAS_WHISPER,
        "diarization": _HAS_PYANNOTE and bool(os.environ.get("HF_TOKEN")),
        "microphone": _HAS_SD,
    }


# ────────────────────────────────────────────────────────────────
# TRANSCRIPTION CORRECTIONS
# ────────────────────────────────────────────────────────────────

_CORRECTIONS = {
    "Durgeesh Mali": "Durgesh Mali",
    "Durgaish Mali": "Durgesh Mali",
    "Durgaishmali": "Durgesh Mali",
    "Gashmali": "Durgesh Mali",
    "Tugeshmali": "Durgesh Mali",
    "Bokeh": "Dabok",
    "Devok": "Dabok",
    "Devoke": "Dabok",
    "AI modern": "AI model",
}


def fix_transcription(text: str) -> str:
    for wrong, correct in _CORRECTIONS.items():
        text = text.replace(wrong, correct)
    return text


# ────────────────────────────────────────────────────────────────
# DEMO CONVERSATION (used when models absent / for UI preview)
# ────────────────────────────────────────────────────────────────

DEMO_CONVERSATION_EN = [
    ("SPEAKER_00", "Hey! Have you tried the new AI translator we built?"),
    ("SPEAKER_01", "Not yet — is it faster than the old whisper pipeline?"),
    ("SPEAKER_00", "Way faster. And it detects who is speaking in real time."),
    ("SPEAKER_01", "That's amazing. Does it also handle sentiment analysis?"),
    ("SPEAKER_00", "Yes, every message gets a sentiment score and a color-coded card."),
    ("SPEAKER_02", "Sounds cool. Can I export the full transcript as a PDF?"),
    ("SPEAKER_00", "Absolutely — PDF, TXT and JSON, one click each."),
    ("SPEAKER_01", "Honestly, this is the cleanest voice tool I've seen this year."),
    ("SPEAKER_02", "Agreed. The neon glass UI is straight fire."),
    ("SPEAKER_00", "Ship it. Let's demo this to the team tomorrow morning."),
]


def build_demo_history(target_language_name: str = "Hindi") -> list[dict]:
    """Fabricate a plausible bilingual demo history — used for UI preview."""
    # Static hindi translations to avoid API dependency during demo
    demo_hi = [
        "अरे! क्या आपने हमारा नया AI ट्रांसलेटर आज़माया?",
        "अभी नहीं — क्या यह पुरानी whisper पाइपलाइन से तेज़ है?",
        "बहुत तेज़। और यह रीयल-टाइम में बताता है कौन बोल रहा है।",
        "यह कमाल है। क्या यह sentiment analysis भी करता है?",
        "हाँ, हर मैसेज को sentiment score और color-coded card मिलता है।",
        "मस्त लग रहा है। क्या मैं पूरा transcript PDF में export कर सकता हूँ?",
        "बिल्कुल — PDF, TXT और JSON, एक-एक क्लिक में।",
        "सच कहूँ तो, इस साल की सबसे साफ़-सुथरी voice tool है।",
        "मान गए। यह neon glass UI बिल्कुल आग है।",
        "चलो शिप करते हैं। कल सुबह टीम को डेमो दिखाते हैं।",
    ]
    lang = target_language_name.lower()
    english_texts = [e[1] for e in DEMO_CONVERSATION_EN]

    if lang.startswith("h"):
        translations = demo_hi
    elif lang.startswith("e"):  # English → English: same-language passthrough
        translations = english_texts
    else:
        translations = [f"{t} [{target_language_name}]" for t in english_texts]

    return [
        {"speaker": spk, "english": en, "translation": tr, "sentiment": "NEU", "score": 0.0}
        for (spk, en), tr in zip(DEMO_CONVERSATION_EN, translations)
    ]


# ────────────────────────────────────────────────────────────────
# LIVE PROCESSING (only when heavy models available)
# ────────────────────────────────────────────────────────────────

_whisper_model = None
_diar_model = None


def load_whisper(model_name: str = "small"):
    global _whisper_model
    if not _HAS_WHISPER:
        return None
    if _whisper_model is None:
        _whisper_model = whisper.load_model(model_name)
    return _whisper_model


def load_diarization():
    global _diar_model
    if not _HAS_PYANNOTE or not os.environ.get("HF_TOKEN"):
        return None
    if _diar_model is None:
        _diar_model = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=os.environ.get("HF_TOKEN"),
        )
    return _diar_model


def process_audio(audio_path: str, target_language: str, translator_fn) -> list[dict]:
    """Full pipeline: STT → diarization → translation. Returns list of dicts."""
    if not _HAS_WHISPER:
        raise RuntimeError("Whisper is not installed. See requirements.txt to enable live mode.")

    w = load_whisper()
    result = w.transcribe(audio_path, language="en", fp16=False)
    segments = result["segments"]

    diar = load_diarization()
    annotation = None
    if diar is not None and _HAS_PYANNOTE:
        audio_data, sr = librosa.load(audio_path, sr=16000, mono=True)
        waveform = torch.tensor(audio_data).unsqueeze(0)
        diarization = diar({"waveform": waveform, "sample_rate": sr})
        annotation = diarization.speaker_diarization

    out = []
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        text = fix_transcription(seg["text"].strip())
        if not text:
            continue

        speaker = "SPEAKER_00"
        if annotation is not None:
            best = 0
            for turn, _, label in annotation.itertracks(yield_label=True):
                overlap = max(0, min(end, turn.end) - max(start, turn.start))
                if overlap > best:
                    best = overlap
                    speaker = label

        translation = translator_fn(text, target_language)
        out.append(
            {
                "speaker": speaker,
                "english": text,
                "translation": translation,
                "sentiment": "NEU",
                "score": 0.0,
            }
        )
    return out


def record_microphone(seconds: int = 8, samplerate: int = 16000, path: str | None = None) -> tuple[str, float]:
    if not _HAS_SD:
        raise RuntimeError("sounddevice not available in this environment.")
    import numpy as np

    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()
    volume = float((audio ** 2).mean() ** 0.5)
    out_path = path or str(Path(__file__).parent / "final_live_chunk.wav")
    sf.write(out_path, audio, samplerate)
    return out_path, volume
