"""Pure presentation layer for the Taxpayer Development Journey dashboard --
palette, CSS injection, and the evidence-tier tagging convention. No
dependency on Streamlit's multipage state, stage metadata, or any data
source: this module can be dropped into any Streamlit app unmodified.
"""

import streamlit as st

NAVY = "#1B3A5C"
GOLD = "#96591A"
SLATE = "#44546A"
CREAM = "#F7F1E5"
GRAY = "#595959"
WHITE = "#FFFFFF"

# The project's brand palette, sampled from the submission document's own
# section-header graphics -- distinct from the NAVY/GOLD site chrome above,
# used for the stage-specific hero/card treatment introduced in the Seed
# build and reused as-is here (not a per-stage palette; every stage's hero
# uses these same values). AMBER is the one color not sourced from the
# document -- a warm accent for "here's the caveat" / illustrative-bridge
# moments, chosen to complement the green rather than clash with it.
GREEN = "#256E29"
GREEN_DARK = "#123815"
TINT = "#D8E7D8"
TINT_LIGHT = "#E5EFE6"
AMBER = "#C97A1D"

EVIDENCE_TIER_HELP = (
    "Every figure on this dashboard carries the same evidence-tier labels used "
    "in the written submission: **model-calculated**, **causal estimate**, "
    "**first-pass**, or **hypothesis** -- so no number is presented with more "
    "confidence than it has earned."
)

_TIER_NAMES = {
    "model": ("MODEL-CALCULATED", "tier-model"),
    "causal": ("CAUSAL ESTIMATE", "tier-causal"),
    "firstpass": ("FIRST-PASS", "tier-firstpass"),
    "hypothesis": ("HYPOTHESIS", "tier-hypothesis"),
}


def inject_base_style():
    st.markdown(
        f"""
        <style>
        .stApp {{ background-color: #FFFFFF; }}
        h1, h2, h3 {{ color: {NAVY}; font-family: Georgia, 'Cambria', serif; }}
        .tdj-callout {{
            background-color: {CREAM};
            border-left: 6px solid {GOLD};
            padding: 0.9rem 1.1rem;
            border-radius: 2px;
            margin: 0.6rem 0 1.1rem 0;
        }}
        .tdj-callout .label {{
            color: {NAVY}; font-weight: 700; letter-spacing: 0.05em;
            font-size: 0.78rem; text-transform: uppercase; margin-bottom: 0.3rem;
        }}
        .tdj-tag {{
            display: inline-block; font-size: 0.72rem; font-weight: 700;
            letter-spacing: 0.03em; text-transform: uppercase;
            padding: 0.12rem 0.5rem; border-radius: 3px; color: white;
            margin-right: 0.4rem;
        }}
        .tier-model {{ background-color: #2E7D32; }}
        .tier-causal {{ background-color: {NAVY}; }}
        .tier-firstpass {{ background-color: {GOLD}; }}
        .tier-hypothesis {{ background-color: #8A8A8A; }}
        .tdj-stagehead {{
            background-color: {NAVY}; color: white; padding: 0.6rem 1rem;
            border-radius: 4px; font-size: 0.95rem; margin-bottom: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_hero_style(texture_b64: str = ""):
    """The green hero-banner + card system introduced in the Seed build
    (composed CSS gradient + a real network-texture asset via
    mix-blend-mode, rather than a static per-stage banner image -- see
    pages/1_Seed.py for why). Centralized here once it was clearly a
    reused pattern rather than a one-off, so a third/fourth stage can
    adopt it without copy-pasting this block again. Call once per page,
    after inject_base_style(). texture_b64 is the base64-encoded
    contents of assets/network_texture.png (or "" to render the hero
    as a flat gradient with no texture overlay).

    Grey (not a third accent hue) marks the "insufficient/unavailable"
    state -- deliberately matching the existing evidence_tag()
    hypothesis tier's grey, not introducing a new color for the same
    idea of "lowest confidence / nothing to show here."
    """
    st.markdown(
        f"""
        <style>
        .tdj-hero {{
            position: relative; border-radius: 10px; overflow: hidden;
            padding: 2.1rem 2.3rem; margin: 0.4rem 0 1.4rem 0;
            background: linear-gradient(135deg, {GREEN} 0%, {GREEN_DARK} 100%);
            border-bottom: 5px solid {AMBER};
        }}
        .tdj-hero::before {{
            content: ""; position: absolute; inset: 0;
            background-image: url("data:image/png;base64,{texture_b64}");
            background-size: cover; background-position: center;
            mix-blend-mode: multiply; opacity: 0.9; pointer-events: none;
        }}
        .tdj-hero-inner {{ position: relative; z-index: 1; }}
        .tdj-hero-title {{
            color: white; font-family: Georgia, 'Cambria', serif;
            font-size: 2rem; font-weight: 700; margin: 0 0 0.3rem 0; line-height: 1.15;
        }}
        .tdj-hero-sub {{ color: {TINT}; font-size: 1.02rem; max-width: 46rem; margin: 0; }}
        .tdj-card {{
            background: {TINT_LIGHT}; border: 1px solid {TINT}; border-radius: 8px;
            padding: 1rem 1.2rem; margin: 0.6rem 0;
        }}
        .tdj-note-card {{
            background: #FDF3E7; border-left: 5px solid {AMBER}; border-radius: 6px;
            padding: 0.9rem 1.1rem; margin: 0.8rem 0;
        }}
        .tdj-note-label {{
            color: {AMBER}; font-weight: 700; font-size: 0.74rem;
            letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.3rem;
        }}
        .tdj-insufficient-card {{
            background: #F4F4F4; border: 1px dashed #9A9A9A; border-radius: 8px;
            padding: 1rem 1.2rem; margin: 0.8rem 0; color: #555;
        }}
        .tdj-insufficient-label {{
            color: #767676; font-weight: 700; font-size: 0.74rem;
            letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.3rem;
        }}
        .tdj-badge {{
            display: inline-block; background: {GREEN}; color: white;
            font-family: Georgia, 'Cambria', serif; font-weight: 700;
            padding: 0.35rem 0.9rem; border-radius: 99px; font-size: 0.95rem;
            margin: 0.2rem 0.3rem 0.2rem 0;
        }}
        .tdj-section-tag {{
            display: inline-block; color: {GREEN}; font-weight: 700;
            font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase;
            border: 1px solid {GREEN}; border-radius: 99px;
            padding: 0.15rem 0.7rem; margin-bottom: 0.6rem;
        }}
        .tdj-demo-note {{ color: #7A7A7A; font-size: 0.8rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def callout(label: str, body_markdown: str):
    st.markdown(
        f"""<div class="tdj-callout">
        <div class="label">{label}</div>
        {body_markdown}
        </div>""",
        unsafe_allow_html=True,
    )


def evidence_tag(tier: str):
    """tier: one of 'model', 'causal', 'firstpass', 'hypothesis'."""
    text, cls = _TIER_NAMES[tier]
    st.markdown(f'<span class="tdj-tag {cls}">{text}</span>', unsafe_allow_html=True)
