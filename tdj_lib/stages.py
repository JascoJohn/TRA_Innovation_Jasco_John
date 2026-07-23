"""Stage registry and cross-page navigation for the six-stage taxpayer
lifecycle (Seed -> Entry -> Active -> Enterprise -> Asset -> Legacy).
Depends only on styling.py (for NAVY) and Streamlit's page_link -- no
data-source dependency, so a new project can reuse this stage-navigation
shape even with a completely different set of stages by editing STAGES
alone.
"""

import streamlit as st

STAGES = [
    {"key": "seed", "label": "Seed", "verb": "Learn", "mechanism": "Experience",
     "page": "pages/1_Seed.py", "icon": "🌱"},
    {"key": "entry", "label": "Entry", "verb": "Join", "mechanism": "Targeting",
     "page": "pages/2_Entry.py", "icon": "🚪"},
    {"key": "active", "label": "Active", "verb": "Understand", "mechanism": "Calculation",
     "page": "pages/3_Active.py", "icon": "⚖️"},
    {"key": "enterprise", "label": "Enterprise", "verb": "Progress", "mechanism": "Status",
     "page": "pages/4_Enterprise.py", "icon": "📈"},
    {"key": "asset", "label": "Asset", "verb": "Reveal", "mechanism": "Reciprocity",
     "page": "pages/5_Asset.py", "icon": "🏠"},
    {"key": "legacy", "label": "Legacy", "verb": "Preserve", "mechanism": "Inheritance",
     "page": "pages/6_Legacy.py", "icon": "🕊️"},
]


def stage_header(icon: str, stage_name: str, verb: str, mechanism: str, position: str):
    st.markdown(
        f"""<div class="tdj-stagehead">
        {icon}&nbsp;&nbsp;<b>{stage_name} Stage</b> &nbsp;|&nbsp; {verb} &rarr; {mechanism}
        &nbsp;&nbsp;&nbsp;<span style="opacity:0.75;">Stage {position} of 6</span>
        </div>""",
        unsafe_allow_html=True,
    )


def stage_nav_footer(current_key: str):
    idx = next(i for i, s in enumerate(STAGES) if s["key"] == current_key)
    cols = st.columns(3)
    with cols[0]:
        if idx > 0:
            prev_s = STAGES[idx - 1]
            st.page_link(prev_s["page"], label=f"← {prev_s['label']}", icon=prev_s["icon"])
    with cols[1]:
        st.page_link("Home.py", label="Overview", icon="🧭")
    with cols[2]:
        if idx < len(STAGES) - 1:
            next_s = STAGES[idx + 1]
            st.page_link(next_s["page"], label=f"{next_s['label']} →", icon=next_s["icon"])
