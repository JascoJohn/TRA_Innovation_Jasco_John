"""Backward-compatible shim. The reusable logic that used to live here
has been split into tdj_lib/ (styling.py, stages.py, pipeline_data.py)
so each piece can be reused independently of this Streamlit app -- see
tdj_lib/__init__.py for the breakdown. Existing pages that still do
`from common import ...` keep working unmodified; new code should import
from tdj_lib directly.
"""

from tdj_lib import (
    NAVY, GOLD, SLATE, CREAM, GRAY, WHITE,
    GREEN, GREEN_DARK, TINT, TINT_LIGHT, AMBER,
    EVIDENCE_TIER_HELP, inject_base_style, inject_hero_style, callout, evidence_tag,
    STAGES, stage_header, stage_nav_footer,
    PipelineData, Figure,
    BenchmarkResult, finscope_adapter,
    DEMO_SAFETY_NOTICE, demo_safety_banner, looks_like_nida, looks_like_phone,
    build_asset_verification_report, build_digital_asset_profile,
)

__all__ = [
    "NAVY", "GOLD", "SLATE", "CREAM", "GRAY", "WHITE",
    "GREEN", "GREEN_DARK", "TINT", "TINT_LIGHT", "AMBER",
    "EVIDENCE_TIER_HELP", "inject_base_style", "inject_hero_style", "callout", "evidence_tag",
    "STAGES", "stage_header", "stage_nav_footer",
    "PipelineData", "Figure",
    "BenchmarkResult", "finscope_adapter",
    "DEMO_SAFETY_NOTICE", "demo_safety_banner", "looks_like_nida", "looks_like_phone",
    "build_asset_verification_report", "build_digital_asset_profile",
]
