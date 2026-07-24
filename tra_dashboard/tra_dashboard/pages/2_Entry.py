import base64
import os

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from common import (
    inject_base_style, inject_hero_style, stage_header, callout, evidence_tag,
    stage_nav_footer, GREEN,
    PipelineData, demo_safety_banner, looks_like_nida, looks_like_phone,
)

st.set_page_config(page_title="Entry — Targeting Priority Tool", page_icon="🚪", layout="wide")
inject_base_style()
stage_header("🚪", "Entry", "Join", "Targeting", "2")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_PERSONA_PATH = os.path.join(ASSETS_DIR, "entry_persona_juma.png")
_TEXTURE_PATH = os.path.join(ASSETS_DIR, "network_texture.png")


@st.cache_data(show_spinner=False)
def _b64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


inject_hero_style(_b64_file(_TEXTURE_PATH) if os.path.exists(_TEXTURE_PATH) else "")

pipeline = PipelineData()

# ---------------------------------------------------------------------------
# A3: recognize a handoff from Seed, without requiring one
# ---------------------------------------------------------------------------
came_from_seed = st.session_state.get("seed_handoff_complete", False)
seed_nida = st.session_state.get("seed_handoff_nida", "")

# ---------------------------------------------------------------------------
# About this pilot -- same treatment as Seed and Active
# ---------------------------------------------------------------------------
with st.expander("Why Entry exists"):
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**The problem**")
        st.write(
            "Juma is 19, runs a phone-repair stall in Mwanza, and has used mobile "
            "money since he was 16. He's already participating in the economy — "
            "receiving customer payments, running a small operation — but to TRA "
            "he doesn't exist yet: no TIN, no registration. Getting one feels like "
            "an extra task competing against unfamiliar paperwork and time he "
            "doesn't have."
        )
        st.markdown("**The mechanism**")
        st.write(
            "Entry addresses this from two directions. The **Targeting Priority "
            "Tool** answers *who* TRA should reach first when outreach budget is "
            "limited. **ENgazi Registration** answers what happens *once someone "
            "is reached* — the document's own USSD channel was never built (real "
            "telecom integration, out of scope for this pilot), so this is a "
            "platform-native alternative that gives Juma something fast to do "
            "right now instead of a channel that doesn't exist yet."
        )
    with c2:
        figures = pipeline.intervention_figures("USSD TIN nudge (Entry Stage)")
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

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
hc1, hc2 = st.columns([2, 1])
with hc1:
    st.markdown(
        """
        <div class="tdj-hero"><div class="tdj-hero-inner">
            <div class="tdj-hero-title">Two ways in: get found, or come in yourself</div>
            <p class="tdj-hero-sub">Below: the real model that decides who TRA should
            reach first, and ENgazi Registration — a way to join TRA's records the
            moment someone is ready, no phone channel required.</p>
        </div></div>
        """,
        unsafe_allow_html=True,
    )
with hc2:
    if os.path.exists(_PERSONA_PATH):
        st.image(_PERSONA_PATH, width="stretch")

if came_from_seed:
    st.markdown(
        '<div class="tdj-note-card"><div class="tdj-note-label">Welcome back</div>'
        "<p>You completed Madarasa Ya Kodi and confirmed your age. Let's get you "
        "set up — ENgazi Registration below already has your NIDA number "
        "ready.</p></div>",
        unsafe_allow_html=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 1: Targeting Priority Tool
# ---------------------------------------------------------------------------
st.markdown("## Targeting Priority Tool")
st.caption(
    "A logistic regression trained on 50,000 records calibrated to FinScope "
    "Tanzania 2023 distributions — a prototype segmentation model, not "
    "calibrated against real TRA administrative registration data."
)

tab_individual, tab_scale = st.tabs(["🎯 Score an individual", "📊 Targeting at scale"])

segmentation = pipeline.ml_segmentation()

with tab_individual:
    evidence_tag("model" if segmentation.available else "hypothesis")
    if segmentation.available:
        seg = segmentation.value
        coefs = {f["feature"]: f["coefficient"] for f in seg["feature_importance"]}
        st.write(
            f"Using the **real** trained logistic regression (AUC = {seg['cv_auc_mean']:.3f} "
            f"± {seg['cv_auc_std']:.3f}, {seg['n_training']:,} training records). "
            "Adjust the features to see how the model's own coefficients move the score."
        )
    else:
        st.write(
            "The real model uses six features. Adjust them to see how predicted "
            "registration likelihood shifts — urban residence is the strongest "
            "predictor by a wide margin."
        )

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
        # Unchanged from the prior verified build -- only the chrome around
        # it changed in this pass.
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

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": " / 100"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": GREEN},
            "steps": [
                {"range": [0, 40], "color": "#EFEFEF"},
                {"range": [40, 70], "color": "#D8E7D8"},
                {"range": [70, 100], "color": "#9CC79F"},
            ],
        },
        title={"text": "Predicted registration priority"},
    ))
    gauge.update_layout(height=280, margin=dict(t=40, b=10))
    st.plotly_chart(gauge, width="stretch")
    st.caption(score_caption)

with tab_scale:
    pop_fig = pipeline.targeting_population()
    if not pop_fig.available:
        st.warning(f"Population-level data isn't connected right now ({pop_fig.note}).")
    else:
        pop = pop_fig.value
        probs = np.array(pop["probabilities"])
        urban_arr = np.array(pop["urban"])
        biz_arr = np.array(pop["business_owner"])
        mm_arr = np.array(pop["has_mobile_money"])
        n_sample = pop["n_sample"]

        evidence_tag("model")
        st.caption(
            f"The same trained classifier as the individual score above, applied to a "
            f"real {n_sample:,}-person representative sample of the {pop['n_population']:,}-person "
            "population it was trained on. A modeled comparison from the classifier's real "
            "coefficients, not a measured outcome from an actual campaign."
        )

        pct = st.slider(
            "Share of the eligible population you can reach this quarter",
            1, 100, 10, format="%d%%",
        )
        top_n = max(1, round(pct / 100 * n_sample))
        order = np.argsort(-probs)
        top_idx = order[:top_n]

        mean_top = probs[top_idx].mean()
        mean_all = probs.mean()
        expected_targeted = top_n * mean_top
        expected_random = top_n * mean_all
        multiple = (mean_top / mean_all) if mean_all else 0.0

        m1, m2, m3 = st.columns(3)
        m1.metric(f"Targeted ({top_n:,} people)", f"~{expected_targeted:,.0f} registrations")
        m2.metric(f"Random selection ({top_n:,} people)", f"~{expected_random:,.0f} registrations")
        m3.metric("Targeting multiplier", f"{multiple:.1f}×")

        cmp_fig = go.Figure(go.Bar(
            x=["Random selection", "Targeted (top-scoring)"],
            y=[expected_random, expected_targeted],
            marker_color=["#B9B9B9", GREEN],
            text=[f"~{expected_random:,.0f}", f"~{expected_targeted:,.0f}"],
            textposition="outside",
        ))
        cmp_fig.update_layout(
            height=280, margin=dict(t=20, b=10),
            yaxis_title="Modeled expected registrations", plot_bgcolor="white",
        )
        st.plotly_chart(cmp_fig, width="stretch")

        st.markdown("#### Who gets contacted first")
        w1, w2, w3 = st.columns(3)
        w1.metric("Urban", f"{urban_arr[top_idx].mean()*100:.0f}%",
                   help=f"{urban_arr.mean()*100:.0f}% across the full sample")
        w2.metric("Business owners", f"{biz_arr[top_idx].mean()*100:.0f}%",
                   help=f"{biz_arr.mean()*100:.0f}% across the full sample")
        w3.metric("Mobile money users", f"{mm_arr[top_idx].mean()*100:.0f}%",
                   help=f"{mm_arr.mean()*100:.0f}% across the full sample")

        st.caption(
            "\"Registration likelihood\" here means how closely someone's profile "
            "matches people who already hold a TIN in the model's training "
            "population, used as a targeting signal — not a causal claim that "
            "contacting a given person will cause them to register."
        )

st.divider()

# ---------------------------------------------------------------------------
# Section 2: ENgazi Registration
# ---------------------------------------------------------------------------
st.markdown("## ENgazi Registration")
st.caption(
    "Reserve your place in TRA's records today — without waiting for a "
    "phone-based channel that doesn't exist yet."
)

_engazi_defaults = {
    "engazi_screen": "intro",
    "engazi_registered": False,
    "engazi_business_registered": False,
}
for k, v in _engazi_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

screen = st.session_state.engazi_screen

if screen == "intro":
    st.markdown(
        '<div class="tdj-card">Like Juma, you might already be economically active — '
        "TRA just hasn't seen you yet. ENgazi Registration adds you to TRA's records "
        "and reserves your place in the tax base today. It doesn't replace an "
        "eventual in-person step — it just turns that step into a short visit for "
        "verification and document submission, instead of registration from "
        "scratch.</div>",
        unsafe_allow_html=True,
    )
    if st.button("Get started →", key="engazi_start", type="primary"):
        st.session_state.engazi_screen = "form"
        st.rerun()

elif screen == "form":
    demo_safety_banner()
    regions_fig = pipeline.active_benchmark_regions()
    region_options = regions_fig.value if regions_fig.available else [
        "Dar es Salaam", "Mwanza", "Arusha", "Dodoma", "Mbeya", "Morogoro",
    ]

    f1, f2 = st.columns(2)
    with f1:
        name = st.text_input("Full name", key="engazi_name_field")
        nida = st.text_input(
            "NIDA number", value=seed_nida, key="engazi_nida_field",
            help="20 digits — format checked only, not verified against NIDA.",
        )
        if nida:
            st.caption("✓ Format accepted (not verified)" if looks_like_nida(nida)
                       else "Doesn't look like a 20-digit NIDA number yet.")
    with f2:
        phone = st.text_input(
            "Phone number", key="engazi_phone_field",
            help="e.g. 07XXXXXXXX — format checked only, not verified with a telecom.",
        )
        if phone:
            st.caption("✓ Format accepted (not verified)" if looks_like_phone(phone)
                       else "Doesn't look like a Tanzanian phone number yet.")
        region = st.selectbox("Region", region_options, key="engazi_region_field")

    if st.button("Join TRA's records", key="engazi_submit", type="primary"):
        missing = []
        if not name.strip():
            missing.append("full name")
        if not looks_like_nida(nida):
            missing.append("a 20-digit NIDA number")
        if not looks_like_phone(phone):
            missing.append("a valid-looking phone number")
        if missing:
            st.warning("Still needed: " + ", ".join(missing) + ".")
        else:
            st.session_state.engazi_name = name.strip()
            st.session_state.engazi_nida = nida
            st.session_state.engazi_phone = phone
            st.session_state.engazi_region = region
            st.session_state.engazi_registered = True
            st.session_state.engazi_screen = "confirmation"
            st.rerun()

elif screen == "confirmation":
    name = st.session_state.get("engazi_name", "")
    st.markdown(
        f'<div class="tdj-card"><b>You\'re now in TRA\'s records as a prospective '
        f"taxpayer{', ' + name if name else ''}.</b><br>You are not yet a fully "
        "registered taxpayer, and nothing has been verified — this reserves your "
        "place. The one remaining real-world step is a short TRA office visit for "
        "verification and document submission, not a repeat of registration from "
        "scratch.</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("#### Already running a business?")
    st.write(
        "Add your business registration number, license, or permit — completely "
        "optional, and you can finish here without it."
    )
    demo_safety_banner()
    biz = st.text_input("Business registration number, license, or permit", key="engazi_biz_field")
    if st.button("Add business details", key="engazi_biz_submit"):
        if biz.strip():
            st.session_state.engazi_business_number = biz.strip()
            st.session_state.engazi_business_registered = True
            st.rerun()

    if st.session_state.engazi_business_registered:
        st.markdown(
            '<div class="tdj-note-card"><div class="tdj-note-label">You\'re already '
            'an active taxpayer</div><p>Here\'s your benchmarking tool — the same '
            "shared reference point Mzani wa Kodi gives every officer and taxpayer "
            "at the Active stage.</p></div>",
            unsafe_allow_html=True,
        )
        st.page_link("pages/3_Active.py", label="Go to Mzani wa Kodi →", icon="⚖️")

    st.write("")
    if st.button("↺ Start a new demo registration", key="engazi_reset"):
        for k in list(_engazi_defaults) + [
            "engazi_name", "engazi_nida", "engazi_phone", "engazi_region",
            "engazi_business_number",
        ]:
            st.session_state.pop(k, None)
        st.rerun()

st.divider()
callout(
    "STRATEGIC CONTRIBUTION",
    "Seed introduces future taxpayers to TRA. Entry converts that familiarity into "
    "the first formal interaction with the tax system — the Targeting Priority Tool "
    "decides who to reach, and ENgazi Registration gives them something to do the "
    "moment they're reached, without waiting on a phone channel that was never "
    "built. Someone who registers a business here arrives at Active already known "
    "to TRA, not as a stranger.",
)

stage_nav_footer("entry")
