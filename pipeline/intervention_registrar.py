"""
intervention_registrar.py

One-time bridge script. Confirmed by direct inspection: register_intervention()
and validate_intervention() (both in shared_context.py) are called ZERO times
anywhere in this codebase -- not by agent_v3b.py, phase3_agents.py, agent_v3.py,
agent_v3c.py, or debate_agents.py. intervention_register.json has therefore
always been an empty skeleton, and get_approved_interventions() always
returns []. This is a genuine prerequisite gap, not something to silently
route around -- flagged and confirmed with the user before building this.

This script does NOT touch agent_v3b.py/agent_v3c.py (per explicit
constraint). It populates the registry from what those files ALREADY
produced, using only real content:

  1. report_sections.json['section_5_innovations'] -- policy_innovation_agent's
     8 named, structured interventions (regex-parsed against its current
     6-part prompt header format -- NOT the stale pre-retrofit format the
     saved file had; re-generate section_5_innovations before running this
     if it's still in the old "THE INNOVATION:" style rather than
     "1. THE BOTTLENECK:").
  2. economic_model.json['cost_benefit']['interventions'] -- 5 Python-
     calculated interventions with real cost/revenue/ROI figures.

These are two INDEPENDENTLY NAMED lists (LLM-generated Swahili concept names
vs. the economic model's own generic English names) with no reliable 1:1
correspondence -- confirmed by inspection, not assumed. Rather than guess a
pairing and risk attributing one intervention's real financial figures to a
completely different intervention's concept, they are registered as SEPARATE
entries, each tagged with its real origin:
  - tags=["llm_generated_narrative"]  -- from section_5_innovations
  - tags=["economic_model_calculated"] -- from economic_model.json

feasibility_score/impact_score are NOT fabricated -- they stay 0 (this
project's existing schema default, since register_intervention() has no
None option for these) with a note that no real scoring agent has run.
validation_status stays 'pending' for everything -- per explicit direction,
nothing is auto-approved just because the 2/3-critic process never ran.

Usage:
    python intervention_registrar.py
"""

import re
import json

from shared_context import register_intervention, LIFECYCLE_STAGES

SECTIONS_FILE = "report_sections.json"
ECON_FILE = "economic_model.json"
REGISTER_FILE = "intervention_register.json"

_STAGE_ALIASES = {
    "seed": "seed", "entry": "entry", "active": "active",
    "enterprise": "enterprise", "asset": "asset", "legacy": "legacy",
}


def _normalize_stage(raw_stage):
    """Maps free-text stage mentions ('Seed Stage (Ages 6-18)', 'Entry',
    'CROSS-CUTTING') to a real LIFECYCLE_STAGES value, or None if it's a
    cross-cutting intervention with no single stage."""
    if not raw_stage:
        return None
    lowered = raw_stage.lower()
    if "cross" in lowered:
        return None
    for stage in LIFECYCLE_STAGES:
        if stage in lowered:
            return stage
    return None


def parse_llm_innovations(content):
    """
    Parses policy_innovation_agent's real output against its CURRENT
    6-part prompt structure:
        INTERVENTION [N] OF 8
        NAME: ...
        TAGLINE: ...
        LIFECYCLE STAGE: ...
        1. THE BOTTLENECK: ...
        ...
        4. IMPLEMENTATION DIFFICULTY: ... Budget estimate: TZS [x] ...
        5. REVENUE/COMPLIANCE IMPLICATION: ...
        6. SELF-CHALLENGE: ...
    Returns [] (not a crash) if the content doesn't match this structure --
    e.g. if it's still the stale pre-retrofit format. Never fabricates a
    parse result from unrecognized text.
    """
    if not content:
        return []

    blocks = re.split(r"INTERVENTION \d+ OF \d+", content)[1:]
    results = []
    for block in blocks:
        # Tolerant of markdown emphasis/headers ("**NAME:**", "### 1. The
        # Bottleneck") and case drift ("The Bottleneck" vs "THE BOTTLENECK") --
        # the model doesn't reproduce the prompt's exact literal formatting
        # every time, so anchor on the stable numbered-section structure
        # rather than exact casing/markdown.
        name_m = re.search(r"NAME:\**\s*(.+)", block)
        tagline_m = re.search(r"TAGLINE:\**\s*(.+)", block)
        stage_m = re.search(r"LIFECYCLE STAGE:\**\s*(.+)", block)
        bottleneck_m = re.search(
            r"#{0,3}\s*1\.[^\n]*\n+(.+?)(?=\n\s*#{0,3}\s*2\.)", block,
            re.DOTALL | re.IGNORECASE)
        difficulty_m = re.search(r"Overall difficulty:\s*([^\n(]+)", block, re.IGNORECASE)
        # Captures an optional range ("TZS 200-800 million"): the original
        # regex's [\d,.]+ character class stops at the hyphen, silently
        # keeping only "200" and understating a range by up to several
        # times. Group 2 is the optional upper-bound number if the model
        # wrote a range.
        budget_m = re.search(
            r"Budget estimate:\s*TZS\s*([\d,.]+)\s*(?:[-–—]\s*([\d,.]+))?"
            r"\s*(million|billion|trillion)?",
            block, re.IGNORECASE)
        self_challenge_m = re.search(
            r"#{0,3}\s*6\.[^\n]*\n+(.+?)(?=\n\s*#{0,3}\s*CONNECTION TO CIVIC PARTNER|\Z)",
            block, re.DOTALL | re.IGNORECASE)

        if not name_m:
            continue  # doesn't match the expected structure -- skip, don't fabricate

        cost_tzs = None
        if budget_m:
            # Take the upper bound of a range rather than averaging --
            # for a cost estimate, understating the budget is the more
            # harmful direction of error, so the conservative (higher)
            # figure is used.
            raw_amount = float(
                (budget_m.group(2) or budget_m.group(1)).replace(",", "")
            )
            multiplier = {"million": 1e6, "billion": 1e9, "trillion": 1e12}.get(
                (budget_m.group(3) or "").lower(), 1)
            cost_tzs = raw_amount * multiplier

        results.append({
            # .strip("*") added in this copy: the regex only strips
            # LEADING "**" after "NAME:" -- when the model closes the
            # name's own bold markers at end-of-line (e.g. "NAME: Foo**"),
            # a trailing "**" survived into every title. Confirmed against
            # a real run of this standalone copy before this fix.
            "title": name_m.group(1).strip().strip("*").strip(),
            "tagline": tagline_m.group(1).strip() if tagline_m else None,
            "lifecycle_stage": _normalize_stage(stage_m.group(1) if stage_m else None),
            "description": (bottleneck_m.group(1).strip() if bottleneck_m else "")[:2000],
            "cost_estimate_tzs": cost_tzs,
            "difficulty": difficulty_m.group(1).strip() if difficulty_m else None,
            "self_challenge": self_challenge_m.group(1).strip() if self_challenge_m else None,
        })
    return results


_TIMEFRAME_ORDER = ["immediate", "short_term", "medium_term", "long_term"]


def _infer_timeframe(cost_tzs, difficulty=None):
    """Infers an implementation timeframe bucket (the enum documented in
    shared_context.py's register_intervention() docstring) from fields
    that are already real and available -- never guessed independently
    of them. cost_estimate_tzs is the primary signal: a bigger budget
    implies more procurement/institutional-coordination scale, which is
    a reasonable proxy for how long an intervention takes to stand up.
    difficulty (the LLM-generated interventions' own self-rated
    "IMPLEMENTATION DIFFICULTY" field) nudges MEDIUM/HIGH-difficulty
    items one bucket longer than cost alone would suggest.

    Deliberately NOT using economic_model.json's "risk" field for the
    economic-model-derived interventions here -- that field rates
    confidence in the modeled REVENUE projection, not implementation
    difficulty, and conflating the two would be a real modeling choice
    dressed up as a fact. Cost alone is used for those entries.

    Returns None (not a guess) if cost_tzs is unavailable -- matches
    agent_v4.py's existing honest-gap handling for a missing timeframe.
    """
    if cost_tzs is None:
        return None

    if cost_tzs < 100_000_000:
        bucket = "immediate"
    elif cost_tzs < 500_000_000:
        bucket = "short_term"
    elif cost_tzs < 2_000_000_000:
        bucket = "medium_term"
    else:
        bucket = "long_term"

    if difficulty and difficulty.upper() in ("MEDIUM", "HIGH"):
        idx = min(_TIMEFRAME_ORDER.index(bucket) + 1, len(_TIMEFRAME_ORDER) - 1)
        bucket = _TIMEFRAME_ORDER[idx]

    return bucket


def parse_economic_model_interventions(econ_path=ECON_FILE):
    """Reads economic_model.json['cost_benefit']['interventions'] --
    already-real, Python-calculated figures. Returns [] if the file or
    key is missing, never a fabricated placeholder."""
    try:
        with open(econ_path, "r", encoding="utf-8") as f:
            econ = json.load(f)
    except FileNotFoundError:
        return []
    return econ.get("cost_benefit", {}).get("interventions", [])


def register_all(sections_path=SECTIONS_FILE, econ_path=ECON_FILE,
                  register_path=REGISTER_FILE, force=False):
    """
    register_intervention() has no dedup -- every call appends a fresh
    randomly-generated intervention_id. Wired into run_pipeline.py (a
    step that may re-run against unchanged inputs across resumed runs),
    so guard against re-registering the same content every time and
    silently doubling the registry + orphaning old intervention_reports/
    PDFs under stale IDs each run. Pass force=True to bypass (matches
    run_pipeline.py's own --force convention).
    """
    if not force:
        try:
            with open(register_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("total", 0) > 0:
                print(f"  SKIP: {register_path} already has "
                      f"{existing['total']} intervention(s) registered "
                      f"-- not re-registering (pass force=True to override).")
                return [(i.get("intervention_id"), i.get("title"), None)
                        for i in existing.get("interventions", [])]
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    with open(sections_path, "r", encoding="utf-8") as f:
        sections = json.load(f)
    innovations_content = sections.get("section_5_innovations", {}).get("content", "")

    llm_interventions = parse_llm_innovations(innovations_content)
    econ_interventions = parse_economic_model_interventions(econ_path)

    if not llm_interventions:
        print(f"  WARNING: parsed 0 interventions from section_5_innovations -- "
              f"either it's empty or still in the stale pre-6-part-retrofit "
              f"format ('THE INNOVATION:' instead of '1. THE BOTTLENECK:'). "
              f"Re-run policy_innovation_agent to refresh it before running this.")

    registered_ids = []

    for item in llm_interventions:
        intervention_id = register_intervention(
            title=item["title"],
            description=item["description"] or item["tagline"] or "(no description parsed)",
            lifecycle_stage=item["lifecycle_stage"],
            objectives=[],  # not reliably parseable from this prompt's structure -- left empty, not guessed
            cost_estimate_tzs=item["cost_estimate_tzs"],
            revenue_estimate_tzs=None,  # this prompt format doesn't produce a specific revenue TZS figure -- real gap, not fabricated
            timeframe=_infer_timeframe(item["cost_estimate_tzs"], item["difficulty"]),
            creating_agent="policy_innovation_agent",
            tags=["llm_generated_narrative"] + ([item["difficulty"]] if item["difficulty"] else []),
        )
        registered_ids.append((intervention_id, item["title"], "llm_generated_narrative"))
        print(f"  Registered (LLM-generated): {intervention_id} -- {item['title']}")

    for econ_item in econ_interventions:
        intervention_id = register_intervention(
            title=econ_item.get("name", "(unnamed)"),
            description=(
                f"Python-calculated intervention from economic_model.py's cost-benefit "
                f"model. No LLM-generated narrative/mechanism matched to this entry -- "
                f"see llm_generated_narrative-tagged entries for the creative concepts."
            ),
            lifecycle_stage=None,  # economic model doesn't tag stage as a structured field
            objectives=[],
            cost_estimate_tzs=econ_item.get("implementation_cost_tzs"),
            revenue_estimate_tzs=econ_item.get("annual_revenue_tzs"),
            timeframe=_infer_timeframe(econ_item.get("implementation_cost_tzs")),
            creating_agent="economic_model.py",
            tags=["economic_model_calculated"],
        )
        registered_ids.append((intervention_id, econ_item.get("name"), "economic_model_calculated"))
        print(f"  Registered (economic-model): {intervention_id} -- {econ_item.get('name')}")

    print(f"\n  Total registered: {len(registered_ids)} "
          f"({len(llm_interventions)} LLM-generated, {len(econ_interventions)} economic-model)")
    print("  All validation_status='pending' -- the 2/3-critic process has "
          "never actually run on any of these, so none are auto-approved.")
    return registered_ids


if __name__ == "__main__":
    import sys
    register_all(force="--force" in sys.argv)
