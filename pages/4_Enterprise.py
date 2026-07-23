import streamlit as st
import plotly.graph_objects as go
from common import inject_base_style, stage_header, callout, evidence_tag, stage_nav_footer, NAVY, GOLD, SLATE, CREAM
from tdj_lib import PipelineData

st.set_page_config(page_title="Enterprise — Ngazi Progression Dashboard", page_icon="📈", layout="wide")
inject_base_style()
stage_header("📈", "Enterprise", "Progress", "Status", "4")

st.title("Ngazi Progression Dashboard")
st.caption("A progression framework that makes compliance status visible and rewards "
           "sustained engagement. Ngazi Status refers specifically to this Enterprise-stage "
           "progression tier.")

figures = PipelineData().intervention_figures('NGAZI ("The Ladder") — Formalization as Levelling-Up')

col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("#### The Problem")
    st.write(
        "Compliance is experienced as repeated obligations rather than measurable "
        "progress. Ngazi tracks progression using existing taxpayer records and answers "
        "three questions: **Where am I? What's next? What happens if I complete it?**"
    )
with col2:
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
            "Revenue/ROI: illustrative — no live source yet even when the pipeline "
            "is connected. intervention_economic_results is stale (computed against "
            "the pre-regeneration intervention set), and revenue_estimate_tzs is not "
            "yet set on the current Ngazi entry. Needs a fresh "
            "economic_model_per_intervention.py run."
            if figures.available else
            f"Illustrative — pipeline data not connected ({figures.note})."
        )

st.divider()
st.markdown("### Try the ladder: find your tier")

c1, c2 = st.columns(2)
with c1:
    on_time_pct = st.slider("% of returns filed on time (last 3 years)", 0, 100, 78)
with c2:
    years_registered = st.slider("Years continuously registered", 0, 30, 6)

# Illustrative tier logic
if on_time_pct >= 90 and years_registered >= 5:
    tier, tier_num = "Level 5 — Platinum", 5
elif on_time_pct >= 80 and years_registered >= 3:
    tier, tier_num = "Level 4 — Gold", 4
elif on_time_pct >= 65:
    tier, tier_num = "Level 3 — Silver", 3
elif on_time_pct >= 45:
    tier, tier_num = "Level 2 — Bronze", 2
else:
    tier, tier_num = "Level 1 — Entry", 1

levels = ["Level 1\nEntry", "Level 2\nBronze", "Level 3\nSilver", "Level 4\nGold", "Level 5\nPlatinum"]
colors = [NAVY if i + 1 == tier_num else "#D9D9D9" for i in range(5)]
fig = go.Figure(go.Bar(x=levels, y=[1, 1, 1, 1, 1], marker_color=colors, text=levels, textposition="inside"))
fig.update_layout(showlegend=False, yaxis_visible=False, height=220, margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
st.success(f"This profile lands at **{tier}**.")

benefits = {
    1: "Standard service — the baseline every registered taxpayer receives.",
    2: "Priority queue at TRA service centres for routine filings.",
    3: "Priority dispute-handling queue; reduced document re-verification on repeat filings.",
    4: "Fast-tracked dispute resolution; eligibility for optional credit-linkage partner "
       "referral (not required for the core mechanism).",
    5: "All Gold-tier benefits, plus first access to new digital services as they roll out.",
}
st.info(f"**Benefits at this level:** {benefits[tier_num]}")
st.caption(
    "Operational benefits are the intended design at every tier; the mechanism is "
    "visible progression, not primarily fresh capital access. Independent evidence "
    "that visible progression *itself* drives sustained compliance is plausible but "
    "not yet proven — treat tier-migration figures as first-pass until validated "
    "against the digital twin."
)

st.divider()
tier_sim = PipelineData().tier_migration()
if tier_sim.available:
    st.markdown("### Real data: national tier migration over 10 years")
    v = tier_sim.value
    yearly = v["yearly_tier_distribution"]
    st.caption(
        f"From a standalone {v['n_agents']:,}-agent, {v['n_years']}-year simulation "
        "built specifically for this chart (separate from the main digital-twin "
        "simulation), using the exact tier thresholds shown above. Tracks two things "
        "that simulation doesn't: years registered and a persistent filing-reliability "
        "trait per agent."
    )
    tier_fig = go.Figure()
    tier_series = [
        ("not_registered_pct", "Not registered", "#D9D9D9"),
        ("level_1_entry_pct", "Level 1 Entry", "#9FB8D9"),
        ("level_2_bronze_pct", "Level 2 Bronze", "#CD7F32"),
        ("level_3_silver_pct", "Level 3 Silver", "#A8A8A8"),
        ("level_4_gold_pct", "Level 4 Gold", GOLD),
        ("level_5_platinum_pct", "Level 5 Platinum", NAVY),
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
        yaxis_range=[0, 100],
    )
    st.plotly_chart(tier_fig, use_container_width=True)
    final_year = yearly[-1]
    st.caption(
        f"By year {v['n_years']}: {final_year['not_registered_pct']:.1f}% still not "
        f"registered, {final_year['level_1_entry_pct']:.1f}% Entry tier, "
        f"{final_year['level_2_bronze_pct']:.1f}% Bronze, "
        f"{final_year['level_3_silver_pct']:.1f}% Silver, "
        f"{final_year['level_4_gold_pct']:.1f}% Gold, "
        f"{final_year['level_5_platinum_pct']:.1f}% Platinum — higher tiers take real "
        "years to reach by design (Gold/Platinum both require years-registered "
        "thresholds), so their small share at year 10 is the model working as intended, "
        "not a weak result."
    )
else:
    st.caption(f"National tier-migration chart not available ({tier_sim.note}).")

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Ngazi Status gives taxpayers a tested experience that engaging with TRA is "
    "reciprocal — sustained compliance is recognised and rewarded, not simply assumed "
    "and taxed. That experience is the precondition for the Asset stage's harder ask: "
    "revealing productive assets that today create obligations with no visible benefit.",
)

stage_nav_footer("enterprise")
