"""Export helpers — JSON, TXT and a styled PDF report."""
from __future__ import annotations

import io
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def to_json(history: list[dict]) -> str:
    return json.dumps(
        {
            "generated_at": datetime.now().isoformat(),
            "message_count": len(history),
            "conversation": history,
        },
        ensure_ascii=False,
        indent=2,
    )


def to_txt(history: list[dict]) -> str:
    lines = [
        "AI VOICE TRANSLATOR — TRANSCRIPT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Messages: {len(history)}",
        "=" * 60,
        "",
    ]
    for i, h in enumerate(history, 1):
        lines.append(f"[{i:03d}] {h['speaker']}  ·  sentiment={h.get('sentiment','NEU')} ({h.get('score',0):+.2f})")
        lines.append(f"  EN: {h['english']}")
        lines.append(f"  TR: {h['translation']}")
        lines.append("-" * 60)
    return "\n".join(lines)


def to_pdf(history: list[dict], title: str = "AI Voice Translator — Session Report") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "vt-title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=colors.HexColor("#0B0C10"),
        spaceAfter=6,
    )
    sub_style = ParagraphStyle(
        "vt-sub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14,
    )
    speaker_style = ParagraphStyle(
        "vt-spk",
        parent=styles["Heading4"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=colors.HexColor("#B026FF"),
        spaceAfter=2,
    )
    label_style = ParagraphStyle(
        "vt-lbl",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#0EA5E9"),
    )
    body_style = ParagraphStyle(
        "vt-body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#0B0C10"),
        leading=14,
        spaceAfter=4,
    )

    story = [
        Paragraph(title, title_style),
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ·  Messages: {len(history)}",
            sub_style,
        ),
    ]

    for i, h in enumerate(history, 1):
        header = f"#{i:03d} · {h['speaker']} · sentiment: {h.get('sentiment','NEU')} ({h.get('score',0):+.2f})"
        story.append(Paragraph(header, speaker_style))

        rows = [
            [Paragraph("<b>EN</b>", label_style), Paragraph(_esc(h["english"]), body_style)],
            [Paragraph("<b>TR</b>", label_style), Paragraph(_esc(h["translation"]), body_style)],
        ]
        tbl = Table(rows, colWidths=[0.5 * inch, 6.5 * inch])
        tbl.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#E0F2FE")),
                    ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#F3E8FF")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(tbl)
        story.append(Spacer(1, 10))

    doc.build(story)
    return buf.getvalue()


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
