import streamlit as st
import plotly.graph_objects as go
from common import (
    STAGES, NAVY, GOLD, SLATE, CREAM, inject_base_style, callout, evidence_tag,
    EVIDENCE_TIER_HELP,
)

st.set_page_config(
    page_title="The Taxpayer Development Journey",
    page_icon="🧭",
    layout="wide",
)
inject_base_style()

st.title("The Taxpayer Development Journey")
st.caption("A Behavioural Lifecycle Architecture for Tanzania's Tax Compliance  ·  "
           "TRA Innovation Challenge 2026")

callout(
    "AT A GLANCE",
    "Six lifecycle stages — Seed, Entry, Active, Enterprise, Asset, Legacy — "
    "anchored by one connective infrastructure that carries a taxpayer's record "
    "forward across all six. Evidence base: FinScope Tanzania 2023 (n = 9,915), "
    "the Integrated Labour Force Survey 2024, TRA's own administrative records "
    "(1997&ndash;2026), and causal estimation (difference-in-differences, "
    "propensity score matching, synthetic control).",
)

st.markdown("### The Journey")
st.write(
    "TRA meets a young mobile money user, a small trader, an informal business "
    "owner, an asset owner, and an heir as though each is a stranger — even when, "
    "over the span of one life, they are the same person. Six real, built "
    "artifacts anchor this journey. Click a stage below to open its tool."
)

# ---- Lifecycle strip --------------------------------------------------------
cols = st.columns(6)
for col, stage in zip(cols, STAGES):
    with col:
        st.page_link(stage["page"], label=f"{stage['icon']}  {stage['label']}", icon=None)
        st.caption(f"*{stage['verb']} → {stage['mechanism']}*")

st.divider()

# ---- Portfolio impact chart --------------------------------------------------
st.markdown("### Portfolio-Level Impact")
st.write(
    "No single stage reaches the compliance outcome the combined journey reaches. "
    "Building only one or two stages in isolation forecloses the rest of that "
    "gain permanently."
)

scenarios = ["Best single module\n(presumptive tax simplification)",
             "Full combined system\n(all six stages)"]
values = [40.4, 58.2]
fig = go.Figure(
    data=[go.Bar(x=scenarios, y=values, marker_color=[SLATE, NAVY],
                 text=[f"{v}%" for v in values], textposition="outside")]
)
fig.update_layout(
    yaxis_title="Modeled compliance probability (%)",
    yaxis_range=[0, 70],
    height=380,
    margin=dict(t=20, b=20),
    plot_bgcolor="white",
)
st.plotly_chart(fig, use_container_width=True)
evidence_tag("model")
st.caption(
    "Modeled compliance probability under the project's tax morale model. The "
    "combined figure (58.2%) sits below the naive sum of each intervention's "
    "solo effect (78.0%), consistent with realistic diminishing returns, not "
    "multiplicative synergy."
)

st.divider()

# ---- Causal evidence strip --------------------------------------------------
st.markdown("### External Validation: Causal Evidence from Tanzania's Own Data")
c1, c2, c3 = st.columns(3)
with c1:
    evidence_tag("causal")
    st.metric("Difference-in-differences", "+4.85 pp",
              help="Mobile money rollout → TIN registration increase")
with c2:
    evidence_tag("causal")
    st.metric("Propensity score matching", "+9.0 pp",
              help="Bias-corrected effect of mobile money ownership on TIN "
                   "registration; naive estimate was +5.94 pp")
with c3:
    evidence_tag("causal")
    st.metric("Synthetic control gap", "−1.44 pp",
              help="Tanzania's TIN registration growth vs. a Ghana/Kenya/Rwanda/"
                   "Uganda counterfactual, by 2022")

st.caption(EVIDENCE_TIER_HELP)

st.divider()
st.markdown(
    f"<p style='color:{SLATE}; font-size:0.85rem;'>Most stage pages (Entry, Active, "
    "Enterprise, Legacy) read live cost/revenue/model figures from this project's own "
    "pipeline (see the README) rather than fixed numbers — each page captions exactly "
    "which of its figures are real and which remain illustrative, and why.</p>",
    unsafe_allow_html=True,
)
