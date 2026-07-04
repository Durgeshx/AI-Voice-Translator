"""Plotly analytics with dark-neon theming."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from styles import PALETTE, SPEAKER_PALETTE


NEON_SEQUENCE = [
    "#B026FF", "#00E5FF", "#FF2E9A", "#C6F91F",
    "#FFB800", "#FF5A5F", "#7DFFC3", "#6366F1",
]


def _apply_dark(fig: go.Figure, height: int = 340):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", color="#F1F5F9", size=13),
        margin=dict(l=20, r=20, t=40, b=20),
        height=height,
        legend=dict(
            bgcolor="rgba(255,255,255,0.04)",
            bordercolor="rgba(255,255,255,0.12)",
            borderwidth=1,
            font=dict(size=11, color="#CBD5E1"),
        ),
    )
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.08)",
        color="#94A3B8",
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.06)",
        zerolinecolor="rgba(255,255,255,0.08)",
        color="#94A3B8",
    )
    return fig


def donut_talking_share(history: list[dict]) -> go.Figure:
    df = pd.DataFrame(history)
    if df.empty:
        return _apply_dark(go.Figure())
    df["words"] = df["english"].astype(str).apply(lambda t: len(t.split()))
    grouped = df.groupby("speaker")["words"].sum().reset_index()
    fig = go.Figure(
        data=[
            go.Pie(
                labels=grouped["speaker"].tolist(),
                values=grouped["words"].tolist(),
                hole=0.62,
                marker=dict(
                    colors=NEON_SEQUENCE[: len(grouped)],
                    line=dict(color="#0B0C10", width=3),
                ),
                textinfo="label+percent",
                textfont=dict(color="#F1F5F9", size=13, family="JetBrains Mono, monospace"),
                pull=[0.02] * len(grouped),
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="TALKING TIME · WORD SHARE",
            font=dict(family="Bricolage Grotesque, sans-serif", size=16, color="#F1F5F9"),
            x=0.02,
        ),
        annotations=[
            dict(
                text=f"<b>{int(grouped['words'].sum())}</b><br><span style='font-size:10px;color:#94A3B8;'>WORDS</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=26, color="#00E5FF", family="Bricolage Grotesque, sans-serif"),
            )
        ],
    )
    return _apply_dark(fig, height=380)


def bar_messages_per_speaker(history: list[dict]) -> go.Figure:
    df = pd.DataFrame(history)
    if df.empty:
        return _apply_dark(go.Figure())
    counts = df.groupby("speaker").size().reset_index(name="messages")
    fig = go.Figure(
        data=[
            go.Bar(
                x=counts["messages"].tolist(),
                y=counts["speaker"].tolist(),
                orientation="h",
                marker=dict(
                    color=counts["messages"].tolist(),
                    colorscale=[[0, "#00E5FF"], [0.5, "#B026FF"], [1, "#FF2E9A"]],
                    line=dict(color="rgba(255,255,255,0.15)", width=1),
                ),
                text=counts["messages"].tolist(),
                textposition="outside",
                textfont=dict(color="#F1F5F9", family="JetBrains Mono, monospace"),
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="MESSAGES · PER SPEAKER",
            font=dict(family="Bricolage Grotesque, sans-serif", size=16, color="#F1F5F9"),
            x=0.02,
        ),
        showlegend=False,
    )
    return _apply_dark(fig, height=280)


def line_sentiment_over_time(history: list[dict]) -> go.Figure:
    df = pd.DataFrame(history)
    if df.empty or "score" not in df.columns:
        return _apply_dark(go.Figure())
    df = df.reset_index().rename(columns={"index": "step"})
    df["step"] = df["step"] + 1

    fig = go.Figure()
    speakers = df["speaker"].unique().tolist()
    for i, sp in enumerate(speakers):
        sub = df[df["speaker"] == sp]
        color = NEON_SEQUENCE[i % len(NEON_SEQUENCE)]
        fig.add_trace(
            go.Scatter(
                x=sub["step"].tolist(),
                y=sub["score"].tolist(),
                mode="lines+markers",
                name=sp,
                line=dict(color=color, width=3, shape="spline"),
                marker=dict(size=11, color=color, line=dict(color="#0B0C10", width=2)),
                hovertemplate="<b>%{y:+.2f}</b><br>%{text}<extra>" + sp + "</extra>",
                text=sub["english"].astype(str).str[:80].tolist(),
            )
        )
    # 0 baseline
    fig.add_hline(
        y=0, line=dict(color="rgba(255,255,255,0.20)", width=1, dash="dot")
    )
    fig.update_layout(
        title=dict(
            text="SENTIMENT · MOOD OVER TIME",
            font=dict(family="Bricolage Grotesque, sans-serif", size=16, color="#F1F5F9"),
            x=0.02,
        ),
        xaxis_title="Message #",
        yaxis_title="Sentiment (-1 → 1)",
        xaxis=dict(range=[0.5, max(df["step"].max(), 5) + 0.5], dtick=1),
        yaxis=dict(range=[-1.15, 1.15], dtick=0.5),
    )
    return _apply_dark(fig, height=340)


def metric_strip(history: list[dict]) -> dict:
    """Compute latency proxy + word stats."""
    if not history:
        return dict(total_words=0, avg_words=0.0, positivity=0.0, unique=0)
    total_words = sum(len(str(h["english"]).split()) for h in history)
    unique = len({h["speaker"] for h in history})
    scores = [float(h.get("score", 0.0)) for h in history]
    positivity = round((sum(scores) / len(scores)) if scores else 0.0, 2)
    return dict(
        total_words=total_words,
        avg_words=round(total_words / max(len(history), 1), 1),
        positivity=positivity,
        unique=unique,
    )
