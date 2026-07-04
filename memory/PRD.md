# AI Voice Translator · Gen-Z Cyberpunk Edition — PRD

## Original Problem Statement
Upgrade Streamlit UI/UX to a Gen-Z aesthetic:
- Dark glassmorphism, neon violet / electric cyan / cyber pink gradients, 16px radii, glowing states
- Waveform visualizer during recording
- Dual-pane WhatsApp/Telegram-style chat bubbles (original ↔ translation)
- Color-coded speaker diarization cards
- Instant PDF / TXT / JSON export
- Interactive Plotly analytics (talking time, sentiment over time)

## Architecture
- **Streamlit** front-end app (`/app/streamlit_app/`), single-user, port 8501
- **Emergent LLM Universal Key** (gpt-5.4) for AI summary + per-message sentiment
- **deep-translator** primary translator, LLM fallback
- Optional local heavy stack (whisper + pyannote + torch + sounddevice) — commented in requirements
- SQLite persistence (`conversation_history.db`)
- Modular files: `app.py`, `styles.py`, `ai_utils.py`, `analytics.py`, `audio_utils.py`, `exports.py`, `db.py`

## User Personas
1. **Bilingual product manager** — records team meetings, exports translated notes to PDF
2. **Language-learning creator** — reviews sentiment/topic breakdown per speaker
3. **Field researcher** — uploads audio, gets diarized bilingual transcript

## Core Requirements (static)
- Hero + control deck + capability badges
- Live waveform visualizer
- Dual-pane chat bubbles (color-coded per speaker)
- Metric strip: messages, words, avg words, positivity index
- Analytics: donut (word share), bar (messages/speaker), sentiment mood line
- AI summary (TL;DR, topics, speaker highlights, vibe, actions)
- Exports: PDF, TXT, JSON, DB save
- History with search + clear-all
- Demo mode (works without hardware / heavy models)

## Implemented (2026-01-04)
- [x] Full Gen-Z dark glassmorphism CSS with animated grain, shimmer hero, glowing recording indicator
- [x] Bricolage Grotesque + Manrope + JetBrains Mono fonts
- [x] 8-color speaker palette with stable per-speaker mapping
- [x] Dual-pane bubble grid with EN / target-lang side-by-side
- [x] Live animated waveform (CSS bars) that pauses when idle
- [x] AI summary + batched sentiment scoring via `gpt-5.4`
- [x] Fallback heuristic sentiment when key absent
- [x] Plotly donut, horizontal bar, sentiment spline chart (dark neon theme)
- [x] Styled PDF report + TXT + JSON exports
- [x] SQLite history with search + clear-all
- [x] Demo mode with bilingual sample conversation
- [x] Graceful fallback when whisper/pyannote/sounddevice unavailable

## Backlog / Future
- **P1**: Streaming AI summary via `stream_message`
- **P1**: Multi-page nav (Live · Analytics · Reports · Settings)
- **P2**: Speaker naming (rename `SPEAKER_00` → `Alice`)
- **P2**: Cloud sync of history (optional Firebase / Supabase)
- **P2**: Auto-translate summary to target language
- **P3**: Voice cloning + auto-dubbing playback

## Files touched
- `/app/streamlit_app/.env` (EMERGENT_LLM_KEY, HF_TOKEN placeholder, provider/model)
- `/app/streamlit_app/requirements.txt`
- `/app/streamlit_app/app.py`
- `/app/streamlit_app/styles.py`
- `/app/streamlit_app/ai_utils.py`
- `/app/streamlit_app/audio_utils.py`
- `/app/streamlit_app/analytics.py`
- `/app/streamlit_app/exports.py`
- `/app/streamlit_app/db.py`
- `/app/streamlit_app/README.md`
- `/app/streamlit_app/final_premium_app_original.py` (original for reference)
