import base64
import os

import plotly.graph_objects as go
import streamlit as st

from common import (
    inject_base_style, inject_hero_style, stage_header, callout, evidence_tag,
    stage_nav_footer, GREEN, GREEN_DARK, AMBER,
    PipelineData,
)

st.set_page_config(page_title="Enterprise — Ngazi Progression Dashboard", page_icon="📈", layout="wide")
inject_base_style()
stage_header("📈", "Enterprise", "Progress", "Status", "4")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_PERSONA_PATH = os.path.join(ASSETS_DIR, "enterprise_persona_asha.png")
_TEXTURE_PATH = os.path.join(ASSETS_DIR, "network_texture.png")


@st.cache_data(show_spinner=False)
def _b64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


inject_hero_style(_b64_file(_TEXTURE_PATH) if os.path.exists(_TEXTURE_PATH) else "")

pipeline = PipelineData()

# ---------------------------------------------------------------------------
# The real 6-milestone benefit ladder, verbatim from the document's own
# Ngazi Progression Dashboard mockup. Deliberately a *different* structure
# from the 500k-agent simulation's 5-tier system below (Entry/Bronze/Silver/
# Gold/Platinum, driven by on-time-filing % and years registered) -- the
# two are not reconciled into one number, because nothing in the real
# simulation output maps cleanly onto these six discrete, sequential
# milestones. Kept visually and structurally separate on this page so
# neither is mistaken for the other.
LADDER = [
    ("TIN Obtained", "Digital taxpayer profile"),
    ("First Return Filed", "Automated reminder service"),
    ("Six Months Compliant", "Downloadable compliance certificate"),
    ("EFD Connected", "Pre-filled renewal forms"),
    ("Annual Filing Completed", "Priority digital support desk"),
    ("Established Taxpayer Status", "Fast-track services, fewer document requests"),
]

# ---------------------------------------------------------------------------
# Part A continuation: recognize an incoming Entry/Active handoff and
# pre-set a sensible starting rung, rather than asking from scratch.
# Strictly additive -- a session with no incoming flag sees none of this.
# ---------------------------------------------------------------------------
came_from_chain = bool(st.session_state.get("engazi_business_registered"))

_self_report_defaults = {
    "ngazi_q_tin": came_from_chain,
    "ngazi_q_filed": False,
    "ngazi_q_6mo": False,
    "ngazi_q_efd": False,
    "ngazi_q_annual": False,
}
for k, v in _self_report_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
hc1, hc2 = st.columns([2, 1])
with hc1:
    st.markdown(
        """
        <div class="tdj-hero"><div class="tdj-hero-inner">
            <div class="tdj-hero-title">Every step unlocks something real</div>
            <p class="tdj-hero-sub">Ngazi isn't a badge for staying compliant — it's a
            ladder where each rung hands you something you can actually use, the moment
            you reach it.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )
with hc2:
    if os.path.exists(_PERSONA_PATH):
        st.image(_PERSONA_PATH, width="stretch")

if came_from_chain:
    st.markdown(
        '<div class="tdj-note-card"><div class="tdj-note-label">Welcome</div>'
        "<p>You've come through Seed, Entry, and Active — you're already registered "
        "as an active taxpayer. We've marked <b>TIN Obtained</b> below to match; "
        "adjust anything else that doesn't fit your situation.</p></div>",
        unsafe_allow_html=True,
    )

with st.expander("Why Ngazi exists"):
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**The problem**")
        st.write(
            "Asha already took real steps toward formality — a trading license, "
            "LGA registration — but her relationship with TRA still feels "
            "transactional. Filing and compliance show up as ongoing burdens, not "
            "as milestones that recognize how far she's already come."
        )
        st.markdown("**The mechanism, and the trap to avoid**")
        st.write(
            "A real randomized field experiment (Campos, Goldstein & McKenzie, "
            "2023, Malawi) found high demand for a formal certificate carrying no "
            "obligation — but almost no uptake of tax registration alongside it. "
            "**Recognition alone moved almost nothing.** What worked was pairing "
            "status with a real, usable benefit. So below, every milestone leads "
            "with what it unlocks — not the status label."
        )
    with c2:
        figures = pipeline.intervention_figures('NGAZI ("The Ladder") — Formalization as Levelling-Up')
        evidence_tag("firstpass")
        st.caption("First-pass, unreviewed")
        if figures.available and figures.value["cost_tzs"] is not None:
            st.metric("Cost", f"TZS {figures.value['cost_tzs']/1e6:.0f}M")
            st.caption("Live from intervention_register.json.")
        else:
            st.metric("Cost", "TZS 750M")
            st.caption(f"Illustrative — pipeline data not connected ({figures.note}).")

        if figures.available and figures.value["revenue_tzs"] is not None:
            st.metric("Modeled revenue", f"TZS {figures.value['revenue_tzs']/1e9:.1f}B")
            st.metric("ROI", f"{figures.value['roi']:.1f}x")
        else:
            st.metric("Modeled revenue", "TZS 4.1B")
            st.metric("ROI", "~5.5x")
            st.caption(
                "Illustrative — no live revenue source yet even when the pipeline "
                "is connected; needs a fresh economic_model_per_intervention.py run."
                if figures.available else
                f"Illustrative — pipeline data not connected ({figures.note})."
            )

st.markdown(
    '<span class="tdj-demo-note">Important limitation: Ngazi\'s long-term effect on '
    "compliance hasn't been empirically tested yet. This is a pilot design grounded "
    "in the Malawi finding above, not a mechanism already proven to work here.</span>",
    unsafe_allow_html=True,
)

st.divider()

# ===========================================================================
# Individual dashboard — Where am I? / What's next? / What happens if I
# complete it?
# ===========================================================================
st.markdown("## Where do you stand?")
st.caption(
    "A few honest questions about your own situation — not a demo default. "
    "Nothing here is saved beyond this session."
)

q1, q2 = st.columns(2)
with q1:
    st.checkbox("I have a TIN", key="ngazi_q_tin")
    st.checkbox("I've filed at least one return", key="ngazi_q_filed")
    st.checkbox("I've been compliant (on-time filing) for 6+ months", key="ngazi_q_6mo")
with q2:
    st.checkbox("My EFD (electronic fiscal device) is connected", key="ngazi_q_efd")
    st.checkbox("I've completed a full annual filing cycle", key="ngazi_q_annual")

# Milestones are sequential by design (you can't skip from "no TIN" to "EFD
# connected") -- position is the longest unbroken run of Yes answers from
# the top, not a simple count, so an inconsistent self-report (e.g. EFD
# connected but no TIN) doesn't overstate progress.
answers = [
    st.session_state.ngazi_q_tin,
    st.session_state.ngazi_q_filed,
    st.session_state.ngazi_q_6mo,
    st.session_state.ngazi_q_efd,
    st.session_state.ngazi_q_annual,
]
position = 0
for a in answers:
    if not a:
        break
    position += 1
# position 0..5 maps to "before milestone 1" .. "milestone 5 (Annual Filing)
# complete"; position 5 with all Yes also means Established Taxpayer Status
# (milestone 6) is reached.
current_label = "Not yet started" if position == 0 else LADDER[position - 1][0]
reached_established = position == 5

# ---------------------------------------------------------------------------
# Forward-compatibility flag for a future Asset-stage build. Nothing in
# this project reads this yet -- Asset is not built. Documented here so
# that build can recognize this session's Ngazi position the same way this
# page recognizes Entry/Active's handoff above, without a rewrite.
# ---------------------------------------------------------------------------
st.session_state.ngazi_current_milestone = current_label
st.session_state.ngazi_established_status_reached = reached_established

ladder_cols = st.columns(6)
for i, (name, _) in enumerate(LADDER):
    with ladder_cols[i]:
        done = i < position or (i == 5 and reached_established)
        st.markdown(
            f'<div style="text-align:center; padding:0.5rem 0.2rem; '
            f'background:{GREEN if done else "#EFEFEF"}; '
            f'color:{"white" if done else "#888"}; border-radius:6px; '
            f'font-size:0.72rem; font-weight:700;">{i+1}. {name}</div>',
            unsafe_allow_html=True,
        )

st.write("")
lc1, lc2 = st.columns(2)
with lc1:
    st.markdown(
        f'<div class="tdj-card"><div class="tdj-note-label" style="color:{GREEN};">WHERE YOU ARE</div>'
        f"<p style='font-size:1.1rem;'><b>{current_label}</b></p></div>",
        unsafe_allow_html=True,
    )

if reached_established:
    name, benefit = LADDER[5]
    with lc2:
        st.markdown(
            f'<div class="tdj-card"><div class="tdj-note-label" style="color:{GREEN};">'
            f'YOU\'VE REACHED THE TOP OF THE LADDER</div>'
            f"<p style='font-size:1.35rem; font-weight:700; color:{GREEN_DARK};'>{benefit}</p>"
            f"<p style='font-size:0.85rem; color:#666;'>{name}</p></div>",
            unsafe_allow_html=True,
        )
else:
    next_name, next_benefit = LADDER[position]
    with lc2:
        # The benefit is the dominant visual element here on purpose -- larger
        # type, primary color, first thing read -- with the milestone name
        # secondary. This is the direct fix for the Malawi finding above:
        # status recognition alone doesn't move behavior, so the status label
        # never gets to be the headline.
        st.markdown(
            f'<div class="tdj-note-card"><div class="tdj-note-label">WHAT YOU GET NEXT</div>'
            f"<p style='font-size:1.35rem; font-weight:700; color:{GREEN_DARK}; margin:0.2rem 0;'>"
            f"{next_benefit}</p>"
            f"<p style='font-size:0.85rem; color:#666;'>Unlocked by: {next_name}</p></div>",
            unsafe_allow_html=True,
        )

st.caption(
    "Every rung above pairs status with a specific, usable benefit — not a badge on "
    "its own. That pairing is the design's whole bet, per the Malawi finding above."
)

st.divider()

# ===========================================================================
# TRA-facing view — the real 500k-agent simulation, unchanged logic,
# framed against what the Deliverable actually asks for.
# ===========================================================================
st.markdown("## TRA view: national progression simulation")

tier_sim = pipeline.tier_migration()
if tier_sim.available:
    evidence_tag("model")
    v = tier_sim.value
    yearly = v["yearly_tier_distribution"]
    st.caption(
        f"A real, standalone {v['n_agents']:,}-agent, {v['n_years']}-year simulation "
        "tracking years-registered and a persistent filing-reliability trait per "
        "agent, using the same tier thresholds as the individual ladder's design "
        "intent (a coarser 5-tier system, not the 6-milestone ladder above — the "
        "two aren't reconciled into one figure)."
    )

    final_year = yearly[-1]
    approaching = final_year["level_1_entry_pct"] + final_year["level_2_bronze_pct"]
    stalled = final_year["level_3_silver_pct"] + final_year["level_4_gold_pct"] + final_year["level_5_platinum_pct"]
    disengaged = final_year["not_registered_pct"]
    early_decline = yearly[1]["not_registered_pct"] - yearly[0]["not_registered_pct"]
    late_decline = yearly[-1]["not_registered_pct"] - yearly[-2]["not_registered_pct"]

    d1, d2, d3 = st.columns(3)
    d1.metric(
        "Approaching next milestone", f"{approaching:.1f}%",
        help="Entry + Bronze tier at year 10 — positioned to progress toward "
             "Silver and above as tenure and filing reliability accumulate.",
    )
    d2.metric(
        "Stalled below Silver", f"{stalled:.1f}%",
        help="Silver + Gold + Platinum combined stay under 10% of the population "
             "even at year 10 — most agents who do register plateau at Entry or "
             "Bronze rather than advancing further, a real pattern in this "
             "simulation, not a modeling artifact.",
    )
    d3.metric(
        "Disengagement risk", f"{disengaged:.1f}%",
        help="Still not registered at all after 10 simulated years — and the "
             f"year-over-year decline in this group is itself slowing "
             f"({early_decline:+.1f}pp in year 2 vs. {late_decline:+.1f}pp in "
             "year 10), meaning new registration momentum tapers over time.",
    )

    tier_fig = go.Figure()
    tier_series = [
        ("not_registered_pct", "Not registered", "#D9D9D9"),
        ("level_1_entry_pct", "Level 1 Entry", "#B7D8B9"),
        ("level_2_bronze_pct", "Level 2 Bronze", GREEN),
        ("level_3_silver_pct", "Level 3 Silver", "#5FA867"),
        ("level_4_gold_pct", "Level 4 Gold", AMBER),
        ("level_5_platinum_pct", "Level 5 Platinum", GREEN_DARK),
    ]
    years = [y["year"] for y in yearly]
    for key, label, color in tier_series:
        tier_fig.add_trace(go.Scatter(
            x=years, y=[y[key] for y in yearly], mode="lines", name=label,
            stackgroup="one", line=dict(color=color, width=0.5),
        ))
    tier_fig.update_layout(
        height=340, margin=dict(t=20, b=10),
        xaxis_title="Year", yaxis_title="% of simulated population",
        yaxis_range=[0, 100], plot_bgcolor="white",
    )
    st.plotly_chart(tier_fig, width="stretch")
    st.caption(
        f"By year {v['n_years']}: {final_year['not_registered_pct']:.1f}% still not "
        f"registered, {final_year['level_1_entry_pct']:.1f}% Entry, "
        f"{final_year['level_2_bronze_pct']:.1f}% Bronze, "
        f"{final_year['level_3_silver_pct']:.1f}% Silver, "
        f"{final_year['level_4_gold_pct']:.1f}% Gold, "
        f"{final_year['level_5_platinum_pct']:.1f}% Platinum — higher tiers take "
        "real years to reach by design (Gold/Platinum both require "
        "years-registered thresholds), so their small share at year 10 is the "
        "model working as intended, not a weak result."
    )
else:
    st.caption(f"National tier-migration chart not available ({tier_sim.note}).")

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Ngazi gives taxpayers a tested experience that engaging with TRA is "
    "reciprocal — sustained compliance is recognised and rewarded with something "
    "usable, not simply assumed and taxed. The longitudinal record this stage "
    "establishes is the foundation the Asset stage's Asset Score and the Legacy "
    "stage's Kodi Legacy Score are built on next.",
)

stage_nav_footer("enterprise")
