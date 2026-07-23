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

Import from the submodules directly (`from tdj_lib.styling import ...`)
or from here for the common subset used on every page.
"""

from .styling import (
    NAVY, GOLD, SLATE, CREAM, GRAY, WHITE,
    EVIDENCE_TIER_HELP, inject_base_style, callout, evidence_tag,
)
from .stages import STAGES, stage_header, stage_nav_footer
from .pipeline_data import PipelineData, Figure

__all__ = [
    "NAVY", "GOLD", "SLATE", "CREAM", "GRAY", "WHITE",
    "EVIDENCE_TIER_HELP", "inject_base_style", "callout", "evidence_tag",
    "STAGES", "stage_header", "stage_nav_footer",
    "PipelineData", "Figure",
]
