import base64
import os
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from common import (
    inject_base_style, inject_hero_style, stage_header, callout, evidence_tag,
    stage_nav_footer, GREEN, GREEN_DARK, AMBER,
    demo_safety_banner,
    build_legacy_certificate,
)

st.set_page_config(page_title="Legacy — Kodi Legacy Score", page_icon="🕊️", layout="wide")
inject_base_style()
stage_header("🕊️", "Legacy", "Preserve", "Continuity", "6")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_PERSONA_PATH = os.path.join(ASSETS_DIR, "legacy_persona_mzeehamisi.png")
_TEXTURE_PATH = os.path.join(ASSETS_DIR, "network_texture.png")


@st.cache_data(show_spinner=False)
def _b64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


inject_hero_style(_b64_file(_TEXTURE_PATH) if os.path.exists(_TEXTURE_PATH) else "")

# ---------------------------------------------------------------------------
# Score construction. Weights match the document's own mockup exactly
# (+45 / +20 / +15 / +10 / +10 = 100). Filing History, TIN Age, and
# Compliance Flags stay illustrative self-report -- no real TRA filing
# dataset exists in this project. Ngazi Status and Asset Score are the two
# components this build makes real, computed from the actual session
# carried forward from Enterprise and Asset rather than self-reported.
# ---------------------------------------------------------------------------
FILING_MAX, TIN_MAX, NGAZI_MAX, ASSET_MAX, COMPLIANCE_MAX = 45, 20, 15, 10, 10
LEGACY_MAX = FILING_MAX + TIN_MAX + NGAZI_MAX + ASSET_MAX + COMPLIANCE_MAX  # 100

# Ngazi Status -> points: graduated across the same 6-rung ladder Enterprise
# and Asset already use, rescaled from Asset's 0-40 Ngazi Standing down to
# this component's 0-15 ceiling (roughly *0.375, rounded to clean steps) --
# proportional partial credit, not all-or-nothing, matching the reasoning
# already established for Asset's Ngazi Standing component.
NGAZI_STATUS_SCALE = {
    "TIN Obtained": 3,
    "First Return Filed": 5,
    "Six Months Compliant": 8,
    "EFD Connected": 10,
    "Annual Filing Completed": 12,
}  # "Established Taxpayer Status" (full graduation) maps to NGAZI_MAX (15) explicitly below

# Asset Score -> points: linear from Asset's fixed floor (700, everyone
# starts there) to this session's achievable ceiling (800, per Asset's own
# BASE_SCORE + component design) mapped onto 0-10, clipped. The document's
# own illustrative example uses 760 for this component -- (760-700)/100 =
# 0.6 -> 6/10 under this mapping, which is also what Asset's own default
# inputs produce before anyone touches a slider, so this reproduces the
# document's reference point rather than contradicting it.
ASSET_SCORE_FLOOR, ASSET_SCORE_CEILING = 700, 800


def _asset_score_points(total_score: int) -> int:
    span = ASSET_SCORE_CEILING - ASSET_SCORE_FLOOR
    frac = max(0.0, min(1.0, (total_score - ASSET_SCORE_FLOOR) / span))
    return round(ASSET_MAX * frac)


# ---------------------------------------------------------------------------
# Recognize real carried-forward session data from Enterprise and Asset.
# Strictly read-only here -- if either is absent, the corresponding
# component honestly shows 0 with a "not yet built" explanation, never a
# fabricated default.
# ---------------------------------------------------------------------------
enterprise_milestone = st.session_state.get("ngazi_current_milestone")
enterprise_graduated = bool(st.session_state.get("ngazi_established_status_reached"))
came_from_enterprise = enterprise_milestone is not None

asset_summary = st.session_state.get("asset_score_summary")
came_from_asset = asset_summary is not None

if enterprise_graduated:
    ngazi_pts = NGAZI_MAX
elif came_from_enterprise:
    ngazi_pts = NGAZI_STATUS_SCALE.get(enterprise_milestone, 0)
else:
    ngazi_pts = 0

asset_pts = _asset_score_points(asset_summary["total_score"]) if came_from_asset else 0

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
hc1, hc2 = st.columns([2, 1])
with hc1:
    st.markdown(
        """
        <div class="tdj-hero"><div class="tdj-hero-inner">
            <div class="tdj-hero-title">A record that doesn't have to end</div>
            <p class="tdj-hero-sub">Kodi Legacy preserves verified compliance history and
            enables responsible succession — a designated successor continues the
            relationship, they don't inherit a free score.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )
with hc2:
    if os.path.exists(_PERSONA_PATH):
        st.image(_PERSONA_PATH, width="stretch")

if came_from_enterprise or came_from_asset:
    bits = []
    if came_from_enterprise:
        bits.append(f"Ngazi progress (<b>{enterprise_milestone}</b>)")
    if came_from_asset:
        bits.append(f"Asset Score (<b>{asset_summary['total_score']} / {asset_summary['max_score']}</b>)")
    st.markdown(
        '<div class="tdj-note-card"><div class="tdj-note-label">Welcome back</div>'
        f"<p>We can see your real {' and '.join(bits)} from earlier this session — both "
        "count as computed, not self-reported, components below.</p></div>",
        unsafe_allow_html=True,
    )

with st.expander("Why Kodi Legacy exists"):
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**The problem**")
        st.write(
            "Mzee Hamisi has run his family business for over 45 years, with decades of "
            "filing history and trust built with TRA. None of that automatically "
            "continues when he retires or passes the business on — a successor inherits "
            "the assets, but not the history behind them. The objective isn't to "
            "transfer legal tax obligations — it's to preserve verified compliance "
            "history."
        )
        st.markdown("**The mechanism**")
        st.write(
            "Two linked findings, not one. Generativity research shows people invest "
            "more in long-term value when they believe it will outlast them. "
            "Reputation research shows people work harder to maintain a trusted "
            "relationship when the reputation itself retains value over time. "
            "Compliance today has no intergenerational value — this stage gives it one."
        )
    with c2:
        evidence_tag("firstpass")
        st.caption("First-pass, low confidence")
        st.metric("Cost", "TZS 700M")
        st.metric("Modeled revenue", "TZS 2.5B")
        st.metric("ROI", "~3.6x")
        st.caption("Illustrative — revenue/ROI unmigrated in this pipeline.")

st.divider()

# ===========================================================================
# Score dashboard
# ===========================================================================
st.markdown("## Build your Legacy profile")
st.caption(
    "Three honest, self-reported inputs, plus two components computed from what "
    "actually happened earlier this session. Nothing here is saved beyond this "
    "session."
)

demo_safety_banner()
person_name = st.text_input(
    "Your name (for the certificate generated below — optional)",
    value=st.session_state.get("engazi_name", ""), key="legacy_name_input",
    placeholder="e.g. Mzee Hamisi",
)

ic1, ic2 = st.columns(2)
with ic1:
    on_time_years = st.slider("Years filed on time (of last 15)", 0, 15, 14, key="legacy_filing")
    tin_age = st.slider("Years of continuous registration (TIN age)", 0, 30, 27, key="legacy_tin")
with ic2:
    compliance_flags = st.slider("Outstanding compliance flags", 0, 5, 0, key="legacy_flags")

filing_pts = round(FILING_MAX * (on_time_years / 15))
tin_pts = round(TIN_MAX * min(tin_age / 27, 1))
compliance_pts = max(0, COMPLIANCE_MAX - compliance_flags * 4)

total = filing_pts + tin_pts + ngazi_pts + asset_pts + compliance_pts

components = [
    dict(name="Filing History", status=f"{on_time_years} of 15 years on time",
         points=filing_pts, max_points=FILING_MAX, tier="illustrative", note=None),
    dict(name="TIN Longevity", status=f"{tin_age} years",
         points=tin_pts, max_points=TIN_MAX, tier="illustrative", note=None),
    dict(
        name="Ngazi Status",
        status=(enterprise_milestone if came_from_enterprise else "Not yet built — reach Ngazi first")
               + (" (graduated)" if enterprise_graduated else ""),
        points=ngazi_pts, max_points=NGAZI_MAX, tier="real",
        note=("Computed from your actual Enterprise-stage progression this session."
              if came_from_enterprise else
              "Reach Established Taxpayer Status in Ngazi (Enterprise stage) to build "
              "this component honestly — showing 0 rather than a fabricated default."),
    ),
    dict(
        name="Asset Score",
        status=f"{asset_summary['total_score']} / {asset_summary['max_score']}" if came_from_asset
               else "Not yet built — visit Asset first",
        points=asset_pts, max_points=ASSET_MAX, tier="real",
        note=("Computed from your actual Asset Score this session."
              if came_from_asset else
              "Generate a Verified Economic Identity in the Asset stage to build this "
              "component honestly — showing 0 rather than a fabricated default."),
    ),
    dict(name="Compliance History", status=f"{compliance_flags} outstanding flag(s)",
         points=compliance_pts, max_points=COMPLIANCE_MAX, tier="illustrative", note=None),
]

score_fig = go.Figure(go.Bar(
    y=[c["name"] for c in components][::-1], x=[c["points"] for c in components][::-1],
    orientation="h",
    marker_color=[GREEN if c["tier"] == "real" else "#9CC79F" for c in components][::-1],
    text=[f"{c['points']} / {c['max_points']}" for c in components][::-1], textposition="outside",
))
score_fig.update_layout(xaxis_range=[0, 50], height=280, margin=dict(t=10, b=10), xaxis_title="Points contributed")
st.plotly_chart(score_fig, width="stretch")

lc1, lc2 = st.columns([1, 2])
with lc1:
    st.metric("Kodi Legacy Score", f"{total} / {LEGACY_MAX}")
with lc2:
    for c in components:
        tag_col = GREEN if c["tier"] == "real" else "#8A8A8A"
        tag_txt = "REAL" if c["tier"] == "real" else "ILLUSTRATIVE"
        st.markdown(
            f"<div style='display:flex; justify-content:space-between; padding:0.2rem 0; "
            f"font-size:0.85rem;'><span><span style='color:{tag_col}; font-weight:700; "
            f"font-size:0.66rem; margin-right:0.5rem;'>{tag_txt}</span>{c['name']}</span>"
            f"<b>{c['points']} / {c['max_points']}</b></div>",
            unsafe_allow_html=True,
        )

st.divider()

# ===========================================================================
# Succession simulation
# ===========================================================================
st.markdown("## Succession simulation")
st.write(
    "On an approved succession, the successor sees the predecessor's score as a "
    "**visible historical reference** — provenance, not entitlement. The score "
    "governing live eligibility for succession benefits blends over a **three-year "
    "transition window**, shifting monthly toward the successor's own record. This "
    "closes the most direct abuse route: a business acquired solely to inherit a high "
    "score without sustaining the behavior that earned it."
)

scenario = st.radio(
    "Hypothetical successor scenario",
    options=["sustained", "lapsed"],
    format_func=lambda k: {
        "sustained": "Successor sustains strong compliance going forward",
        "lapsed": "Successor lets compliance lapse",
    }[k],
    horizontal=True, key="legacy_succession_scenario",
)
SUSTAINED_SUCCESSOR_SCORE, LAPSED_SUCCESSOR_SCORE = 82, 20
successor_score = SUSTAINED_SUCCESSOR_SCORE if scenario == "sustained" else LAPSED_SUCCESSOR_SCORE
st.caption(
    f"Illustrative successor own-record score for this scenario: {successor_score} / 100 "
    "— what the successor's own filing behavior would score on its own, with no "
    "inheritance at all."
)

months_since = st.slider("Months since succession (inspect a point in time)", 0, 36, 12, key="legacy_months")

months_range = list(range(0, 37, 3))


def _blend_curve(successor_target):
    return [round(total * (1 - min(m / 36, 1)) + successor_target * min(m / 36, 1)) for m in months_range]


sustained_curve = _blend_curve(SUSTAINED_SUCCESSOR_SCORE)
lapsed_curve = _blend_curve(LAPSED_SUCCESSOR_SCORE)
live_score_active = round(total * (1 - min(months_since / 36, 1)) + successor_score * min(months_since / 36, 1))

blend_fig = go.Figure()
blend_fig.add_trace(go.Scatter(
    x=months_range, y=sustained_curve, mode="lines+markers", name="Successor sustains compliance",
    line=dict(color=GREEN, width=3),
))
blend_fig.add_trace(go.Scatter(
    x=months_range, y=lapsed_curve, mode="lines+markers", name="Successor lets compliance lapse",
    line=dict(color=AMBER, width=3, dash="dash"),
))
blend_fig.add_hline(y=total, line_dash="dot", line_color="#888", annotation_text="Inherited reference (historical only)")
blend_fig.add_vline(x=months_since, line_dash="dash", line_color="#444")
blend_fig.update_layout(
    height=340, margin=dict(t=20, b=10),
    xaxis_title="Months since succession", yaxis_title="Live eligibility score",
    yaxis_range=[0, 100], plot_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(blend_fig, width="stretch")

st.metric(
    f"Live eligibility score at month {months_since} ({scenario} scenario)",
    f"{live_score_active} / {LEGACY_MAX}",
    delta=f"{live_score_active - total} vs. inherited reference",
)
st.caption(
    "Both trajectories start at the same inherited score and reach the same point at "
    "month 36 (the successor's own record, in full) — only the path between differs. "
    "Inherited standing decays toward whatever the successor actually sustains; it "
    "isn't kept just because it was once earned."
)

st.divider()

# ===========================================================================
# Certificate
# ===========================================================================
st.markdown("## Your Kodi Legacy Certificate")
st.caption(
    "A real, downloadable document — component breakdown, succession status if "
    "simulated above, and a visible demo-safety mark since this is the one artifact "
    "here most easily mistaken for something with legal effect once downloaded."
)

succession_for_cert = dict(
    scenario=scenario, successor_score=successor_score,
    live_score_at_month=live_score_active, month=months_since,
)
certificate_pdf = build_legacy_certificate(
    person_name, components, total, LEGACY_MAX,
    succession=succession_for_cert, generated_at=datetime.now(),
)
st.download_button(
    "⬇ Download Kodi Legacy Certificate (PDF)", data=certificate_pdf,
    file_name="kodi_legacy_certificate.pdf", mime="application/pdf",
)

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Enterprise builds retention. Asset builds reciprocity. <b>Legacy builds "
    "continuity — the point where the Ngazi Platform's two expressions, compliance "
    "progression and asset credibility, converge into a single record that outlives "
    "the taxpayer.</b> This closes the lifecycle: Seed builds familiarity before any "
    "relationship exists; Legacy makes sure that relationship, once built, doesn't "
    "have to end.",
)

st.divider()

# ===========================================================================
# Journey Recap — the closing screen of the entire six-stage build
# ===========================================================================
st.markdown("## Your journey")
st.caption(
    "Every stage's real outcome from this session, in one place — a continuous "
    "record, not six disconnected transactions. Any stage skipped this session is "
    "marked honestly, not filled in."
)

seed_done = bool(st.session_state.get("seed_journey_completed"))
seed_titles = st.session_state.get("seed_titles", [])
entry_done = bool(st.session_state.get("engazi_registered"))
active_done = bool(st.session_state.get("active_benchmark_completed"))

recap_rows = [
    ("🌱", "Seed", "Completed" if seed_done else "Not completed this session",
     (", ".join(seed_titles) if seed_titles else "Madarasa Ya Kodi missions played") if seed_done else "", seed_done),
    ("🚪", "Entry", "Registered via ENgazi" if entry_done else "Not completed this session",
     "Reserved a place in TRA's records" if entry_done else "", entry_done),
    ("⚖️", "Active", "Compliance benchmark generated" if active_done else "Not completed this session",
     "Real FinScope-based comparison viewed" if active_done else "", active_done),
    ("📈", "Enterprise", enterprise_milestone if came_from_enterprise else "Not started",
     "Established Taxpayer Status" if enterprise_graduated else
     (f"On the ladder: {enterprise_milestone}" if came_from_enterprise else ""), came_from_enterprise),
    ("🏠", "Asset", f"Asset Score: {asset_summary['total_score']} / {asset_summary['max_score']}" if came_from_asset else "Not generated",
     asset_summary["confidence_band"] if came_from_asset else "", came_from_asset),
    ("🕊️", "Legacy", f"Kodi Legacy Score: {total} / {LEGACY_MAX}", "This stage, always available once reached", True),
]

for icon, stage, status, detail, done in recap_rows:
    dot_color = GREEN if done else "#CFCFCF"
    text_color = GREEN_DARK if done else "#888"
    # Built as one single-line string, deliberately -- a blank/empty line
    # inside a raw unsafe_allow_html block (e.g. from an empty `detail`
    # slotted into a multi-line f-string) makes Streamlit's markdown
    # parser drop out of HTML-passthrough mode partway through, leaking
    # literal "</div>" text onto the page. Caught by reading the rendered
    # page during verification, not assumed safe.
    detail_html = f'<div style="font-size:0.82rem; color:#666;">{detail}</div>' if detail else ""
    row_html = (
        f'<div style="display:flex; align-items:flex-start; gap:0.9rem; '
        f'border-left:3px solid {dot_color}; margin-left:0.6rem; padding:0.7rem 0 0.7rem 1.1rem; '
        f'position:relative;">'
        f'<div style="position:absolute; left:-9px; top:1.05rem; width:14px; height:14px; '
        f'border-radius:50%; background:{dot_color}; border:2px solid white; '
        f'box-shadow:0 0 0 2px {dot_color};"></div>'
        f'<div style="font-size:1.3rem; line-height:1.4rem;">{icon}</div>'
        f'<div>'
        f'<div style="font-weight:700; color:{text_color}; font-size:0.78rem; '
        f'text-transform:uppercase; letter-spacing:0.04em;">{stage}</div>'
        f'<div style="font-size:1rem; color:#222;">{status}</div>'
        f'{detail_html}'
        f'</div>'
        f'</div>'
    )
    st.markdown(row_html, unsafe_allow_html=True)

st.write("")
completed_count = sum(1 for *_, done in recap_rows if done)
st.markdown(
    f'<div class="tdj-note-card"><div class="tdj-note-label">This session\'s record</div>'
    f"<p>{completed_count} of 6 stages carried a real, continuous record forward — "
    "the same thesis this whole project is built on: one relationship, not six "
    "resets.</p></div>",
    unsafe_allow_html=True,
)

stage_nav_footer("legacy")
