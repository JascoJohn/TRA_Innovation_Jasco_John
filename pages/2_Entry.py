import streamlit as st
import plotly.graph_objects as go
from common import inject_base_style, stage_header, callout, evidence_tag, stage_nav_footer, NAVY, GOLD, SLATE
from tdj_lib import PipelineData

st.set_page_config(page_title="Entry — Targeting Priority Tool", page_icon="🚪", layout="wide")
inject_base_style()
stage_header("🚪", "Entry", "Join", "Targeting", "2")

st.title("Targeting Priority Tool")
st.caption("A logistic regression trained on 50,000 real records, ranking the Entry-stage "
           "population by predicted registration likelihood.")

pipeline = PipelineData()
figures = pipeline.intervention_figures("USSD TIN nudge (Entry Stage)")
segmentation = pipeline.ml_segmentation()

col1, col2 = st.columns([3, 2])
with col1:
    st.markdown("#### The Problem")
    st.write(
        "Millions of young Tanzanians are already participating in the economy — "
        "receiving customer payments, running small operations — but to TRA they don't "
        "exist yet: no TIN, no registration. Obtaining a Taxpayer Identification Number "
        "feels like an additional administrative task competing against completing "
        "unfamiliar paperwork and setting aside working time."
    )
    st.write(
        "**If TRA can afford only 500,000 USSD messages this quarter, the tool identifies "
        "the 500,000 people most likely to register** — not a random 500,000 — and shows "
        "the modeled registration gain versus sending the same volume at random."
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
        st.metric("Cost", "TZS 420M")
        st.metric("Modeled revenue", "TZS 8.7 – 9B")
        st.metric("ROI", "20.7x")
        st.caption(f"Illustrative — pipeline data not connected ({figures.note}).")

st.divider()
st.markdown("### Try the model: score a citizen segment")

if segmentation.available:
    seg = segmentation.value
    coefs = {f["feature"]: f["coefficient"] for f in seg["feature_importance"]}
    st.write(
        f"Using the **real** trained logistic regression (AUC = {seg['cv_auc_mean']:.3f} "
        f"± {seg['cv_auc_std']:.3f}, {seg['n_training']:,} training records) from "
        "economic_model.json. Adjust the features to see how the model's own "
        "coefficients move the score."
    )
else:
    st.write("The real model uses six features. Adjust them to see how predicted "
             "registration likelihood shifts — urban residence is the strongest "
             "predictor by a wide margin.")

c1, c2 = st.columns(2)
with c1:
    urban = st.radio("Residence", ["Rural", "Urban"], index=1, horizontal=True)
    business = st.radio("Owns a business", ["No", "Yes"], index=1, horizontal=True)
    mobile_money = st.radio("Active mobile money use", ["No", "Yes"], index=1, horizontal=True)
with c2:
    income = st.select_slider("Income level", ["Low", "Lower-middle", "Middle", "Upper-middle", "High"], value="Middle")
    life_stage = st.select_slider("Life stage", ["Student", "Young adult", "Established adult", "Older adult"], value="Young adult")
    age = st.slider("Age", 15, 70, 26)

if segmentation.available:
    # Real coefficients from ml_segmentation, applied to this page's own
    # 0-1 feature encodings. No trained intercept is stored in
    # economic_model.json, so this is a logit-style weighted index scaled
    # to 0-100 for the gauge -- not a calibrated predicted probability.
    # That distinction is real and stated below, not glossed over.
    income_map = {"Low": 0.0, "Lower-middle": 0.25, "Middle": 0.5, "Upper-middle": 0.75, "High": 1.0}
    life_stage_map = {"Student": 0.0, "Young adult": 0.33, "Established adult": 0.67, "Older adult": 1.0}
    age_norm = (age - 15) / (70 - 15)

    features = {
        "urban_residence": 1.0 if urban == "Urban" else 0.0,
        "business_owner": 1.0 if business == "Yes" else 0.0,
        "has_mobile_money": 1.0 if mobile_money == "Yes" else 0.0,
        "income_normalised": income_map[income],
        "lifecycle_stage": life_stage_map[life_stage],
        "age_normalised": age_norm,
    }
    max_possible = sum(abs(coefs.get(f, 0)) for f in features)
    raw = sum(coefs.get(f, 0) * v for f, v in features.items())
    score = round(max(0.0, min(1.0, raw / max_possible if max_possible else 0)) * 100)
    score_caption = (
        "Real coefficients, illustrative scaling: economic_model.json does not store "
        "the model's trained intercept, so this is a 0-100 index built from the real "
        "feature weights above — not a calibrated predicted probability."
    )
else:
    # Illustrative weights only -- directional, matches the document's stated
    # feature ranking (urban residence is the strongest predictor by a wide margin).
    # Does NOT reproduce the trained model's actual coefficients.
    score = 0.0
    score += 34 if urban == "Urban" else 6
    score += 18 if business == "Yes" else 4
    score += 16 if mobile_money == "Yes" else 2
    score += {"Low": 4, "Lower-middle": 8, "Middle": 12, "Upper-middle": 15, "High": 10}[income]
    score += {"Student": 5, "Young adult": 14, "Established adult": 10, "Older adult": 6}[life_stage]
    score += max(0, 12 - abs(age - 32) * 0.35)
    score = min(100, round(score))
    score_caption = (
        "Illustrative scoring only — directionally matches the trained model's feature "
        "ranking but does not reproduce its actual coefficients. Pipeline data not "
        f"connected ({segmentation.note})."
    )

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=score,
    number={"suffix": " / 100"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": NAVY},
        "steps": [
            {"range": [0, 40], "color": "#EDEDED"},
            {"range": [40, 70], "color": "#F7F1E5"},
            {"range": [70, 100], "color": "#FBEBD5"},
        ],
    },
    title={"text": "Predicted registration priority"},
))
fig.update_layout(height=280, margin=dict(t=40, b=10))
st.plotly_chart(fig, use_container_width=True)
st.caption(score_caption)

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Seed introduces future taxpayers to TRA. Entry converts that familiarity into "
    "the first formal interaction with the tax system — the onboarding layer of the "
    "taxpayer development journey.",
)

stage_nav_footer("entry")
