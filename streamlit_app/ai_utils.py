"""
AI utilities powered by Emergent Universal LLM key.
Provides: sentiment classification, AI-powered conversation summary,
optional high-quality translation fallback.
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import re
import threading
from typing import Iterable, Iterator

from dotenv import load_dotenv

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-5.4")


def _has_key() -> bool:
    return bool(EMERGENT_LLM_KEY)


def _run(coro):
    """Run async coroutine safely from a sync (Streamlit) context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


async def _chat(system: str, user: str, session_id: str = "vt-session") -> str:
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system,
    ).with_model(LLM_PROVIDER, LLM_MODEL)
    resp = await chat.send_message(UserMessage(text=user))
    return resp if isinstance(resp, str) else str(resp)


# ────────────────────────────────────────────────────────────────
# SENTIMENT ANALYSIS (batched)
# ────────────────────────────────────────────────────────────────

_SENT_SYSTEM = (
    "You classify short conversation utterances. "
    "For each numbered line, respond with ONLY that line's number, a colon, "
    "and one of: POS, NEG, NEU. "
    "Also append a score between -1.0 (very negative) and 1.0 (very positive), "
    "rounded to 2 decimals. Format strictly: `<n>:<LABEL>:<score>`. "
    "One classification per line. No extra text."
)


def _fallback_sentiment(text: str) -> tuple[str, float]:
    pos = {"good", "great", "love", "amazing", "awesome", "happy", "thanks", "nice", "cool", "yes", "sure", "excellent"}
    neg = {"bad", "hate", "angry", "awful", "terrible", "no", "sad", "sorry", "problem", "issue", "wrong", "worst"}
    tokens = re.findall(r"[a-zA-Z']+", text.lower())
    p = sum(1 for t in tokens if t in pos)
    n = sum(1 for t in tokens if t in neg)
    if p == n == 0:
        return "NEU", 0.0
    score = (p - n) / max(p + n, 1)
    label = "POS" if score > 0.15 else "NEG" if score < -0.15 else "NEU"
    return label, round(score, 2)


def analyze_sentiment_batch(texts: list[str]) -> list[tuple[str, float]]:
    """Return list of (label, score) for each text. Uses LLM if key set, else heuristic."""
    if not texts:
        return []
    if not _has_key():
        return [_fallback_sentiment(t) for t in texts]

    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    try:
        raw = _run(_chat(_SENT_SYSTEM, numbered, session_id="vt-sentiment"))
    except Exception:
        return [_fallback_sentiment(t) for t in texts]

    results: dict[int, tuple[str, float]] = {}
    for line in raw.splitlines():
        m = re.match(r"\s*(\d+)\s*:\s*(POS|NEG|NEU)\s*:\s*(-?\d+(?:\.\d+)?)", line, re.I)
        if m:
            idx = int(m.group(1)) - 1
            label = m.group(2).upper()
            try:
                score = float(m.group(3))
            except ValueError:
                score = 0.0
            results[idx] = (label, max(-1.0, min(1.0, score)))
    return [results.get(i, _fallback_sentiment(t)) for i, t in enumerate(texts)]


# ────────────────────────────────────────────────────────────────
# AI CONVERSATION SUMMARY
# ────────────────────────────────────────────────────────────────

_SUMMARY_SYSTEM = (
    "You are an expert conversation analyst. Given a multi-speaker transcript, "
    "produce a crisp, structured summary in markdown with these sections:\n"
    "1. **TL;DR** (2–3 sentences)\n"
    "2. **Key Topics** (bulleted, at most 6)\n"
    "3. **Speaker Highlights** (one line per speaker on what they contributed)\n"
    "4. **Sentiment Vibe** (single word: Positive / Neutral / Tense / Mixed) with 1-line why\n"
    "5. **Action Items / Follow-ups** (if any, else write 'None detected.')\n"
    "Keep it under 220 words. No boilerplate greetings."
)


def _fallback_summary(history: list[dict]) -> str:
    speakers = sorted({h["speaker"] for h in history})
    total = len(history)
    text_preview = " ".join(h["english"] for h in history)[:600]
    return (
        f"**TL;DR**\nConversation with {len(speakers)} speaker(s) across {total} messages.\n\n"
        f"**Key Topics**\n- (LLM key not configured — enable EMERGENT_LLM_KEY for smart summary)\n\n"
        f"**Speaker Highlights**\n" + "\n".join(f"- **{s}**: participated in the conversation" for s in speakers) +
        f"\n\n**Sentiment Vibe**\nNeutral — heuristic fallback.\n\n"
        f"**Action Items / Follow-ups**\nNone detected.\n\n"
        f"---\n*Preview:* {text_preview}…"
    )


def ai_summary(history: list[dict]) -> str:
    if not history:
        return ""
    if not _has_key():
        return _fallback_summary(history)

    transcript = "\n".join(
        f"{h['speaker']}: {h['english']}"
        for h in history
    )
    try:
        return _run(_chat(_SUMMARY_SYSTEM, transcript, session_id="vt-summary"))
    except Exception:
        return _fallback_summary(history)


# ────────────────────────────────────────────────────────────────
# STREAMING SUMMARY (token-by-token via stream_message)
# ────────────────────────────────────────────────────────────────

def stream_ai_summary(history: list[dict]) -> Iterator[str]:
    """Yield summary text chunks as they arrive from the LLM.

    Bridges the library's async streaming API into a sync generator that
    Streamlit's `st.write_stream()` can consume.
    """
    if not history:
        return
    if not _has_key():
        # single yield with the fallback so st.write_stream still works
        yield _fallback_summary(history)
        return

    transcript = "\n".join(f"{h['speaker']}: {h['english']}" for h in history)

    q: "queue.Queue[str | None]" = queue.Queue()
    _SENTINEL = None

    async def _producer():
        try:
            from emergentintegrations.llm.chat import (
                LlmChat,
                StreamDone,
                TextDelta,
                UserMessage,
            )

            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id="vt-summary-stream",
                system_message=_SUMMARY_SYSTEM,
            ).with_model(LLM_PROVIDER, LLM_MODEL)

            async for event in chat.stream_message(UserMessage(text=transcript)):
                if isinstance(event, TextDelta):
                    if event.content:
                        q.put(event.content)
                elif isinstance(event, StreamDone):
                    break
        except Exception as e:  # pragma: no cover
            q.put(f"\n\n_[stream error: {e}]_")
        finally:
            q.put(_SENTINEL)

    def _runner():
        asyncio.run(_producer())

    t = threading.Thread(target=_runner, daemon=True)
    t.start()

    while True:
        chunk = q.get()
        if chunk is _SENTINEL:
            break
        yield chunk


# ────────────────────────────────────────────────────────────────
# HIGH-QUALITY TRANSLATION (optional; deep_translator is default)
# ────────────────────────────────────────────────────────────────

_TRANSLATE_SYSTEM = (
    "You are a professional translator. Translate the user's message into the "
    "requested target language. Output ONLY the translation, no quotes, no explanation."
)


def ai_translate(text: str, target_language_name: str) -> str:
    if not _has_key() or not text.strip():
        return ""
    try:
        prompt = f"Target language: {target_language_name}\n\nText:\n{text}"
        return _run(_chat(_TRANSLATE_SYSTEM, prompt, session_id="vt-translate")).strip()
    except Exception:
        return ""
