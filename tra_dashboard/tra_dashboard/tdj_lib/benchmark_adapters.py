"""Data-source adapters for Mzani wa Kodi (Active stage) benchmarking.

Every adapter implements the same contract -- region + sector in,
a BenchmarkResult out -- so the page never touches a raw data source
directly and never hardcodes which source it's looking at. FinScope is
the only data source available today (finscope_adapter, below); TRA's
own tax-collection records and BRELA business-registration data are
realistic future additions, and each would be a *stronger* evidence
tier than a survey proxy (an actual observed assessment for a
comparable business, vs. a survey-implied one). Adding a second
adapter later means writing one more function with this same
signature and letting the page's evidence-tier-driven copy pick up the
new source_label/evidence_tier automatically -- not touching
pages/3_Active.py's rendering logic at all.

No UI for choosing between sources exists yet, on purpose -- there's
only one. This module is the seam, not a plugin system.
"""

from dataclasses import dataclass
from typing import Optional

from .pipeline_data import Figure, PipelineData

# Below this many respondents in a cell, no estimate is shown at all --
# a visible "insufficient data" result, not a number built on too few
# people to mean anything.
MIN_N_FOR_ANY_ESTIMATE = 8
# Below this, an estimate is shown but flagged small-sample.
MIN_N_FOR_CONFIDENT_ESTIMATE = 20

# The illustrative bridge from a real strand/registration profile to a
# presumptive-tax category. This is NOT a turnover estimate -- see
# BenchmarkResult.presumptive_evidence_tier, always "hypothesis" here.
PRESUMPTIVE_BANDS = [
    ("Likely below TZS 4,000,000 (no presumptive tax due)", 0.0, 0.34),
    ("Likely TZS 4,000,000 – 11,000,000 (graduated presumptive rates apply)", 0.34, 0.67),
    ("Likely TZS 11,000,000 – 100,000,000 (3.5% presumptive rate applies)", 0.67, 1.01),
]


@dataclass
class BenchmarkResult:
    """What every adapter returns. Nothing in here is specific to any
    one data source -- the page renders this shape, never a source's
    raw fields directly."""

    available: bool
    region: str
    sector: str
    sample_size: int = 0
    weighted_population: Optional[float] = None

    # The real, source-derived comparison.
    strand_distribution: Optional[dict] = None      # e.g. {"Banked": 12.4, ...}
    formality_rate_pct: Optional[float] = None       # % registered/formal in this cell
    evidence_tier: str = "hypothesis"                # tier for the fields above
    source_label: str = ""                            # e.g. "FinScope Tanzania 2023 ..."

    # The illustrative bridge to a presumptive-tax category.
    composite_score: Optional[float] = None            # 0..1
    presumptive_category: Optional[str] = None
    presumptive_evidence_tier: str = "hypothesis"      # always a bridge, never "model"

    # Framing copy -- source-aware, so the page never writes its own
    # claim about what kind of evidence this is.
    taxpayer_note: str = ""
    officer_note: str = ""
    note: str = ""                                     # explains gaps / insufficient data


def _presumptive_category(score: float) -> str:
    for label, lo, hi in PRESUMPTIVE_BANDS:
        if lo <= score < hi:
            return label
    return PRESUMPTIVE_BANDS[-1][0]


def finscope_adapter(
    region: str, sector: str, pipeline: Optional[PipelineData] = None,
) -> BenchmarkResult:
    """The only adapter that exists today. Reads
    finscope_active_benchmark.json through PipelineData.active_benchmark_cell()
    -- see pipeline/finscope_active_benchmark_loader.py for exactly how
    that file's strand_distribution_pct and registered_pct are computed
    from raw FinScope microdata. Every FinScope-specific column name
    (fasx, D6_4a, IncomeMain, reg_name) lives in that loader script;
    this function only ever touches the already-neutral JSON shape it
    produced, and returns the source-agnostic BenchmarkResult above."""
    pipeline = pipeline or PipelineData()
    cell: Figure = pipeline.active_benchmark_cell(region, sector)

    if not cell.available:
        return BenchmarkResult(
            available=False, region=region, sector=sector,
            note=cell.note or "No data available for this combination.",
        )

    n = cell.value["respondent_count"]
    if n < MIN_N_FOR_ANY_ESTIMATE:
        return BenchmarkResult(
            available=False, region=region, sector=sector, sample_size=n,
            note=(
                f"Only {n} FinScope respondents matched {sector.lower()} businesses "
                f"in {region} — too few to responsibly estimate a comparison. "
                "Showing a number here would look precise without being reliable, "
                "so this combination is flagged instead of guessed."
            ),
        )

    strand = cell.value["strand_distribution_pct"]
    formality = cell.value.get("registered_pct")
    banked_like = strand.get("Banked", 0) + strand.get("Other formal non-bank", 0)
    formality_term = (formality / 100) if formality is not None else (banked_like / 100)
    score = round(0.6 * (banked_like / 100) + 0.4 * formality_term, 3)
    confident = n >= MIN_N_FOR_CONFIDENT_ESTIMATE

    return BenchmarkResult(
        available=True, region=region, sector=sector, sample_size=n,
        weighted_population=cell.value["weighted_population"],
        strand_distribution=strand,
        formality_rate_pct=formality,
        evidence_tier="model",
        source_label="FinScope Tanzania 2023 national survey sample",
        composite_score=score,
        presumptive_category=_presumptive_category(score),
        presumptive_evidence_tier="hypothesis",
        taxpayer_note=(
            "This compares your business to others like it in a national survey — "
            "it is not a calculation of your income and is not your tax bill."
        ),
        officer_note=(
            "This is a survey-based reference point for discussion with the "
            "taxpayer, not a computed assessment. Use it alongside your own "
            "judgement and any records the taxpayer can provide."
        ),
        note=(
            f"Based on {n} FinScope respondents in this exact region/sector "
            f"combination — {'a small sample, treat as indicative only' if not confident else 'a reasonable sample size for this survey'}."
        ),
    )
