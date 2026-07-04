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

---

## Update — 2026-01-04 (Iteration 2)

### New in this iteration
- [x] **Speaker rename UI** — collapsible expander in Control Deck lists all detected raw speaker IDs; typing a name applies it everywhere (dual-pane bubbles, donut / bar / sentiment charts, AI summary, PDF/TXT/JSON exports, DB save). Empty field falls back to raw ID.
- [x] **Streaming AI summary** — new `stream_ai_summary()` bridges Emergent's `stream_message()` async API into a sync generator; consumed via `st.write_stream()` for token-by-token display in a glass card. Session-state-cached so it survives reruns.
- [x] **Hosted preview** — Streamlit now runs under supervisor (`/etc/supervisor/conf.d/streamlit.conf`) on :8501; the React frontend has been swapped for a tiny Node `http-proxy` server (`/app/frontend/proxy_server.js`) on :3000 that reverse-proxies HTTP + WebSocket to :8501. Old React app still available via `yarn start:react`. Public URL: `${REACT_APP_BACKEND_URL}` serves Streamlit directly.

### Files added / changed
- `/app/streamlit_app/ai_utils.py` — added `stream_ai_summary()` (thread + queue async→sync bridge)
- `/app/streamlit_app/app.py` — added `display_name()` / `apply_names()` helpers, Rename Speakers expander, converted summary to streaming display
- `/app/frontend/proxy_server.js` — new HTTP+WS reverse proxy
- `/app/frontend/package.json` — new `start` = `node proxy_server.js`, old React kept as `start:react`
- `/etc/supervisor/conf.d/streamlit.conf` — new program

### Verified
- Public URL loads Streamlit UI end-to-end
- Speakers renamed to Alice / Bob / Charlie propagate to chat bubbles, analytics legend/labels, and streamed AI summary
- `stream_message()` events land in the UI without buffering

---

## Update — 2026-01-04 (Iteration 3)

### New in this iteration
- [x] **English target language** — added `en · English` as the first option in the language dropdown
- [x] **EN → EN passthrough** — when target is English (audio source is already English) `translate()` returns the original text instead of round-tripping through Google Translate
- [x] **build_demo_history** — English target now shows identical English text on both bubble panes (removed the `[English]` suffix)
- [x] **Split requirements** — `requirements.txt` (core, hosted-preview safe) and `requirements-local.txt` (heavy live pipeline: openai-whisper, pyannote.audio, torch, torchaudio, librosa, sounddevice, soundfile). README explains both.

### Notes
- Heavy AI packages cannot build inside the preview pod (setuptools/pkg_resources missing in build isolation) — they're intended for the user's local machine. Hosted preview uses Demo Mode + Emergent LLM key.
