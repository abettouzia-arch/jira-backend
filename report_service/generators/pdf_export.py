"""
PDF export utilities for Report Service.

Generates a readable PDF migration report from a structured report dict.
"""

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "generated_reports"


def export_report_to_pdf(
    report: dict,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> str:
    """Export a migration report to PDF and return the file path."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_id = report.get("report_id", "unknown-report")
    file_path = output_path / f"{report_id}.pdf"

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(report.get("title", "Migration Report"), styles["Title"]))
    story.append(Spacer(1, 16))

    _add_markdown_text(
        story,
        report.get("ai_summary") or report.get("summary", ""),
        styles,
    )

    story.append(Spacer(1, 12))
    story.append(Paragraph("Migration Score", styles["Heading2"]))
    story.append(Paragraph(f"{report.get('migration_score', 0)}/100", styles["BodyText"]))
    recommendation_text = _clean_inline(report.get("migration_recommendation", ""))
    story.append(Paragraph(recommendation_text, styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Risk Overview", styles["Heading2"]))
    risk = report.get("sections", {}).get("risk_overview", {})
    risk_table = Table([
        ["Risk", "Count"],
        ["Blockers", risk.get("blockers", 0)],
        ["Major", risk.get("major", 0)],
        ["Minor", risk.get("minor", 0)],
        ["Info", risk.get("info", 0)],
        ["Incompatible", risk.get("incompatible", 0)],
        ["Partial", risk.get("partial", 0)],
        ["Compatible", risk.get("compatible", 0)],
    ])
    risk_table.setStyle(_table_style())
    story.append(risk_table)
    story.append(Spacer(1, 16))

    blockers = report.get("sections", {}).get("blockers", [])
    story.append(Paragraph("Blockers", styles["Heading2"]))

    if blockers:
        blocker_rows = [["Component", "Plugin", "Risk", "Status"]]
        for blocker in blockers:
            blocker_rows.append([
                blocker.get("component_id", ""),
                blocker.get("plugin", ""),
                blocker.get("risk_level", ""),
                blocker.get("overall_status", ""),
            ])

        blockers_table = Table(blocker_rows, repeatRows=1)
        blockers_table.setStyle(_table_style())
        story.append(blockers_table)
    else:
        story.append(Paragraph("No blockers detected.", styles["BodyText"]))

    story.append(Spacer(1, 16))

    story.append(Paragraph("Recommendations", styles["Heading2"]))
    recommendations = report.get("sections", {}).get("recommendations", [])

    if recommendations:
        for recommendation in recommendations[:10]:
            text = (
                f"<b>{_clean_inline(recommendation.get('priority', ''))}</b> — "
                f"{_clean_inline(recommendation.get('component_id', ''))}: "
                f"{_clean_inline(recommendation.get('action', ''))}"
            )
            story.append(Paragraph(text, styles["BodyText"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No prioritized recommendations.", styles["BodyText"]))

    doc.build(story)
    return str(file_path)


def _add_markdown_text(story: list, text: str, styles) -> None:
    """Convert simple Markdown text into ReportLab paragraphs."""
    lines = text.splitlines()

    for line in lines:
        line = line.strip()

        if not line or line == "---":
            story.append(Spacer(1, 6))
            continue

        if line.startswith("## "):
            story.append(Paragraph(_clean_inline(line[3:]), styles["Heading1"]))
            story.append(Spacer(1, 8))
            continue

        if line.startswith("### "):
            story.append(Paragraph(_clean_inline(line[4:]), styles["Heading2"]))
            story.append(Spacer(1, 6))
            continue

        if line.startswith("*   ") or line.startswith("- "):
            content = line.replace("*   ", "", 1).replace("- ", "", 1)
            story.append(Paragraph(f"• {_clean_inline(content)}", styles["BodyText"]))
            continue

        numbered_match = re.match(r"^\d+\.\s+(.*)", line)
        if numbered_match:
            story.append(Paragraph(_clean_inline(line), styles["BodyText"]))
            continue

        story.append(Paragraph(_clean_inline(line), styles["BodyText"]))


def _clean_inline(text: str) -> str:
    """Clean inline Markdown and make it ReportLab-safe."""
    text = str(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.*?)`", r"<font name='Courier'>\1</font>", text)

    return text


def _table_style() -> TableStyle:
    """Return default table style."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ])
