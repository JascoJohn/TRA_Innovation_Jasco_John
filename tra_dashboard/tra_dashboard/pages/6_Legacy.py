import streamlit as st
import plotly.graph_objects as go
from common import inject_base_style, stage_header, callout, evidence_tag, stage_nav_footer, NAVY, GOLD, SLATE
from tdj_lib import PipelineData

st.set_page_config(page_title="Legacy — Kodi Legacy Score", page_icon="🕊️", layout="wide")
inject_base_style()
stage_header("🕊️", "Legacy", "Preserve", "Inheritance", "6")

st.title("Kodi Legacy Score")
st.caption("A lifetime compliance index that preserves a taxpayer's verified compliance "
           "history and enables its structured transfer to an approved successor.")

figures = PipelineData().intervention_figures('URITHI SALAMA ("Secure Inheritance") — Compliance as Retirement Collateral')

col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("#### The Problem")
    st.write(
        "When a taxpayer retires or passes away, the institutional relationship they "
        "built does not automatically continue. A successor may inherit the business "
        "assets, but not the trust, history, and compliance record accumulated over "
        "decades. **The objective is not to transfer legal tax obligations — it is to "
        "preserve verified compliance history.**"
    )
with col2:
    evidence_tag("firstpass")
    st.caption("First-pass, low confidence")
    if figures.available and figures.value["cost_tzs"] is not None:
        st.metric("Cost", f"TZS {figures.value['cost_tzs']/1e6:.0f}M")
        st.caption("Live from intervention_register.json.")
    else:
        st.metric("Cost", "TZS 700M")
        st.caption(f"Illustrative — pipeline data not connected ({figures.note}).")

    if figures.available and figures.value["revenue_tzs"] is not None:
        st.metric("Modeled revenue", f"TZS {figures.value['revenue_tzs']/1e9:.1f}B")
        st.metric("ROI", f"{figures.value['roi']:.1f}x")
    else:
        st.metric("Modeled revenue", "TZS 2.5B")
        st.metric("ROI", "~3.6x")
        st.caption(
            "Revenue/ROI: illustrative — revenue_estimate_tzs is not yet set on the "
            "current Urithi Salama entry; needs a fresh "
            "economic_model_per_intervention.py run."
            if figures.available else
            f"Illustrative — pipeline data not connected ({figures.note})."
        )

st.divider()
st.markdown("### Try the calculator: score components")
st.caption(
    "Component weights below are set so the five contributions sum to a true 100 "
    "maximum — a correction from the current draft submission, where the same five "
    "components (+45, +20, +15, +10, +10) sum to 100 but are labeled a 92/100 example. "
    "That's worth fixing in the document."
)

c1, c2 = st.columns(2)
with c1:
    on_time_years = st.slider("Years filed on time (of last 15)", 0, 15, 14)
    tin_age = st.slider("Years of continuous registration (TIN age)", 0, 30, 27)
    ngazi_level = st.slider("Ngazi Status level achieved", 1, 5, 5)
with c2:
    asset_score = st.slider("Asset Score", 0, 1000, 760)
    compliance_flags = st.slider("Outstanding compliance flags", 0, 5, 0)

filing_pts = round(45 * (on_time_years / 15))
tin_pts = round(20 * min(tin_age / 27, 1))
ngazi_pts = round(15 * (ngazi_level / 5))
asset_pts = round(10 * min(asset_score / 760, 1))
compliance_pts = max(0, 10 - compliance_flags * 4)

total = filing_pts + tin_pts + ngazi_pts + asset_pts + compliance_pts

fig = go.Figure(go.Bar(
    y=["Filing Consistency", "TIN Longevity", "Ngazi Status", "Asset Score", "Compliance History"],
    x=[filing_pts, tin_pts, ngazi_pts, asset_pts, compliance_pts],
    orientation="h",
    marker_color=NAVY,
    text=[filing_pts, tin_pts, ngazi_pts, asset_pts, compliance_pts],
    textposition="outside",
))
fig.update_layout(xaxis_range=[0, 48], height=280, margin=dict(t=10, b=10),
                   xaxis_title="Points contributed")
st.plotly_chart(fig, use_container_width=True)
st.metric("Overall Kodi Legacy Score", f"{total} / 100")

st.divider()
st.markdown("### Try the mechanic: succession anti-gaming safeguard")
st.write(
    "On approved succession, the successor receives the predecessor's score as a "
    "**visible historical reference**. But the score governing live eligibility for "
    "succession benefits blends over a **three-year transition window** — shifting "
    "monthly from the inherited score toward the successor's own filing behaviour. "
    "This closes the most direct abuse route TRA would face: a business acquired "
    "solely to inherit a high score without sustaining the behaviour that earned it."
)

c1, c2 = st.columns(2)
with c1:
    months_since = st.slider("Months since succession", 0, 36, 12)
with c2:
    successor_score = st.slider("Successor's own filing score so far", 0, 100, 55,
                                 help="What the successor's own record would score on "
                                      "its own, if they had no inheritance at all.")

blend_weight_own = min(months_since / 36, 1.0)
live_score = round(total * (1 - blend_weight_own) + successor_score * blend_weight_own)

fig2 = go.Figure()
months_range = list(range(0, 37, 3))
live_curve = [round(total * (1 - min(m/36,1)) + successor_score * min(m/36,1)) for m in months_range]
fig2.add_trace(go.Scatter(x=months_range, y=live_curve, mode="lines+markers",
                           line=dict(color=GOLD, width=3), name="Live eligibility score"))
fig2.add_hline(y=total, line_dash="dot", line_color=SLATE,
               annotation_text="Inherited reference (historical only)")
fig2.add_vline(x=months_since, line_dash="dash", line_color=NAVY)
fig2.update_layout(height=320, margin=dict(t=20, b=10),
                    xaxis_title="Months since succession", yaxis_title="Score",
                    yaxis_range=[0, 100])
st.plotly_chart(fig2, use_container_width=True)

st.metric(f"Live eligibility score at month {months_since}", f"{live_score} / 100",
          delta=f"{live_score - total} vs. inherited reference")
st.caption(
    "At month 0 the live score equals the full inherited score. By month 36 it is "
    "entirely the successor's own record. A successor who does not sustain compliance "
    "sees the live score decline accordingly."
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

stage_nav_footer("legacy")
