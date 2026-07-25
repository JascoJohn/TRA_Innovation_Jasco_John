import base64
import os

import plotly.graph_objects as go
import streamlit as st

from common import (
    inject_base_style, stage_header, callout, evidence_tag, stage_nav_footer,
    demo_safety_banner, looks_like_nida,
)

st.set_page_config(page_title="Seed — Madarasa Ya Kodi", page_icon="🌱", layout="wide")
inject_base_style()
stage_header("🌱", "Seed", "Learn", "Experience", "1")

# ---------------------------------------------------------------------------
# Seed-stage palette. Sampled directly from the submission document's own
# Seed-section graphics (not the app-wide NAVY/GOLD chrome from
# tdj_lib/styling.py, which stays untouched above and below this page's
# game). #256E29 is the exact green used in the document's "4.1 Seed Stage"
# section banner; the two tints are lighter steps off that same hue for
# card surfaces. SEED_AMBER is the one color NOT sourced from the document
# -- it's a warm, analogous accent chosen for "TRA helps" moments so they
# read as a distinct beat without introducing a clashing hue.
# ---------------------------------------------------------------------------
SEED_GREEN = "#256E29"
SEED_GREEN_DARK = "#123815"
SEED_TINT = "#D8E7D8"
SEED_TINT_LIGHT = "#E5EFE6"
SEED_AMBER = "#C97A1D"

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_PERSONA_PATH = os.path.join(ASSETS_DIR, "seed_persona_amina.png")
_TEXTURE_PATH = os.path.join(ASSETS_DIR, "network_texture.png")


@st.cache_data(show_spinner=False)
def _b64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


_texture_b64 = _b64_file(_TEXTURE_PATH) if os.path.exists(_TEXTURE_PATH) else ""

st.markdown(
    f"""
    <style>
    .seed-hero {{
        position: relative;
        border-radius: 10px;
        overflow: hidden;
        padding: 2.1rem 2.3rem;
        margin: 0.4rem 0 1.4rem 0;
        background:
            linear-gradient(135deg, {SEED_GREEN} 0%, {SEED_GREEN_DARK} 100%);
        border-bottom: 5px solid {SEED_AMBER};
    }}
    .seed-hero::before {{
        content: "";
        position: absolute; inset: 0;
        background-image: url("data:image/png;base64,{_texture_b64}");
        background-size: cover;
        background-position: center;
        mix-blend-mode: multiply;
        opacity: 0.9;
        pointer-events: none;
    }}
    .seed-hero-inner {{ position: relative; z-index: 1; }}
    .seed-hero-title {{
        color: white; font-family: Georgia, 'Cambria', serif;
        font-size: 2rem; font-weight: 700; margin: 0 0 0.3rem 0; line-height: 1.15;
    }}
    .seed-hero-sub {{
        color: {SEED_TINT}; font-size: 1.02rem; max-width: 46rem; margin: 0;
    }}
    .seed-card {{
        background: {SEED_TINT_LIGHT};
        border: 1px solid {SEED_TINT};
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0;
    }}
    .seed-tra-card {{
        background: #FDF3E7;
        border-left: 5px solid {SEED_AMBER};
        border-radius: 6px;
        padding: 0.9rem 1.1rem;
        margin: 0.8rem 0;
    }}
    .seed-tra-label {{
        color: {SEED_AMBER}; font-weight: 700; font-size: 0.74rem;
        letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.3rem;
    }}
    .seed-badge {{
        display: inline-block; background: {SEED_GREEN}; color: white;
        font-family: Georgia, 'Cambria', serif; font-weight: 700;
        padding: 0.35rem 0.9rem; border-radius: 99px; font-size: 0.95rem;
        margin: 0.2rem 0.3rem 0.2rem 0;
    }}
    .seed-mission-tag {{
        display: inline-block; color: {SEED_GREEN}; font-weight: 700;
        font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase;
        border: 1px solid {SEED_GREEN}; border-radius: 99px;
        padding: 0.15rem 0.7rem; margin-bottom: 0.6rem;
    }}
    .seed-demo-note {{ color: #7A7A7A; font-size: 0.8rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
_defaults = {
    "seed_screen": "intro",
    "seed_village": "",
    "seed_titles": [],
    "seed_m1_done": False,
    "seed_m2_done": False,
    "seed_m3_done": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _village_name() -> str:
    return st.session_state.seed_village.strip() or "Amina's village"


def _reset_game():
    for k, v in _defaults.items():
        st.session_state[k] = v
    for key in ("m1_choice", "m2_choice", "m3_choice"):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# About this pilot (kept from the original page, tucked away so the game
# itself gets top billing on this page)
# ---------------------------------------------------------------------------
with st.expander("Why Madarasa Ya Kodi exists"):
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("**The problem**")
        st.write(
            "Future taxpayers often encounter TRA only when an obligation appears. A "
            "child has no reason to feel ownership over a system introduced only as an "
            "adult obligation — there is no familiarity, no institutional association, "
            "no early relationship."
        )
        st.markdown("**The mechanism**")
        st.write(
            "Not tax education — identity formation. Children get repeated, first-hand "
            "experience of *being someone who helps their community*, so that identity "
            "is already theirs by the time an adult obligation ever appears. The game "
            "below is a simplified, playable slice of that mechanic."
        )
    with c2:
        evidence_tag("hypothesis")
        st.caption(
            "Revenue impact is not scored for this stage — the mechanism is identity "
            "formation, not immediate compliance gain."
        )
        st.metric("Estimated pilot cost", "TZS 260M – 1.06B")

# ---------------------------------------------------------------------------
# Tabs: the game itself, and what TRA would see in aggregate
# ---------------------------------------------------------------------------
play_tab, tra_tab = st.tabs(["🎮 Play the mission", "📊 TRA view: participation data"])

# ============================================================ PLAY TAB =====
with play_tab:
    evidence_tag("hypothesis")
    st.markdown(
        '<span class="seed-demo-note">Illustrative demo — a playable slice of the '
        "concept, not fed by live TRA or FinScope data.</span>",
        unsafe_allow_html=True,
    )

    screen = st.session_state.seed_screen

    # ---- INTRO ----------------------------------------------------------
    if screen == "intro":
        st.markdown(
            f"""
            <div class="seed-hero"><div class="seed-hero-inner">
                <div class="seed-hero-title">Your community needs your help</div>
                <p class="seed-hero-sub">Every term, your village sets money aside for
                the things it needs most. This term, you decide how it's spent —
                and you'll see exactly what happens because of your choice.</p>
            </div></div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([1, 2])
        with col1:
            if os.path.exists(_PERSONA_PATH):
                st.image(_PERSONA_PATH, width="stretch")
        with col2:
            st.write(
                "You're playing as **Amina**, 12, from Dodoma. She's just started "
                "helping decide what her village spends its shared savings on this "
                "term — three real decisions, three real outcomes."
            )
            st.text_input(
                "Name your own village (optional)",
                key="seed_village",
                placeholder="e.g. Amina's village",
            )
            if st.button("Start →", type="primary"):
                st.session_state.seed_screen = "m1"
                st.rerun()

    # ---- MISSION 1: COMPETENCE ------------------------------------------
    elif screen == "m1":
        st.markdown('<div class="seed-mission-tag">Mission 1 of 3</div>', unsafe_allow_html=True)
        st.markdown(f"### {_village_name()}'s shared well is broken, and the school desks are falling apart")
        st.write(
            f"{_village_name()} has **TZS 400,000** saved up this term. Fixing the "
            "well fully costs TZS 300,000. New desks fully cost TZS 100,000. Decide "
            "how to split the money between them."
        )

        well_pct = st.slider(
            "Share of the treasury for the water well",
            0, 100, 50, key="m1_slider",
            help="The rest goes toward school desks.",
        )
        treasury = 400_000
        well_need, desks_need = 300_000, 100_000
        well_funds = treasury * well_pct // 100
        desks_funds = treasury - well_funds

        a, b = st.columns(2)
        a.metric("💧 Water well", f"TZS {well_funds:,}", help=f"Needs TZS {well_need:,} to fully fix")
        b.metric("🏫 School desks", f"TZS {desks_funds:,}", help=f"Needs TZS {desks_need:,} to fully cover")

        if st.button("See what happens", key="m1_confirm"):
            st.session_state.seed_m1_done = True
            st.session_state.m1_well_funds = well_funds
            st.session_state.m1_desks_funds = desks_funds

        if st.session_state.seed_m1_done:
            well_short = max(0, well_need - st.session_state.m1_well_funds)
            desks_short = max(0, desks_need - st.session_state.m1_desks_funds)

            if well_short == 0 and desks_short == 0:
                st.markdown(
                    f'<div class="seed-card">Perfect split — the well gets fixed '
                    f'<b>and</b> the desks get bought, fully, this term. No shortfall '
                    f'at all. {_village_name()} did this on its own.</div>',
                    unsafe_allow_html=True,
                )
            else:
                need_label, short_amt = (
                    ("the water well", well_short) if well_short > desks_short
                    else ("the school desks", desks_short)
                )
                st.markdown(
                    f'<div class="seed-card">{_village_name()} funded most of what '
                    f"it needed this term, but came up TZS {short_amt:,} short on "
                    f"{need_label}.</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"""<div class="seed-tra-card">
                    <div class="seed-tra-label">TRA stepped in</div>
                    <p>TRA matched the remaining TZS {short_amt:,} for {need_label} —
                    finishing what {_village_name()} had already started, not doing it
                    instead of them.</p>
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown('<span class="seed-badge">🏅 Community Helper</span>', unsafe_allow_html=True)
            if st.button("Continue to Mission 2 →", key="m1_next", type="primary"):
                if "Community Helper" not in st.session_state.seed_titles:
                    st.session_state.seed_titles.append("Community Helper")
                st.session_state.seed_screen = "m2"
                st.rerun()

    # ---- MISSION 2: AUTONOMY ---------------------------------------------
    elif screen == "m2":
        st.markdown('<div class="seed-mission-tag">Mission 2 of 3</div>', unsafe_allow_html=True)
        st.markdown(f"### {_village_name()} has grown. Now there's a harder choice.")
        st.write(
            f"This term's treasury is **TZS 900,000**. Three real needs are competing "
            "for it — and this time there's no slider to balance them perfectly. Pick "
            "the one you think matters most."
        )

        option = st.radio(
            "What does the village fund this term?",
            options=["road", "school", "water"],
            format_func=lambda k: {
                "road": "🛣️ Extend the market road — traders reach buyers faster",
                "school": "🏫 Add a classroom — more children get a seat",
                "water": "🚰 Open a new water point — shorter walks for water",
            }[k],
            key="m2_choice",
        )

        outcomes = {
            "road": dict(
                primary="the market-road extension", primary_cost=650_000,
                secondary="a covered market shelter for traders", secondary_need=400_000,
                who="the traders who'll use both",
            ),
            "school": dict(
                primary="the new classroom", primary_cost=900_000,
                secondary=None, secondary_need=0,
                who="the children who needed a seat",
            ),
            "water": dict(
                primary="the new water point", primary_cost=500_000,
                secondary="extending it into a small irrigation channel", secondary_need=550_000,
                who="the households nearest the new tap",
            ),
        }

        if st.button("See what happens", key="m2_confirm"):
            st.session_state.seed_m2_done = True
            st.session_state.m2_option = option

        if st.session_state.seed_m2_done:
            o = outcomes[st.session_state.m2_option]
            treasury2 = 900_000
            leftover = treasury2 - o["primary_cost"]
            st.markdown(
                f'<div class="seed-card">{o["primary"].capitalize()} gets funded in '
                f"full this term — {o['who']} feel it immediately.</div>",
                unsafe_allow_html=True,
            )
            if o["secondary"] is None:
                st.markdown(
                    f'<div class="seed-card">The whole treasury went into one '
                    f"project, done properly, with nothing left over — and nothing "
                    f"short. {_village_name()} closed this one on its own.</div>",
                    unsafe_allow_html=True,
                )
            else:
                short = max(0, o["secondary_need"] - leftover)
                if short == 0:
                    st.markdown(
                        f'<div class="seed-card">There was even enough left over for '
                        f'{o["secondary"]}.</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""<div class="seed-tra-card">
                        <div class="seed-tra-label">TRA stepped in</div>
                        <p>What was left over wasn't quite enough for {o['secondary']}
                        — TRA covered the remaining TZS {short:,}, so that didn't have
                        to wait another term.</p>
                        </div>""",
                        unsafe_allow_html=True,
                    )

            st.caption(
                "A different choice here would have funded a different need, in full "
                "— that's the trade-off: this isn't a puzzle with one right answer."
            )
            st.markdown('<span class="seed-badge">🏅 Village Builder</span>', unsafe_allow_html=True)
            if st.button("Continue to Mission 3 →", key="m2_next", type="primary"):
                if "Village Builder" not in st.session_state.seed_titles:
                    st.session_state.seed_titles.append("Village Builder")
                st.session_state.seed_screen = "m3"
                st.rerun()

    # ---- MISSION 3: RELATEDNESS -------------------------------------------
    elif screen == "m3":
        st.markdown('<div class="seed-mission-tag">Mission 3 of 3</div>', unsafe_allow_html=True)
        st.markdown("### Two people are counting on this term's treasury")
        st.write(
            f"{_village_name()} has **TZS 350,000** left this term. Two people need "
            "help, and there isn't quite enough for both in full. Who does the "
            "village help first?"
        )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                '<div class="seed-card"><b>Baraka, age 8</b><br>His classroom has no '
                'roof — class stops the moment it rains.<br>Full fix: '
                '<b>TZS 220,000</b></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                '<div class="seed-card"><b>Mama Fatuma, mother of three</b><br>The '
                'clinic supply post near her has run out of basic medicine.<br>Full '
                'restock: <b>TZS 190,000</b></div>',
                unsafe_allow_html=True,
            )

        who = st.radio(
            "Who gets funded first, in full?",
            options=["baraka", "fatuma"],
            format_func=lambda k: {
                "baraka": "Fund Baraka's classroom roof first",
                "fatuma": "Fund Mama Fatuma's clinic supplies first",
            }[k],
            key="m3_choice",
        )

        if st.button("See what happens", key="m3_confirm"):
            st.session_state.seed_m3_done = True
            st.session_state.m3_who = who

        if st.session_state.seed_m3_done:
            treasury3 = 350_000
            roof, clinic = 220_000, 190_000
            if st.session_state.m3_who == "baraka":
                first_name, first_cost = "Baraka's roof", roof
                second_name, second_need, second_person = "Mama Fatuma's clinic restock", clinic, "Mama Fatuma"
            else:
                first_name, first_cost = "Mama Fatuma's clinic restock", clinic
                second_name, second_need, second_person = "Baraka's roof", roof, "Baraka"
            leftover = treasury3 - first_cost
            short = max(0, second_need - leftover)

            st.markdown(
                f'<div class="seed-card">{first_name} is fully funded this term. '
                "That's a real, immediate difference for one specific person.</div>",
                unsafe_allow_html=True,
            )
            if short > 0:
                st.markdown(
                    f"""<div class="seed-tra-card">
                    <div class="seed-tra-label">TRA stepped in</div>
                    <p>{_village_name()} still had TZS {leftover:,} left toward
                    {second_name} — TRA covered the remaining TZS {short:,}, so
                    {second_person} didn't have to wait for next term's treasury.</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
            st.caption(
                "Whoever you fund first, the village can't quite reach both alone — "
                "your choice decided who TRA stepped in for, not whether help arrived."
            )
            st.markdown('<span class="seed-badge">🏅 Young Leader</span>', unsafe_allow_html=True)
            if st.button("Finish →", key="m3_next", type="primary"):
                if "Young Leader" not in st.session_state.seed_titles:
                    st.session_state.seed_titles.append("Young Leader")
                st.session_state.seed_screen = "closing"
                st.rerun()

    # ---- CLOSING -----------------------------------------------------------
    elif screen == "closing":
        # Part C (Legacy build): a minimal, additive completion signal for the
        # journey recap -- reaching this screen always means all 3 missions
        # were completed, regardless of whether the optional NIDA step below
        # is used. Distinct from seed_handoff_complete, which is conditional
        # on that NIDA step and means something narrower (ready to continue
        # to Entry with data to carry forward).
        st.session_state.seed_journey_completed = True

        st.markdown(
            f"""
            <div class="seed-hero"><div class="seed-hero-inner">
                <div class="seed-hero-title">You've become someone who helps
                {_village_name()} solve real problems</div>
                <p class="seed-hero-sub">Three terms, three decisions, three people
                and projects better off because of choices you made.</p>
            </div></div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "".join(f'<span class="seed-badge">🏅 {t}</span>' for t in st.session_state.seed_titles),
            unsafe_allow_html=True,
        )
        st.write("")
        st.write(
            "Every time your own contribution came up short, TRA finished what "
            f"{_village_name()} had already started — the well, the market shelter "
            "or irrigation channel, Baraka's roof or Mama Fatuma's clinic. Not "
            "instead of you. Alongside you."
        )
        st.caption(
            "Reserved for a longer arc: two further titles — Community Champion and "
            "Future Nation Builder — exist in the source material but are out of "
            "scope for this 3-mission build."
        )
        if st.button("↺ Play again"):
            _reset_game()
            st.rerun()

        st.divider()
        st.markdown("#### Continue your journey")
        st.write(
            "A real person your age would eventually register with TRA as an "
            "adult. Confirm you're ready to continue, and Entry will already "
            "have your NIDA number waiting — no need to enter it twice. "
            "Completely optional — stopping above is a complete ending too."
        )
        demo_safety_banner()
        handoff_nida = st.text_input(
            "NIDA number (optional)", key="seed_handoff_nida_field",
            help="20 digits — format checked only, not verified against NIDA.",
        )
        if handoff_nida:
            st.caption(
                "✓ Format accepted (not verified)" if looks_like_nida(handoff_nida)
                else "Doesn't look like a 20-digit NIDA number yet."
            )
        if st.button("Confirm I'm ready to continue", key="seed_handoff_submit"):
            if looks_like_nida(handoff_nida):
                st.session_state.seed_handoff_complete = True
                st.session_state.seed_handoff_nida = handoff_nida
            else:
                st.warning(
                    "Enter a 20-digit NIDA number to continue, or just leave this "
                    "blank — stopping here is a complete ending too."
                )
        if st.session_state.get("seed_handoff_complete"):
            st.page_link("pages/2_Entry.py", label="Continue to Entry →", icon="🚪")

# ============================================================ TRA TAB ======
with tra_tab:
    evidence_tag("hypothesis")
    st.markdown(
        '<span class="seed-demo-note">Illustrative demo — mock aggregate figures '
        "across many simulated players, not derived from this single session and not "
        "fed by live TRA or FinScope data.</span>",
        unsafe_allow_html=True,
    )
    st.write(
        "Per the submission's Seed-stage deliverable, TRA receives usage analytics "
        "and participation metrics from Madarasa Ya Kodi — a structured channel for "
        "reaching future taxpayers years before they'd otherwise appear in any TRA "
        "system. This is a mock-up of that view."
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Sessions started (mock)", "14,208")
    m2.metric("Reached Mission 3", "54%")
    m3.metric("Avg. session length", "6m 40s")

    stages = ["Started", "Mission 1\n(Community Helper)", "Mission 2\n(Village Builder)",
              "Mission 3\n(Young Leader)"]
    counts = [14208, 12981, 9932, 7677]
    fig = go.Figure(
        data=[go.Bar(
            x=counts, y=stages, orientation="h",
            marker_color=[SEED_GREEN_DARK, SEED_GREEN, SEED_GREEN, SEED_AMBER],
            text=[f"{c:,}" for c in counts], textposition="outside",
        )]
    )
    fig.update_layout(
        xaxis_title="Simulated players (mock)", height=320,
        margin=dict(t=20, b=20, l=10, r=40), plot_bgcolor="white",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Mock participation funnel — the shape (steady, gentle drop-off across three "
        "short missions) is illustrative of what a real cohort funnel would look "
        "like, not a measured result."
    )

st.divider()
callout(
    "CONNECTS FORWARD TO ENTRY",
    "The mechanism connecting a child's Madarasa Ya Kodi record to their adult "
    "taxpayer profile is Tanzania's National Identification Authority (NIDA) number, "
    "which every citizen already holds. The familiarity built here is retrievable, "
    "not re-established from scratch, when that citizen later reaches Entry.",
)

stage_nav_footer("seed")
