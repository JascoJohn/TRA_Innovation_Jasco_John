"""Demo-safety helpers for every screen in this app that asks for a NIDA
number, phone number, or other identifying detail (Entry's ENgazi
Registration, Seed's optional closing-screen step).

This dashboard is live on a public URL. A convincing-looking government
registration form asking real members of the public for real ID
numbers is a real risk, not a formality -- so every one of these rules
is enforced here, once, rather than re-implemented per page:

  - demo_safety_banner() must be called directly above every such input,
    not just linked from a footer disclaimer.
  - looks_like_nida()/looks_like_phone() are FORMAT checks only -- digit
    count and shape, nothing else. They do not call NIDA, a telecom, or
    any external service, and never will: there is nothing to call.
  - Every caller in this app stores values in st.session_state only.
    Nothing here writes a file, calls an API, or logs an entered value
    anywhere -- grep this file and every caller if that's ever in doubt.
    Session state vanishes when the browser session ends, same as every
    other piece of state in this project.
"""

import streamlit as st

DEMO_SAFETY_NOTICE = "Pilot demonstration — do not enter real personal information."


def demo_safety_banner():
    st.markdown(
        f'<div class="tdj-note-card"><div class="tdj-note-label">⚠ {DEMO_SAFETY_NOTICE}</div>'
        "<p>Anything typed below stays only in this browser tab's session and is "
        "never saved, logged, or sent anywhere. Use a made-up number.</p></div>",
        unsafe_allow_html=True,
    )


def looks_like_nida(value: str) -> bool:
    """Loose FORMAT check only -- digit count in Tanzania's real NIN
    length range (20 digits). This is not real NIDA validation (nothing
    in this project can call NIDA) and callers must never describe a
    True result as "verified" -- "format accepted" or equivalent only."""
    digits = "".join(ch for ch in value if ch.isdigit())
    return len(digits) == 20


def looks_like_phone(value: str) -> bool:
    """Loose FORMAT check only -- digit count matching a Tanzanian
    mobile number with or without a country code (e.g. 07XXXXXXXX,
    255XXXXXXXXX, +255XXXXXXXXX). Not real verification -- see
    looks_like_nida()'s docstring, same rule applies here."""
    digits = "".join(ch for ch in value if ch.isdigit())
    return len(digits) in (10, 12)
