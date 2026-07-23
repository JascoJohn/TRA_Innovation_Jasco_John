import streamlit as st
import plotly.graph_objects as go
from common import inject_base_style, stage_header, callout, evidence_tag, stage_nav_footer, NAVY, GOLD, SLATE
from tdj_lib import PipelineData

st.set_page_config(page_title="Active — Mzani wa Kodi", page_icon="⚖️", layout="wide")
inject_base_style()
stage_header("⚖️", "Active", "Understand", "Calculation", "3")

st.title("Mzani wa Kodi")
st.caption("Evidence-based benchmarking that provides a transparent reference point for "
           "presumptive tax assessments.")

figures = PipelineData().intervention_figures("Presumptive tax simplification")

col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("#### The Problem")
    st.write(
        "Informal businesses often experience presumptive taxation as subjective. "
        "Using FinScope microdata, income distributions are calculated for different "
        "combinations of region, business activity, and economic characteristics, "
        "then mapped against Tanzania's existing presumptive tax framework — replacing "
        "perceived guesswork with a transparent, evidence-based reference."
    )
with col2:
    evidence_tag("model")
    if figures.available:
        v = figures.value
        st.metric("Cost", f"TZS {v['cost_tzs']/1e6:.0f}M")
        st.metric("Modeled revenue", f"TZS {v['revenue_tzs']/1e9:.1f}B")
        st.metric("ROI", f"{v['roi']:.1f}x")
        st.caption("Live from economic_model.json.")
    else:
        st.metric("Cost", "TZS 600M")
        st.metric("Modeled revenue", "TZS 12.8 – 13B")
        st.metric("ROI", "21.3x")
        st.caption(f"Illustrative — pipeline data not connected ({figures.note}).")

st.divider()

pipeline = PipelineData()
_regions_figure = pipeline.available_regions()
region_activity_regions = _regions_figure.value if _regions_figure.available else None

if region_activity_regions:
    st.markdown("### Real data: business-activity prevalence by region")
    st.caption(
        "Weighted from FinScope Tanzania 2023 microdata (Household_weight). This is a "
        "**prevalence** table, not a turnover-band calculator: FinScope has no turnover "
        "or income-amount variable at all — checked exhaustively against the codebook "
        "and raw columns. What it answers is 'what share of this region's business "
        "owners are in this activity,' which is what a real, honest version of this "
        "tool can currently support."
    )
    region = st.selectbox("Region", region_activity_regions,
                           index=region_activity_regions.index("Dar es Salaam")
                           if "Dar es Salaam" in region_activity_regions else 0)
    prevalence = pipeline.region_activity_prevalence(region)
    activities = list(prevalence.value.keys())
    activities_sorted = sorted(activities, key=lambda a: -prevalence.value[a]["pct"])

    fig = go.Figure(go.Bar(
        y=activities_sorted,
        x=[prevalence.value[a]["pct"] for a in activities_sorted],
        orientation="h", marker_color=NAVY,
        text=[f"{prevalence.value[a]['pct']:.1f}%" for a in activities_sorted],
        textposition="outside",
    ))
    fig.update_layout(height=260, margin=dict(t=10, b=10), xaxis_title="% of region's business-activity population")
    st.plotly_chart(fig, use_container_width=True)

    smallest_n = min(prevalence.value[a]["respondent_count"] for a in activities_sorted)
    if smallest_n < 15:
        st.caption(
            f"Small-sample note: the least-represented category in {region} has only "
            f"{smallest_n} survey respondents — treat its percentage as indicative, "
            "not precise."
        )
else:
    st.markdown("### Try the calculator: estimate a presumptive band")
    c1, c2, c3 = st.columns(3)
    with c1:
        region = st.selectbox("Region", ["Dar es Salaam", "Mwanza", "Arusha", "Dodoma", "Mbeya", "Morogoro"])
    with c2:
        activity = st.selectbox("Business activity", ["Retail trade", "Tailoring / crafts", "Food & beverage",
                                                         "Transport", "Personal services"])
    with c3:
        scale = st.select_slider("Estimated monthly turnover (TZS)",
                                  ["<300,000", "300,000–700,000", "700,000–1.5M", "1.5M–3M", ">3M"],
                                  value="700,000–1.5M")

    # Illustrative FinScope-style band mapping — placeholder for the real regional/sector
    # benchmark distribution pending extraction from TRA's own Excel records.
    region_factor = {"Dar es Salaam": 1.25, "Mwanza": 1.05, "Arusha": 1.1, "Dodoma": 0.9,
                      "Mbeya": 0.95, "Morogoro": 1.0}[region]
    scale_band = {"<300,000": (0, 15_000), "300,000–700,000": (15_000, 40_000),
                  "700,000–1.5M": (40_000, 90_000), "1.5M–3M": (90_000, 180_000),
                  ">3M": (180_000, 350_000)}[scale]
    low = round(scale_band[0] * region_factor)
    high = round(scale_band[1] * region_factor)

    st.metric(f"Suggested presumptive band — {activity} in {region}", f"TZS {low:,} – {high:,} / month")
    st.caption(
        f"Illustrative mapping only — pipeline data not connected ({_regions_figure.note}). "
        "The real region x activity prevalence (see finscope_region_activity_loader.py) "
        "still cannot support a turnover-band figure -- FinScope has no turnover "
        "variable -- so this illustrative band remains a placeholder either way."
    )

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Seed creates familiarity with TRA. Entry encourages registration. "
    "<b>Active strengthens trust at the point where many informal businesses first "
    "experience taxation</b>, ensuring entry into the tax system is guided by "
    "transparent, evidence-based assessments rather than perceived guesswork. Each "
    "benchmarked assessment cycle adds to a defensible, multi-year assessment history "
    "for that taxpayer — the record Enterprise is built on next.",
)

stage_nav_footer("active")
