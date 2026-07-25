"""tdj_lib -- the Taxpayer Development Journey dashboard's reusable
core, split by concern so each piece can be reused independently of the
Streamlit multipage app it was built for:

  styling.py       Palette, CSS injection, evidence-tier tags.
                    No data or stage dependency.
  stages.py         Stage registry + cross-page navigation.
                    No data dependency.
  pipeline_data.py  Optional live bridge into tanzania_policy_agent's
                    real pipeline output. Degrades to an explicit,
                    honest data-gap Figure when unavailable -- never
                    raises, never guesses.
  benchmark_adapters.py
                    Source-agnostic region+sector benchmarking for the
                    Active stage. finscope_adapter is the only adapter
                    today; a future TRA-collections or BRELA adapter
                    plugs in beside it without changing the page.
  demo_identity.py  Shared demo-safety rules for every screen that asks
                    for a NIDA/phone number (Entry's ENgazi Registration,
                    Seed's optional closing step) -- visible warning
                    banner, format-only validation, no persistence
                    beyond st.session_state.
  documents.py      PDF rendering for this project's three downloadable
                    artifacts (Asset's Verification Report and Digital
                    Asset Profile, Legacy's Kodi Legacy Certificate).
                    Pure layout -- score computation stays in each
                    calling page, this module only draws whatever
                    component list it's given. BytesIO only, no disk
                    writes.

Import from the submodules directly (`from tdj_lib.styling import ...`)
or from here for the common subset used on every page.
"""

from .styling import (
    NAVY, GOLD, SLATE, CREAM, GRAY, WHITE,
    GREEN, GREEN_DARK, TINT, TINT_LIGHT, AMBER,
    EVIDENCE_TIER_HELP, inject_base_style, inject_hero_style, callout, evidence_tag,
)
from .stages import STAGES, stage_header, stage_nav_footer
from .pipeline_data import PipelineData, Figure
from .benchmark_adapters import BenchmarkResult, finscope_adapter
from .demo_identity import DEMO_SAFETY_NOTICE, demo_safety_banner, looks_like_nida, looks_like_phone
from .documents import (
    build_asset_verification_report, build_digital_asset_profile, build_legacy_certificate,
)

__all__ = [
    "NAVY", "GOLD", "SLATE", "CREAM", "GRAY", "WHITE",
    "GREEN", "GREEN_DARK", "TINT", "TINT_LIGHT", "AMBER",
    "EVIDENCE_TIER_HELP", "inject_base_style", "inject_hero_style", "callout", "evidence_tag",
    "STAGES", "stage_header", "stage_nav_footer",
    "PipelineData", "Figure",
    "BenchmarkResult", "finscope_adapter",
    "DEMO_SAFETY_NOTICE", "demo_safety_banner", "looks_like_nida", "looks_like_phone",
    "build_asset_verification_report", "build_digital_asset_profile", "build_legacy_certificate",
]
