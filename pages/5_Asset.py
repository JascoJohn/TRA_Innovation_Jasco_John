import streamlit as st
import plotly.graph_objects as go
from common import inject_base_style, stage_header, callout, evidence_tag, stage_nav_footer, NAVY, GOLD

st.set_page_config(page_title="Asset — Asset Score Dashboard", page_icon="🏠", layout="wide")
inject_base_style()
stage_header("🏠", "Asset", "Reveal", "Reciprocity", "5")

st.title("Asset Score Dashboard")
st.caption("Converts verified ownership behaviour into a credibility signal — the Core "
           "Asset Score runs entirely on data TRA already holds.")

col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("#### The Problem")
    st.write(
        "Asset disclosure creates obligations but limited visible benefit for citizens. "
        "Tanzania's own tax-morale figures (WVS 61.8%, Afrobarometer 59.8%) show this "
        "population is, in principle, willing to participate in a genuine exchange. "
        "What's missing isn't willingness — it's that the exchange, as currently "
        "structured, only runs one way."
    )
with col2:
    evidence_tag("hypothesis")
    st.caption("Reciprocity mechanism — revenue impact secondary, not yet modeled")
    st.metric("Data source", "Vehicle + rental (TRA-owned)")

st.divider()
st.markdown("### Try the score: Core Asset Score")
st.caption("Core Asset Score uses only data already available to TRA. No external "
           "dependency.")

c1, c2, c3 = st.columns(3)
with c1:
    vehicles = st.number_input("Registered vehicles", 0, 10, 2)
with c2:
    rental_declared = st.radio("Rental income declared", ["No", "Yes"], index=1, horizontal=True)
with c3:
    verification_age = st.slider("Years since last verification", 0, 10, 1)

score = 0
score += min(vehicles, 4) * 15
score += 35 if rental_declared == "Yes" else 0
score += max(0, 15 - verification_age * 3)
score = min(100, score)

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=score,
    number={"suffix": " / 100"},
    gauge={"axis": {"range": [0, 100]}, "bar": {"color": GOLD},
           "steps": [{"range": [0, 40], "color": "#EDEDED"},
                     {"range": [40, 75], "color": "#F7F1E5"},
                     {"range": [75, 100], "color": "#FBEBD5"}]},
    title={"text": "Core Asset Score"},
))
fig.update_layout(height=280, margin=dict(t=40, b=10))
st.plotly_chart(fig, use_container_width=True)

st.markdown("**Citizen view would show:**")
b1, b2, b3 = st.columns(3)
b1.write("✓ Verify registered assets")
b2.write("✓ Track score improvements")
b3.write("✓ Download an Asset Verification Report")

st.divider()
st.markdown("#### An Important Limitation")
st.write(
    "The Core Asset Score can be built on data TRA already has. The **Full** Asset "
    "Score — incorporating land, building, and property records — depends on future "
    "data-sharing agreements with the Ministry of Lands and local government registries. "
    "This is a named future expansion, not current scope, and the core mechanism does "
    "not depend on it."
)

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Asset Score gives verified transparency real value during a taxpayer's active "
    "life — but that value currently has no way to outlast them. This is not a "
    "thematic link but a mechanical one: the Asset Score is a literal, computed input "
    "into the Kodi Legacy Score, alongside filing consistency and TIN longevity.",
)

stage_nav_footer("asset")
