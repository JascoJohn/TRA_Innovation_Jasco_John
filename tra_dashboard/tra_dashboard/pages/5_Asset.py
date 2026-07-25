import base64
import os
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from common import (
    inject_base_style, inject_hero_style, stage_header, callout, evidence_tag,
    stage_nav_footer, GREEN, GREEN_DARK, AMBER,
    demo_safety_banner,
    build_asset_verification_report, build_digital_asset_profile,
)

st.set_page_config(page_title="Asset — Verified Economic Identity", page_icon="🏠", layout="wide")
inject_base_style()
stage_header("🏠", "Asset", "Reveal", "Reciprocity", "5")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_PERSONA_PATH = os.path.join(ASSETS_DIR, "asset_persona_joseph.png")
_TEXTURE_PATH = os.path.join(ASSETS_DIR, "network_texture.png")


@st.cache_data(show_spinner=False)
def _b64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


inject_hero_style(_b64_file(_TEXTURE_PATH) if os.path.exists(_TEXTURE_PATH) else "")

# ---------------------------------------------------------------------------
# Score construction. BASE_SCORE + illustrative components reproduces the
# document's own Figure 4.21 example exactly (700 + 20 + 25 + 15 + 0 = 760)
# -- 760 is the one total the document states outright ("a score of 760
# would be eligible for..."); BASE_SCORE=700 is this build's own
# reconstruction back-solved from that example, since the underlying table
# wasn't available to read directly. Ngazi Standing is new: a fifth
# component, on the same points idiom, computed (not self-reported) from
# real Enterprise progression -- see NGAZI_STANDING_SCALE below for the
# rebalancing reasoning.
BASE_SCORE = 700
MAX_SCORE = 1000

VEHICLE_MAX, RENTAL_MAX, OWNERSHIP_MAX, PROPERTY_MAX = 20, 25, 15, 0
NGAZI_MAX = 40  # see comment at NGAZI_STANDING_SCALE

# Real 6-milestone ladder benefits, verbatim from pages/4_Enterprise.py's
# LADDER constant -- duplicated here (static reference data, not logic)
# so Asset's benefits panel can show what was actually earned without
# Enterprise needing to export anything beyond the two flags it already
# documents for this purpose.
ENTERPRISE_LADDER = [
    ("TIN Obtained", "Digital taxpayer profile"),
    ("First Return Filed", "Automated reminder service"),
    ("Six Months Compliant", "Downloadable compliance certificate"),
    ("EFD Connected", "Pre-filled renewal forms"),
    ("Annual Filing Completed", "Priority digital support desk"),
    ("Established Taxpayer Status", "Fast-track services, fewer document requests"),
]
_LADDER_NAMES = [name for name, _ in ENTERPRISE_LADDER]

# Ngazi Standing's own points scale: max (40) chosen to outweigh any single
# illustrative component (highest is Rental Declarations at 25) since this
# is the one REAL, non-self-reported signal -- but kept well under the sum
# of all three illustrative components (60), so a taxpayer with no Enterprise
# history isn't structurally locked out of a strong score. Partial credit
# is graduated across the ladder's 6 rungs rather than all-or-nothing at
# "Established Taxpayer Status," since real progression is gradual. With
# this addition the achievable maximum becomes 700+20+25+15+0+40 = 800 --
# deliberately left short of MAX_SCORE (1000), leaving headroom for
# Property Verification's future real contribution once a Full Asset Score
# exists, rather than a scale that's already saturated today.
NGAZI_STANDING_SCALE = {
    "Not yet started": 0,
    "TIN Obtained": 7,
    "First Return Filed": 13,
    "Six Months Compliant": 20,
    "EFD Connected": 27,
    "Annual Filing Completed": 33,
}  # "Established Taxpayer Status" (full graduation) maps to NGAZI_MAX (40) explicitly below

CONFIDENCE_BANDS = [
    (768, "Strong Verification"),
    (734, "Moderate Verification"),
    (0, "Developing Verification"),
]


def _confidence_band(total: int) -> str:
    for threshold, label in CONFIDENCE_BANDS:
        if total >= threshold:
            return label
    return CONFIDENCE_BANDS[-1][1]


# ---------------------------------------------------------------------------
# Part A continuation: recognize Enterprise's forward-compatibility flags
# (ngazi_current_milestone, ngazi_established_status_reached -- documented
# in pages/4_Enterprise.py). Strictly additive: a session with neither key
# present sees none of this and Asset works exactly standalone.
# ---------------------------------------------------------------------------
enterprise_milestone = st.session_state.get("ngazi_current_milestone")
enterprise_graduated = bool(st.session_state.get("ngazi_established_status_reached"))
came_from_enterprise = enterprise_milestone is not None

if enterprise_graduated:
    ngazi_points = NGAZI_MAX
elif came_from_enterprise:
    ngazi_points = NGAZI_STANDING_SCALE.get(enterprise_milestone, 0)
else:
    ngazi_points = 0

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
hc1, hc2 = st.columns([2, 1])
with hc1:
    st.markdown(
        """
        <div class="tdj-hero"><div class="tdj-hero-inner">
            <div class="tdj-hero-title">You're building a Verified Economic Identity</div>
            <p class="tdj-hero-sub">Mali Alama — the Asset Score — is one legible piece of
            it: a record that turns what you already own and already comply with into
            something you can show, not just something TRA can see.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )
with hc2:
    if os.path.exists(_PERSONA_PATH):
        st.image(_PERSONA_PATH, width="stretch")

if enterprise_graduated:
    st.markdown(
        '<div class="tdj-note-card"><div class="tdj-note-label">You graduated from Ngazi</div>'
        "<p>Reaching <b>Established Taxpayer Status</b> in Ngazi triggered automatic "
        "Ngazi Enterprise Graduation — you've come through Seed, Entry, Active, and "
        "Enterprise. That progression now counts as a real, computed component of your "
        "Verified Economic Identity below (not a self-reported one), and every benefit "
        "you already earned carries forward into the panel further down.</p></div>",
        unsafe_allow_html=True,
    )
elif came_from_enterprise:
    st.markdown(
        '<div class="tdj-note-card"><div class="tdj-note-label">Welcome</div>'
        f"<p>We can see your Ngazi progress — currently <b>{enterprise_milestone}</b>. "
        "That's already counted as a real component below. Reach Established Taxpayer "
        "Status in Ngazi for full credit here.</p></div>",
        unsafe_allow_html=True,
    )

with st.expander("Why Mali Alama exists"):
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**The problem**")
        st.write(
            "Joseph owns a rental property and a commercial vehicle, both generating "
            "real income. Declaring them to TRA currently looks one-sided — TRA gains "
            "visibility, he gains nothing tangible back."
        )
        st.markdown("**The mechanism**")
        st.write(
            "Fiscal Exchange Theory (Alm, Jackson & McKee, 1993): compliance rises when "
            "people perceive a genuine two-way exchange. Tanzania's own tax-morale "
            "figures show the willingness already exists (World Values Survey 61.8%, "
            "Afrobarometer 59.8%) — what's missing isn't attitude, it's the exchange "
            "itself."
        )
    with c2:
        evidence_tag("hypothesis")
        st.caption("Reciprocity mechanism — revenue impact secondary, not yet modeled")
        st.metric("Data source", "Vehicle + rental (TRA-owned)")

st.markdown(
    '<span class="tdj-demo-note">Important limitation: the Core Asset Score below runs '
    "entirely on data TRA already holds. The <b>Full</b> Asset Score — land, building, "
    "and property records — depends on future data-sharing agreements with the "
    "Ministry of Lands and local government registries. Named future expansion, not "
    "current scope; nothing here implies those records are available today.</span>",
    unsafe_allow_html=True,
)

st.divider()

# ===========================================================================
# Self-reported inputs
# ===========================================================================
st.markdown("## Build your profile")
st.caption(
    "Three honest, self-reported inputs — not a demo default. Nothing here is saved "
    "beyond this session."
)

demo_safety_banner()
person_name = st.text_input(
    "Your name (for the documents generated below — optional)", key="asset_name_input",
    placeholder="e.g. Joseph M.",
)

ic1, ic2, ic3 = st.columns(3)
with ic1:
    vehicles = st.number_input("Registered vehicles", 0, 10, 1, key="asset_vehicles")
with ic2:
    rental_declared = st.radio("Rental income declared", ["No", "Yes"], index=1, horizontal=True, key="asset_rental")
with ic3:
    ownership_years = st.slider("Years of ownership", 0, 15, 5, key="asset_ownership_years")

vehicle_points = VEHICLE_MAX if vehicles >= 1 else 0
rental_points = RENTAL_MAX if rental_declared == "Yes" else 0
ownership_points = OWNERSHIP_MAX if ownership_years >= 3 else round(OWNERSHIP_MAX * ownership_years / 3)
property_points = 0

total_score = BASE_SCORE + vehicle_points + rental_points + ownership_points + property_points + ngazi_points
max_achievable = BASE_SCORE + VEHICLE_MAX + RENTAL_MAX + OWNERSHIP_MAX + PROPERTY_MAX + NGAZI_MAX
band = _confidence_band(total_score)

components = [
    dict(
        name="Vehicle Registration (Verified)",
        status=f"{vehicles} vehicle(s) registered" if vehicles else "No vehicles registered",
        points=vehicle_points, max_points=VEHICLE_MAX, tier="illustrative",
        note="Self-reported for this demonstration — the real Core Asset Score reads "
             "this directly from TRA's own vehicle registration records.",
    ),
    dict(
        name="Rental Declarations (Consistent)",
        status="Declared" if rental_declared == "Yes" else "Not declared",
        points=rental_points, max_points=RENTAL_MAX, tier="illustrative",
        note="Self-reported for this demonstration.",
    ),
    dict(
        name="Ownership Stability (High)",
        status=f"{ownership_years} years" if ownership_years else "New ownership",
        points=ownership_points, max_points=OWNERSHIP_MAX, tier="illustrative",
        note="Self-reported for this demonstration; full credit at 3+ years, "
             "proportional below that.",
    ),
    dict(
        name="Property Verification (Pending)",
        status="Not in scope — Full Asset Score only",
        points=property_points, max_points=PROPERTY_MAX, tier="illustrative",
        note="Always 0 today. Activates only once land/building/mortgage "
             "data-sharing agreements exist — a named future expansion, not a gap "
             "in this build.",
    ),
    dict(
        name="Ngazi Standing",
        status=(enterprise_milestone if came_from_enterprise else "Not yet built — reach Ngazi first")
               + (" (graduated)" if enterprise_graduated else ""),
        points=ngazi_points, max_points=NGAZI_MAX, tier="real",
        note=(
            "Computed from your actual Enterprise-stage progression this session — "
            "the one component here that isn't self-reported."
            if came_from_enterprise else
            "Reach Established Taxpayer Status in Ngazi (Enterprise stage) to build "
            "this component honestly — showing 0 rather than a fabricated default."
        ),
    ),
]

st.divider()

# ===========================================================================
# Score display -- identity framing first, number second
# ===========================================================================
st.markdown("## Your Verified Economic Identity")

sc1, sc2 = st.columns([1, 2])
with sc1:
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_score,
        number={"suffix": f" / {MAX_SCORE}", "font": {"size": 26}},
        gauge={
            "axis": {"range": [0, MAX_SCORE], "tickvals": [0, 700, 800, 1000]},
            "bar": {"color": GREEN},
            "steps": [
                {"range": [0, 700], "color": "#EFEFEF"},
                {"range": [700, 734], "color": "#F4F4F4"},
                {"range": [734, 768], "color": "#D8E7D8"},
                {"range": [768, 1000], "color": "#9CC79F"},
            ],
        },
    ))
    gauge.update_layout(height=260, margin=dict(t=20, b=10))
    st.plotly_chart(gauge, width="stretch")
with sc2:
    st.markdown(
        f'<div class="tdj-card"><div class="tdj-note-label" style="color:{GREEN};">{band.upper()}</div>'
        f"<p style='font-size:0.95rem;'>Score reflects a neutral baseline plus what you've "
        "verified above — not a judgement, a legible summary of what's on record. "
        f"Achievable maximum this session: {max_achievable} / {MAX_SCORE}.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown("###### Component breakdown")
    for c in components:
        tag_col = GREEN if c["tier"] == "real" else "#8A8A8A"
        tag_txt = "REAL" if c["tier"] == "real" else "ILLUSTRATIVE"
        st.markdown(
            f"<div style='display:flex; justify-content:space-between; padding:0.25rem 0; "
            f"border-bottom:1px solid #eee; font-size:0.88rem;'>"
            f"<span><span style='color:{tag_col}; font-weight:700; font-size:0.68rem; "
            f"margin-right:0.5rem;'>{tag_txt}</span>{c['name']}</span>"
            f"<b>{c['points']} / {c['max_points']}</b></div>",
            unsafe_allow_html=True,
        )

st.divider()

# ===========================================================================
# Benefits panel -- one continuous list, Enterprise-earned + Asset-specific
# ===========================================================================
st.markdown("## What your Verified Economic Identity unlocks")

benefits = []
if enterprise_graduated:
    for name, benefit in ENTERPRISE_LADDER:
        benefits.append((benefit, f"Earned via Ngazi: {name}", True))
elif came_from_enterprise:
    idx = _LADDER_NAMES.index(enterprise_milestone) if enterprise_milestone in _LADDER_NAMES else -1
    for name, benefit in ENTERPRISE_LADDER[: idx + 1]:
        benefits.append((benefit, f"Earned via Ngazi: {name}", True))

benefits += [
    ("Streamlined loan verification", "Illustrative potential value.", False),
    ("Reduced collateral assessment time", "Illustrative potential value.", False),
    ("Preferred borrower profile with participating lenders", "Illustrative potential value.", False),
]

for title, note, is_real in benefits:
    tag_col = GREEN if is_real else AMBER
    tag_txt = "EARNED" if is_real else "ILLUSTRATIVE"
    st.markdown(
        f"<div class='tdj-card' style='padding:0.7rem 1rem; margin:0.4rem 0;'>"
        f"<span style='color:{tag_col}; font-weight:700; font-size:0.68rem;'>{tag_txt}</span> "
        f"<b>{title}</b><br><span style='font-size:0.82rem; color:#666;'>{note}</span></div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<span class="tdj-demo-note">No financial institution or government partnership '
    "currently exists for the illustrative benefits above — realizing them requires "
    "future negotiation. They demonstrate potential value, not a redeemable offer "
    "today.</span>",
    unsafe_allow_html=True,
)

st.divider()

# ===========================================================================
# Document generation -- real downloadable files, in-memory only
# ===========================================================================
st.markdown("## Your documents")
st.caption(
    "Two different artifacts for two different audiences — an internal-style audit "
    "trail, and a shareable summary someone could plausibly hand to a lender."
)

_gen_time = datetime.now()
report_pdf = build_asset_verification_report(person_name, components, total_score, MAX_SCORE, _gen_time)
highlights = [f"{c['name']}: {c['status']}" for c in components if c["points"] > 0]
profile_pdf = build_digital_asset_profile(
    person_name, total_score, MAX_SCORE, band, highlights, benefits, _gen_time,
)

dl1, dl2 = st.columns(2)
with dl1:
    st.markdown("**Asset Verification Report**")
    st.caption("Full component breakdown, verification status, methodology — the audit trail.")
    st.download_button(
        "⬇ Download Verification Report (PDF)", data=report_pdf,
        file_name="asset_verification_report.pdf", mime="application/pdf",
    )
with dl2:
    st.markdown("**Digital Asset Profile**")
    st.caption("Shareable Verified Economic Identity summary — headline score and highlights only.")
    st.download_button(
        "⬇ Download Digital Asset Profile (PDF)", data=profile_pdf,
        file_name="digital_asset_profile.pdf", mime="application/pdf",
    )

st.divider()

# ---------------------------------------------------------------------------
# Forward-compatibility flag, now consumed by pages/6_Legacy.py -- the
# document states Asset Score is a literal, computed input into the Kodi
# Legacy Score (alongside filing consistency and TIN longevity).
# ---------------------------------------------------------------------------
st.session_state.asset_score_summary = {
    "total_score": total_score,
    "max_score": MAX_SCORE,
    "confidence_band": band,
    "ngazi_standing_points": ngazi_points,
    "ngazi_standing_real": came_from_enterprise,
}

# ---------------------------------------------------------------------------
# Part B (Legacy build): a small, additive card once a score exists (which
# is always, on this page) pointing toward continuity/succession planning.
# Placed only after the score and documents render -- touches nothing above.
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="tdj-card" style="font-size:0.92rem;">Ready to plan for the future? '
    "See how your Verified Economic Identity contributes to lifetime "
    "continuity.</div>",
    unsafe_allow_html=True,
)
st.page_link("pages/6_Legacy.py", label="See my Kodi Legacy Score →", icon="🕊️")

st.divider()

callout(
    "STRATEGIC CONTRIBUTION",
    "Asset Score gives verified transparency real value during a taxpayer's active "
    "life — but that value currently has no way to outlast them. This is not a "
    "thematic link but a mechanical one: the Asset Score is a literal, computed input "
    "into the Kodi Legacy Score, alongside filing consistency and TIN longevity.",
)

stage_nav_footer("asset")
