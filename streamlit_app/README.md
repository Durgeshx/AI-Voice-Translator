# AI Voice Translator · Gen-Z Cyberpunk Edition

A complete UI/UX overhaul of the original AI Voice Translator with:

- **Dark glassmorphism** with neon violet / electric cyan / cyber pink accents
- **Dual-pane chat bubbles** (WhatsApp / Telegram style, English ↔ Translation side-by-side)
- **Color-coded speaker cards** (8-color palette, stable per speaker)
- **Live waveform visualizer** while recording
- **Interactive Plotly analytics** — talking-time donut, per-speaker bars, sentiment mood-line
- **AI-powered summary + per-message sentiment** (Emergent Universal LLM key, `gpt-5.4`)
- **Instant exports** — PDF (styled), TXT, JSON
- **Demo mode** so the whole UI is explorable without hardware

---

## Quick start

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

## Enable full live pipeline (mic + Whisper + pyannote)

For real microphone recording, local Whisper transcription and
pyannote speaker diarization, also install the heavy stack:

```bash
pip install -r requirements-local.txt
```

Set your Hugging Face token in `.env` (needed to download
`pyannote/speaker-diarization-3.1`):

```
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

Without these packages the app stays fully functional via **Demo Mode**.

## Environment

`.env`:

```
EMERGENT_LLM_KEY=sk-emergent-…       # already provisioned
HF_TOKEN=                             # optional, for pyannote diarization
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.4
```

## File map

| file | purpose |
|------|---------|
| `app.py` | main Streamlit page |
| `styles.py` | CSS + hero / section / waveform helpers |
| `ai_utils.py` | Emergent LLM key wrappers (summary, sentiment, translation) |
| `analytics.py` | Plotly charts |
| `audio_utils.py` | Whisper + pyannote pipeline + demo fallback |
| `exports.py` | PDF / TXT / JSON exporters |
| `db.py` | SQLite persistence |
