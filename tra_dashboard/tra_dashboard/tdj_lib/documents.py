"""PDF generation for this project's three downloadable artifacts: Asset's
Verification Report and Digital Asset Profile, and Legacy's Kodi Legacy
Certificate.

Pure rendering only -- none of these functions compute anything about a
score. Each takes an already-assembled list of component dicts (built
by the calling page from its own session-state inputs) and lays it out
as PDF bytes in memory via reportlab, returned straight to
st.download_button. No temp files, no disk writes -- BytesIO only, so
this works identically under Streamlit Cloud's ephemeral filesystem as
it does locally.

Uses reportlab's built-in Times-Roman/Times-Bold as the closest
built-in serif to the project's Georgia/Lora-style headings elsewhere
-- no custom font file exists in this project's assets to embed, and
adding one is out of scope for what this build needs.
"""

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

GREEN = colors.HexColor("#256E29")
GREEN_DARK = colors.HexColor("#123815")
TINT_LIGHT = colors.HexColor("#E5EFE6")
AMBER = colors.HexColor("#C97A1D")
INK = colors.HexColor("#222222")
MUTED = colors.HexColor("#666666")

DEMO_MARK = "PILOT DEMONSTRATION — ILLUSTRATIVE DATA, NOT VERIFIED TRA RECORDS"
CERTIFICATE_DEMO_MARK = (
    "PILOT DEMONSTRATION — ILLUSTRATIVE DOCUMENT, NOT A LEGALLY BINDING "
    "CERTIFICATE OR VERIFIED TRA RECORD"
)

_styles = {
    "title": ParagraphStyle("title", fontName="Times-Bold", fontSize=20, leading=26, textColor=GREEN_DARK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10, leading=13, textColor=MUTED, spaceAfter=14),
    "subtitle_center": ParagraphStyle("subtitle_center", fontName="Helvetica", fontSize=10, leading=13, textColor=MUTED, alignment=1, spaceAfter=2),
    "h2": ParagraphStyle("h2", fontName="Times-Bold", fontSize=13, textColor=GREEN_DARK, spaceBefore=14, spaceAfter=6),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13.5),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=8, textColor=MUTED, leading=11),
    "demo": ParagraphStyle("demo", fontName="Helvetica-Bold", fontSize=8.5, textColor=AMBER, leading=11),
    "score_block": ParagraphStyle("score_block", fontName="Times-Bold", fontSize=44, leading=50, textColor=GREEN_DARK, alignment=1, spaceAfter=4),
    "band": ParagraphStyle("band", fontName="Helvetica-Bold", fontSize=13, textColor=GREEN, alignment=1, spaceAfter=2),
    "credential_headline": ParagraphStyle("credential_headline", fontName="Times-Bold", fontSize=17, leading=21, textColor=GREEN_DARK, alignment=1, spaceAfter=2),
}


def _demo_banner(text: str = DEMO_MARK):
    return Table(
        [[Paragraph(f"⚠ {text}", _styles["demo"])]],
        colWidths=[170 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDF3E7")),
            ("BOX", (0, 0), (-1, -1), 0.75, AMBER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]),
    )


def build_asset_verification_report(person_name: str, components: list, total_score: int,
                                      max_score: int, generated_at: datetime = None) -> bytes:
    """Audit-style document: full component breakdown with each one's
    real/illustrative status, generation metadata, methodology note.

    components: list of dicts with keys name, status, points, max_points,
    tier ("real" or "illustrative"), note.
    """
    generated_at = generated_at or datetime.now()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=16 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    story = []

    story.append(Paragraph("Asset Verification Report", _styles["title"]))
    story.append(Paragraph("Mali Alama — Verified Economic Identity, TRA Innovation Pilot", _styles["subtitle"]))
    story.append(_demo_banner())
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<b>Prepared for:</b> {person_name or 'Demo taxpayer'}<br/>"
        f"<b>Generated:</b> {generated_at.strftime('%d %B %Y, %H:%M')}<br/>"
        f"<b>Overall score:</b> {total_score} / {max_score}",
        _styles["body"],
    ))

    story.append(Paragraph("Component Breakdown", _styles["h2"]))
    table_data = [["Component", "Status", "Evidence", "Points"]]
    for c in components:
        table_data.append([
            Paragraph(c["name"], _styles["body"]),
            Paragraph(c["status"], _styles["body"]),
            Paragraph("Real (computed)" if c["tier"] == "real" else "Illustrative (self-reported)", _styles["small"]),
            Paragraph(f"{c['points']} / {c['max_points']}", _styles["body"]),
        ])
    t = Table(table_data, colWidths=[52 * mm, 55 * mm, 40 * mm, 23 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TINT_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    for c in components:
        if c.get("note"):
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>{c['name']}:</b> {c['note']}", _styles["small"]))

    story.append(Paragraph("Methodology", _styles["h2"]))
    story.append(Paragraph(
        "Score computed on a 0–1000 illustrative scale: a neutral baseline of 700, plus "
        "component contributions above. Vehicle Registration, Rental Declarations, and "
        "Ownership Stability are self-reported for this demonstration — the real Core Asset "
        "Score is designed to run entirely on TRA-administered vehicle and rental records. "
        "Property Verification is always 0 in this scope; it activates only under a future "
        "Full Asset Score using land, building, and mortgage data via data-sharing agreements "
        "not yet in place. Ngazi Standing is the one component computed from real session "
        "data — this taxpayer's actual progression on the Enterprise stage's ladder, not a "
        "self-reported input.",
        _styles["body"],
    ))
    story.append(Paragraph(
        "This report follows the same evidence-tier discipline used throughout this project: "
        "figures are never presented with more confidence than their underlying source "
        "supports. Nothing in this document has been verified against real TRA records.",
        _styles["small"],
    ))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 4))
    story.append(_demo_banner())

    doc.build(story)
    return buf.getvalue()


def build_digital_asset_profile(person_name: str, total_score: int, max_score: int,
                                  confidence_band: str, highlights: list, benefits: list,
                                  generated_at: datetime = None) -> bytes:
    """Shareable, portable-credential-style single page: headline score,
    qualitative band, key verified components at a glance, and the
    benefits panel with its illustrative-only disclaimer. Visually
    distinct from the audit report -- no component-by-component table,
    no methodology essay, just what someone could plausibly show a lender.

    highlights: list of short strings (e.g. "Vehicle Registration: Verified").
    benefits: list of (title, note, is_real) tuples.
    """
    generated_at = generated_at or datetime.now()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=16 * mm, leftMargin=24 * mm, rightMargin=24 * mm,
    )
    story = []

    story.append(_demo_banner())
    story.append(Spacer(1, 14))
    story.append(Paragraph("Verified Economic Identity", _styles["subtitle_center"]))
    story.append(Paragraph("Digital Asset Profile", _styles["credential_headline"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f'{total_score}<br/><font size=11 color="#666666">out of {max_score}</font>',
        _styles["score_block"],
    ))
    story.append(Paragraph(confidence_band, _styles["band"]))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=GREEN, thickness=1.2))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Verified at a glance", _styles["h2"]))
    for h in highlights:
        story.append(Paragraph(f"✓ {h}", _styles["body"]))

    story.append(Paragraph("What this identity unlocks", _styles["h2"]))
    for title, note, is_real in benefits:
        tag = "Earned" if is_real else "Illustrative"
        story.append(Paragraph(f"<b>{title}</b> <font size=8 color='#666666'>({tag})</font>", _styles["body"]))
        story.append(Paragraph(note, _styles["small"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Loan-verification, collateral, and preferred-borrower examples above illustrate "
        "potential value only. No financial institution or government partnership currently "
        "exists — realizing these benefits requires future negotiation and is not a "
        "redeemable offer today.",
        _styles["small"],
    ))

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        f"{person_name or 'Demo taxpayer'} · Generated {generated_at.strftime('%d %B %Y')}",
        _styles["small"],
    ))
    story.append(Spacer(1, 8))
    story.append(_demo_banner())

    doc.build(story)
    return buf.getvalue()


def build_legacy_certificate(person_name: str, components: list, total_score: int,
                               max_score: int, succession: dict = None,
                               generated_at: datetime = None) -> bytes:
    """Kodi Legacy Certificate -- reuses this module's shared styles and
    _demo_banner() rather than a parallel document approach. Framed as
    continuity/stewardship documentation, not a transfer instrument: the
    "digitally signed" mark is explicitly labeled illustrative, and the
    certificate carries the stronger, certificate-specific demo mark
    (CERTIFICATE_DEMO_MARK) rather than the generic one, since this is the
    one artifact in the project most easily mistaken for something with
    legal effect once it's out of the app's own context.

    components: same shape as build_asset_verification_report's.
    succession: optional dict with keys scenario ("sustained"/"lapsed"),
    successor_score, live_score_at_month, month -- omitted entirely from
    the certificate if no succession was simulated this session, rather
    than showing a fabricated default.
    """
    generated_at = generated_at or datetime.now()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=16 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    story = []

    story.append(Paragraph("Kodi Legacy Certificate", _styles["title"]))
    story.append(Paragraph("Verified Compliance Continuity — TRA Innovation Pilot", _styles["subtitle"]))
    story.append(_demo_banner(CERTIFICATE_DEMO_MARK))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"<b>Taxpayer:</b> {person_name or 'Demo taxpayer'} (placeholder identifier)<br/>"
        f"<b>Issued:</b> {generated_at.strftime('%d %B %Y, %H:%M')}<br/>"
        f"<b>Kodi Legacy Score:</b> {total_score} / {max_score}",
        _styles["body"],
    ))

    story.append(Paragraph("This certificate preserves — it does not transfer", _styles["h2"]))
    story.append(Paragraph(
        "This document records a verified compliance history for continuity and "
        "stewardship purposes. It does not transfer any legal tax obligation, and "
        "reaching an approved successor does not hand over this score for free — "
        "see Succession Status below for how inherited standing is treated as "
        "provenance, not entitlement.",
        _styles["body"],
    ))

    story.append(Paragraph("Component Breakdown", _styles["h2"]))
    table_data = [["Component", "Status", "Evidence", "Points"]]
    for c in components:
        table_data.append([
            Paragraph(c["name"], _styles["body"]),
            Paragraph(c["status"], _styles["body"]),
            Paragraph("Real (computed)" if c["tier"] == "real" else "Illustrative (self-reported)", _styles["small"]),
            Paragraph(f"{c['points']} / {c['max_points']}", _styles["body"]),
        ])
    t = Table(table_data, colWidths=[45 * mm, 62 * mm, 40 * mm, 23 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, TINT_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Paragraph("Succession Status", _styles["h2"]))
    if succession:
        scenario_label = "sustains strong compliance" if succession["scenario"] == "sustained" else "lets compliance lapse"
        story.append(Paragraph(
            f"A hypothetical successor scenario was simulated this session: successor "
            f"{scenario_label}, illustrative own-record score {succession['successor_score']} / 100. "
            f"At month {succession['month']} of the 3-year transition window, the live "
            f"eligibility score is {succession['live_score_at_month']} / {max_score} — blending "
            "monthly from this certificate's inherited score toward the successor's own "
            "record, fully replaced by month 36. The inherited score above remains a "
            "historical reference only; it is not the successor's live standing.",
            _styles["body"],
        ))
    else:
        story.append(Paragraph(
            "No succession was simulated this session. This certificate reflects the "
            "current taxpayer's own record only.",
            _styles["body"],
        ))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "✒ Digitally signed — illustrative mark only, not a cryptographic or legal signature.",
        ParagraphStyle("sig", fontName="Times-Italic", fontSize=10, textColor=GREEN_DARK),
    ))
    story.append(Spacer(1, 10))
    story.append(_demo_banner(CERTIFICATE_DEMO_MARK))

    doc.build(story)
    return buf.getvalue()
