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
