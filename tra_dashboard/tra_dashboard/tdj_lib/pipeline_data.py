"""Bridge into this project's own data pipeline (economic_model.json,
intervention_register.json, finscope_region_activity.json) -- fully
migrated into TRA Innovation 2/pipeline/, no cross-project dependency.

Originally this read across to a sibling project (tanzania_policy_agent
in "TRA Innovation") since that's where the source data and computation
scripts happened to already live. Fully migrated on request: the
computation scripts (economic_model.py, finscope_analysis.py,
intervention_registrar.py, shared_context.py, assumption_ledger.py,
finscope_region_activity_loader.py), their raw source data (FinScope.csv,
the codebook), and a run_all.py orchestrator now live in
../../../pipeline/ relative to this file -- see that directory's
run_all.py to regenerate everything from scratch, standalone.

Every accessor here still returns a Figure with .available=False (never
a guess, never an exception) when a file or field can't be found -- kept
even after the migration because the dashboard is also meant to run
standalone on share.streamlit.io, where pipeline/'s large data files
(FinScope.csv is 40MB) may not be deployed alongside it.

Known gap: Enterprise's and Legacy's *revenue* figures have no live
source -- economic_model_per_intervention.py (which computes real
per-intervention revenue) was never migrated, since it isn't part of
this dashboard's own pipeline and depends on tanzania_policy_agent's
broader evidence base. revenue_estimate_tzs is None on both current
register entries; intervention_figures() returns available=True (cost
is real) with revenue/roi as None and a note explaining the gap.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

DEFAULT_PIPELINE_DIR = os.environ.get(
    "TDJ_PIPELINE_DIR",
    os.path.normpath(os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "pipeline",
    )),
)


@dataclass
class Figure:
    """Every pipeline_data accessor returns one of these. Check
    .available before trusting .value; .note explains why when it's
    False. Never raises for a missing file or field."""
    value: Optional[Any]
    available: bool
    note: str = ""


def _load_json(pipeline_dir: str, filename: str) -> Optional[dict]:
    path = os.path.join(pipeline_dir, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class PipelineData:
    """One instance per pipeline directory. Construct once per page
    load: PipelineData() picks up TDJ_PIPELINE_DIR / the default sibling
    path; pass pipeline_dir explicitly to point at a different checkout
    or an uploaded copy of the two JSON files."""

    def __init__(self, pipeline_dir: str = DEFAULT_PIPELINE_DIR):
        self.pipeline_dir = pipeline_dir
        self._econ = _load_json(pipeline_dir, "economic_model.json")
        self._register = _load_json(pipeline_dir, "intervention_register.json")
        self._region_activity = _load_json(pipeline_dir, "finscope_region_activity.json")
        self._active_benchmark = _load_json(pipeline_dir, "finscope_active_benchmark.json")
        self._targeting_population = _load_json(pipeline_dir, "finscope_targeting_population.json")

    @property
    def connected(self) -> bool:
        """True if at least one real pipeline file was found. Pages can
        use this to show/hide a 'live data connected' indicator."""
        return self._econ is not None or self._register is not None

    def intervention_figures(self, name_or_id: str) -> Figure:
        """Cost/revenue/ROI for one intervention. Checks
        economic_model.json's cost_benefit.interventions by exact name
        first (has real revenue figures for the 6 Python-modeled
        interventions), then falls back to intervention_register.json by
        title or intervention_id (cost only -- revenue_estimate_tzs is a
        disclosed, real gap for LLM-narrative interventions until
        economic_model_per_intervention.py is re-run against them)."""
        if self._econ:
            for i in self._econ.get("cost_benefit", {}).get("interventions", []):
                if i.get("name") == name_or_id:
                    cost = i.get("implementation_cost_tzs")
                    revenue = i.get("annual_revenue_tzs")
                    return Figure(
                        value={
                            "cost_tzs": cost,
                            "revenue_tzs": revenue,
                            "roi": (revenue / cost) if cost else None,
                        },
                        available=True,
                    )

        if self._register:
            for i in self._register.get("interventions", []):
                if name_or_id in (i.get("title"), i.get("intervention_id")):
                    revenue = i.get("revenue_estimate_tzs")
                    # available=True whenever the intervention itself is found --
                    # cost_estimate_tzs is real here even when revenue isn't. A
                    # caller that only checks .available and blindly renders
                    # value['revenue_tzs'] would print "TZS None" -- check that
                    # field specifically before rendering it, using .note (also
                    # non-empty here) to explain the gap instead.
                    return Figure(
                        value={
                            "cost_tzs": i.get("cost_estimate_tzs"),
                            "revenue_tzs": revenue,
                            "roi": i.get("roi"),
                        },
                        available=True,
                        note=(
                            "" if revenue is not None else
                            "cost is real (intervention_register.json); revenue not yet "
                            "computed -- economic_model_per_intervention.py has not been "
                            "re-run against this intervention since the registry was last "
                            "regenerated"
                        ),
                    )

        return Figure(
            value=None, available=False,
            note=(
                f"pipeline directory not found or '{name_or_id}' not present in "
                f"economic_model.json or intervention_register.json (looked in "
                f"{self.pipeline_dir})"
            ),
        )

    def ml_segmentation(self) -> Figure:
        """The real trained logistic-regression segmentation model
        (feature coefficients + cross-validated AUC) backing Entry's
        Targeting Priority Tool, from economic_model.json's
        ml_segmentation key."""
        if not self._econ or not self._econ.get("ml_segmentation"):
            return Figure(
                value=None, available=False,
                note="economic_model.json missing or has no ml_segmentation key",
            )
        return Figure(value=self._econ["ml_segmentation"], available=True)

    def tier_migration(self) -> Figure:
        """Real yearly Ngazi tier distribution (Entry/Bronze/Silver/Gold/
        Platinum, plus not-registered) from economic_model.json's
        tier_migration_simulation key -- a standalone 500k-agent
        simulation built specifically to back Enterprise's tier chart,
        using the exact tier thresholds already shown on that page."""
        if not self._econ or not self._econ.get("tier_migration_simulation"):
            return Figure(
                value=None, available=False,
                note="economic_model.json missing or has no tier_migration_simulation key",
            )
        return Figure(value=self._econ["tier_migration_simulation"], available=True)

    def available_regions(self) -> Figure:
        """Sorted list of regions with real business-activity prevalence
        data (from finscope_region_activity.json), for populating a
        region selector without the caller reaching into private state."""
        if not self._region_activity:
            return Figure(
                value=None, available=False,
                note="finscope_region_activity.json not found in pipeline directory",
            )
        regions = sorted({r["region"] for r in self._region_activity["rows"]})
        return Figure(value=regions, available=True)

    def region_activity_prevalence(self, region: str) -> Figure:
        """Real, weighted FinScope 2023 business-activity prevalence for
        one region -- e.g. {"Traders - non-agricultural": 50.6, ...} as
        percentages of that region's business-activity population.

        This is NOT a turnover/income-amount distribution: FinScope 2023
        has no such variable (checked exhaustively -- see
        finscope_region_activity_loader.py's docstring in the pipeline
        repo). It answers "what share of this region's business owners
        are in this activity" -- a targeting/prevalence question, not
        "what should this business's presumptive tax band be." Callers
        must not relabel this as a turnover estimate."""
        if not self._region_activity:
            return Figure(
                value=None, available=False,
                note="finscope_region_activity.json not found in pipeline directory",
            )
        rows = [r for r in self._region_activity["rows"] if r["region"] == region]
        if not rows:
            return Figure(
                value=None, available=False,
                note=f"region '{region}' not present in finscope_region_activity.json",
            )
        return Figure(
            value={
                r["activity"]: {
                    "pct": r["pct_of_region_business_activity"],
                    "respondent_count": r["respondent_count"],
                }
                for r in rows
            },
            available=True,
        )

    def active_benchmark_regions(self) -> Figure:
        """Sorted list of regions present in finscope_active_benchmark.json,
        for populating Active's region input without the caller reaching
        into private state."""
        if not self._active_benchmark:
            return Figure(
                value=None, available=False,
                note="finscope_active_benchmark.json not found in pipeline directory",
            )
        regions = sorted({r["region"] for r in self._active_benchmark["rows"]})
        return Figure(value=regions, available=True)

    def active_benchmark_activities(self) -> Figure:
        """The fixed list of business-activity categories the benchmark
        cells are built on (finscope_active_benchmark.json's own
        strand_categories/rows -- same four IncomeMain categories as
        finscope_region_activity.json)."""
        if not self._active_benchmark:
            return Figure(
                value=None, available=False,
                note="finscope_active_benchmark.json not found in pipeline directory",
            )
        activities = sorted({r["activity"] for r in self._active_benchmark["rows"]})
        return Figure(value=activities, available=True)

    def active_benchmark_cell(self, region: str, activity: str) -> Figure:
        """Raw region x activity benchmark cell (respondent_count,
        weighted_population, strand_distribution_pct, registered_pct) from
        finscope_active_benchmark.json -- see
        pipeline/finscope_active_benchmark_loader.py for exactly how these
        are computed. This is the only accessor
        tdj_lib/benchmark_adapters.py's finscope_adapter() reads; every
        FinScope-specific field name (fasx, D6_4a, IncomeMain, reg_name)
        lives in the loader script that produced this JSON, not here and
        not in the adapter."""
        if not self._active_benchmark:
            return Figure(
                value=None, available=False,
                note="finscope_active_benchmark.json not found in pipeline directory",
            )
        for r in self._active_benchmark["rows"]:
            if r["region"] == region and r["activity"] == activity:
                return Figure(value=r, available=True)
        return Figure(
            value=None, available=False,
            note=f"no benchmark cell for {activity!r} in {region!r}",
        )

    def targeting_population(self) -> Figure:
        """The Entry-stage Targeting Priority Tool's scored population --
        a real, index-aligned 5,000-person sample (probabilities +
        urban/business_owner/has_mobile_money/stage) from the exact same
        50,000-person model and population already backing
        economic_model.json's ml_segmentation aggregates -- see
        pipeline/finscope_targeting_population_loader.py for exactly how
        it's reproduced and verified against that committed model."""
        if not self._targeting_population:
            return Figure(
                value=None, available=False,
                note="finscope_targeting_population.json not found in pipeline directory",
            )
        return Figure(value=self._targeting_population, available=True)
