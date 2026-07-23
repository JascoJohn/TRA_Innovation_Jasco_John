import base64
import os

import plotly.graph_objects as go
import streamlit as st

from common import (
    inject_base_style, inject_hero_style, stage_header, callout, evidence_tag,
    stage_nav_footer, GREEN, GREEN_DARK, AMBER,
    PipelineData, finscope_adapter,
)

st.set_page_config(page_title="Active — Mzani wa Kodi", page_icon="⚖️", layout="wide")
inject_base_style()
stage_header("⚖️", "Active", "Understand", "Calculation", "3")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_PERSONA_PATH = os.path.join(ASSETS_DIR, "active_persona_neema.png")
_TEXTURE_PATH = os.path.join(ASSETS_DIR, "network_texture.png")


@st.cache_data(show_spinner=False)
def _b64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


inject_hero_style(_b64_file(_TEXTURE_PATH) if os.path.exists(_TEXTURE_PATH) else "")

pipeline = PipelineData()

# ---------------------------------------------------------------------------
# About this pilot -- same treatment as Seed's "Why this exists" expander
# ---------------------------------------------------------------------------
with st.expander("Why Mzani wa Kodi exists"):
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**The problem**")
        st.write(
            "Neema runs a small tailoring business in Morogoro. Her business "
            "generates regular income, but she's never registered for a TIN. "
            "When a business like hers is assessed, its turnover has to be "
            "estimated — and because she keeps no formal records, that estimate "
            "can look like it depends entirely on the individual officer's "
            "judgement rather than any shared standard. She accepts that tax is "
            "part of doing business; what erodes trust is not knowing how the "
            "number was arrived at."
        )
        st.markdown("**The mechanism**")
        st.write(
            "Perceived procedural fairness drives voluntary compliance — people "
            "accept an obligation more readily when they believe it was reached "
            "transparently and consistently. Mzani wa Kodi doesn't remove officer "
            "discretion or change the tax rules. It gives the officer and the "
            "taxpayer the same evidence-based reference point, so the "
            "conversation shifts from *how much should this person pay* to "
            "*how does this compare to similar businesses.* A trusted assessment "
            "here is also what a taxpayer keeps building a record against — the "
            "same record Enterprise's Ngazi Status is built on next."
        )
    with c2:
        figures = pipeline.intervention_figures("Presumptive tax simplification")
        evidence_tag("model")
        if figures.available and figures.value.get("revenue_tzs"):
            v = figures.value
            st.metric("Cost", f"TZS {v['cost_tzs']/1e6:.0f}M")
            st.metric("Modeled revenue", f"TZS {v['revenue_tzs']/1e9:.1f}B")
            st.metric("ROI", f"{v['roi']:.1f}x")
            st.caption("Live from economic_model.json.")
        else:
            st.metric("Cost", "TZS 600M")
            st.metric("Modeled revenue", "TZS 12.8 – 13B")
            st.metric("ROI", "21.3x")
            st.caption("Illustrative — pipeline cost/revenue figures not connected.")

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
hc1, hc2 = st.columns([2, 1])
with hc1:
    st.markdown(
        """
        <div class="tdj-hero"><div class="tdj-hero-inner">
            <div class="tdj-hero-title">A shared reference point, not a verdict</div>
            <p class="tdj-hero-sub">Mzani wa Kodi doesn't tell anyone what they owe.
            It shows where a business sits next to real, comparable businesses —
            so an assessment can be discussed, not just handed down.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )
with hc2:
    if os.path.exists(_PERSONA_PATH):
        st.image(_PERSONA_PATH, width="stretch")

st.markdown(
    '<span class="tdj-demo-note">This tool cannot and does not estimate a specific '
    "income or tax-liability figure — FinScope Tanzania 2023 has no income or "
    "turnover variable at all. Every figure below is either a real survey "
    "comparison or a clearly labeled illustrative reference, never a single "
    "confident number.</span>",
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Framing toggle -- same computation, different audience copy
# ---------------------------------------------------------------------------
viewer = st.radio(
    "Viewing as",
    options=["taxpayer", "officer"],
    format_func=lambda k: {
        "taxpayer": "👤 I'm the taxpayer — how does my business compare?",
        "officer": "🧑‍💼 I'm the officer — reference benchmark for this assessment",
    }[k],
    horizontal=True,
    label_visibility="collapsed",
)

# ---------------------------------------------------------------------------
# Inputs -- real FinScope categories only
# ---------------------------------------------------------------------------
regions_fig = pipeline.active_benchmark_regions()
activities_fig = pipeline.active_benchmark_activities()

if not (regions_fig.available and activities_fig.available):
    st.warning(
        "Benchmark data isn't connected right now "
        f"({regions_fig.note or activities_fig.note}). This page needs "
        "pipeline/finscope_active_benchmark.json to be present."
    )
else:
    ic1, ic2 = st.columns(2)
    with ic1:
        region = st.selectbox(
            "Region", regions_fig.value,
            index=regions_fig.value.index("Morogoro") if "Morogoro" in regions_fig.value else 0,
        )
    with ic2:
        activity = st.selectbox(
            "Business activity", activities_fig.value,
            index=activities_fig.value.index("Service providers")
            if "Service providers" in activities_fig.value else 0,
            help="Drawn from FinScope's own business-activity categories — the same "
                 "four activity types used throughout this project's real "
                 "region-level data.",
        )

    result = finscope_adapter(region, activity, pipeline=pipeline)

    st.write("")

    # ---- Insufficient data: a correct, visible output, not a hidden failure --
    if not result.available:
        st.markdown(
            f"""<div class="tdj-insufficient-card">
            <div class="tdj-insufficient-label">Insufficient data for this combination</div>
            <p>{result.note}</p>
            </div>""",
            unsafe_allow_html=True,
        )
        st.caption(
            "This is the honest outcome for a thin cell — not a bug. The officer "
            "should rely on other evidence (records, comparable local knowledge) "
            "for this specific region/sector pairing rather than a guessed figure."
        )

    else:
        # ---- The real comparison ------------------------------------------
        headline = (
            f"Businesses like yours in {region}" if viewer == "taxpayer"
            else f"Comparable businesses: {activity.lower()} in {region}"
        )
        st.markdown(f"#### {headline}")
        evidence_tag(result.evidence_tier)
        st.caption(result.source_label)

        m1, m2, m3 = st.columns(3)
        m1.metric("Survey respondents in this cell", result.sample_size)
        m2.metric("Represents (weighted)", f"{result.weighted_population:,.0f} people")
        m3.metric(
            "Currently registered / formal",
            f"{result.formality_rate_pct:.1f}%" if result.formality_rate_pct is not None else "n/a",
        )

        strand = result.strand_distribution
        order = sorted(strand, key=lambda k: -strand[k])
        fig = go.Figure(go.Bar(
            y=order, x=[strand[k] for k in order], orientation="h",
            marker_color=[GREEN_DARK, GREEN, "#5FA867", "#9CC79F"][:len(order)],
            text=[f"{strand[k]:.1f}%" for k in order], textposition="outside",
        ))
        fig.update_layout(
            height=220, margin=dict(t=10, b=10, l=10, r=40),
            xaxis_title="% of businesses like this (financial access strand)",
            plot_bgcolor="white",
        )
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "FinScope's own financial-access-strand classification (Banked / Other "
            "formal non-bank / Informal only / Excluded) — the closest real, "
            "respondent-level signal this survey has for economic engagement, in "
            "the absence of any income or turnover variable."
        )

        st.divider()

        # ---- The illustrative bridge to a presumptive category ------------
        st.markdown("#### Reference presumptive category")
        evidence_tag(result.presumptive_evidence_tier)

        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(result.composite_score * 100),
            number={"suffix": "", "font": {"size": 28}},
            gauge={
                "axis": {"range": [0, 100], "tickvals": [0, 34, 67, 100]},
                "bar": {"color": AMBER},
                "steps": [
                    {"range": [0, 34], "color": "#EFEFEF"},
                    {"range": [34, 67], "color": "#D8E7D8"},
                    {"range": [67, 100], "color": "#9CC79F"},
                ],
            },
            domain={"x": [0, 1], "y": [0, 1]},
        ))
        gauge.update_layout(height=220, margin=dict(t=20, b=10, l=30, r=30))
        gc1, gc2 = st.columns([1, 2])
        with gc1:
            st.plotly_chart(gauge, width="stretch")
        with gc2:
            st.markdown(
                f'<div class="tdj-note-card">'
                f'<div class="tdj-note-label">{result.presumptive_category}</div>'
                "<p>An illustrative reference point, not a computed liability — see "
                "how this is estimated below.</p></div>",
                unsafe_allow_html=True,
            )
            st.caption(
                "0% below TZS 4,000,000 · graduated rates TZS 4,000,000–11,000,000 "
                "· 3.5% for TZS 11,000,000–100,000,000."
            )

        with st.expander("How is this estimated?"):
            st.write(
                f"This combines two real, FinScope-derived figures for this exact "
                f"region/sector cell: the share in a formal or banked financial "
                f"tier ({strand.get('Banked', 0) + strand.get('Other formal non-bank', 0):.1f}%, "
                f"weighted 60%) and the business-registration rate "
                f"({result.formality_rate_pct:.1f}%, weighted 40%), giving a composite "
                f"score of {result.composite_score:.2f} on a 0–1 scale. That score is "
                "then mapped onto Tanzania's three presumptive-tax bands as an "
                "**assumption that higher financial/formality engagement roughly "
                "tracks higher turnover** — a reasonable starting hypothesis, not a "
                "measurement. FinScope has no income or turnover variable, so no "
                "step in this calculation ever touches an actual shilling figure."
            )

        st.markdown(
            f'<div class="tdj-note-card">'
            f'<div class="tdj-note-label">What this is — and isn\'t</div>'
            f"<p>{result.taxpayer_note if viewer == 'taxpayer' else result.officer_note} "
            "It is not a calculated income figure, a legal assessment, or a "
            "replacement for the officer's judgement — it's a shared starting "
            "point for a conversation about a fair number.</p></div>",
            unsafe_allow_html=True,
        )
        st.caption(result.note)

st.divider()

# ---------------------------------------------------------------------------
# The fuller picture -- the original real prevalence chart, kept as-is
# ---------------------------------------------------------------------------
with st.expander("See the full region × activity picture"):
    prevalence_regions_fig = pipeline.available_regions()
    if prevalence_regions_fig.available:
        st.caption(
            "Weighted from FinScope Tanzania 2023 microdata. "
            "This is a **prevalence** table — what share of a region's business "
            "owners are in each activity — not a turnover or income table."
        )
        p_region = st.selectbox(
            "Region", prevalence_regions_fig.value,
            index=prevalence_regions_fig.value.index("Dar es Salaam")
            if "Dar es Salaam" in prevalence_regions_fig.value else 0,
            key="prevalence_region",
        )
        prevalence = pipeline.region_activity_prevalence(p_region)
        activities_sorted = sorted(prevalence.value, key=lambda a: -prevalence.value[a]["pct"])
        fig2 = go.Figure(go.Bar(
            y=activities_sorted,
            x=[prevalence.value[a]["pct"] for a in activities_sorted],
            orientation="h", marker_color=GREEN,
            text=[f"{prevalence.value[a]['pct']:.1f}%" for a in activities_sorted],
            textposition="outside",
        ))
        fig2.update_layout(height=240, margin=dict(t=10, b=10), xaxis_title="% of region's business-activity population")
        st.plotly_chart(fig2, width="stretch")
        smallest_n = min(prevalence.value[a]["respondent_count"] for a in activities_sorted)
        if smallest_n < 15:
            st.caption(
                f"Small-sample note: the least-represented category in {p_region} has "
                f"only {smallest_n} survey respondents — treat its percentage as "
                "indicative, not precise."
            )
    else:
        st.caption(f"Not connected: {prevalence_regions_fig.note}")

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Seed creates familiarity with TRA. Entry encourages registration. "
    "<b>Active strengthens trust at the point where many informal businesses first "
    "experience taxation</b>, ensuring entry into the tax system is guided by "
    "transparent, evidence-based reference points rather than perceived guesswork. "
    "Each benchmarked conversation adds to a defensible, multi-year assessment "
    "history for that taxpayer — the record Enterprise is built on next.",
)

stage_nav_footer("active")
