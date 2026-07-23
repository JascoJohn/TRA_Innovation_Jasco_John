"""
assumption_ledger.py
═══════════════════════════════════════════════════════════════
Tanzania Policy Design Agent — Assumption Ledger
═══════════════════════════════════════════════════════════════

PURPOSE
-------
Reads assumption_ledger.json (written by shared_context.py
as agents run) and formats it into a clean, readable
Appendix D for the final report.

Also provides a register_assumption() wrapper so any agent
can log assumptions in one line without importing the full
shared_context module.

HOW TO USE IN ANY AGENT
------------------------
    from assumption_ledger import log_assumption

    log_assumption(
        text="35% of Entry Stage mobile money users will
              register when offered airtime incentive",
        agent="lifecycle_intervention_agent",
        category="behavioral",
        confidence="MEDIUM",
        evidence="Rwanda behavioral nudge studies show
                  34% conversion rates",
        section="section_4_lifecycle"
    )

PIPELINE POSITION
-----------------
Run after all agents have completed, before agent_v4.py.
Produces assumption_ledger_report.txt for Appendix D.

FILES READ
----------
→ assumption_ledger.json   (written by shared_context.py)

FILES PRODUCED
--------------
→ assumption_ledger_report.txt   (Appendix D — readable)
→ assumption_ledger_summary.json (structured — for v4)
"""

import os
import json
from datetime import datetime


# ============================================================
# FILE PATHS
# ============================================================
LEDGER_FILE  = "assumption_ledger.json"
REPORT_FILE  = "assumption_ledger_report.txt"
SUMMARY_FILE = "assumption_ledger_summary.json"


# ============================================================
# CATEGORY LABELS
# Human-readable versions of category codes
# ============================================================
CATEGORY_LABELS = {
    "behavioral":  "Behavioral / Psychological",
    "economic":    "Economic / Financial",
    "political":   "Political / Institutional",
    "technical":   "Technical / Operational",
    "demographic": "Demographic / Population",
    "legal":       "Legal / Regulatory",
}

CONFIDENCE_LABELS = {
    "HIGH":   "High — supported by strong evidence",
    "MEDIUM": "Medium — plausible but not fully tested",
    "LOW":    "Low — working assumption requiring validation",
}


# ============================================================
# SIMPLE WRAPPER
# Agents call this instead of importing shared_context
# ============================================================
def log_assumption(
    text,
    agent,
    category="behavioral",
    confidence="MEDIUM",
    evidence=None,
    section=None
):
    """
    Logs one assumption to assumption_ledger.json.
    Call this from any agent file.

    Parameters
    ----------
    text       : The assumption statement
    agent      : Name of the agent making the assumption
    category   : behavioral / economic / political /
                 technical / demographic / legal
    confidence : HIGH / MEDIUM / LOW
    evidence   : What evidence supports this assumption
    section    : Which report section uses this assumption
    """
    try:
        from shared_context import register_assumption
        return register_assumption(
            assumption_text=text,
            made_by_agent=agent,
            category=category,
            confidence=confidence,
            evidence_support=evidence,
            section_reference=section
        )
    except ImportError:
        # Fallback: write directly to ledger file
        # if shared_context is not available
        _write_direct(text, agent, category,
                      confidence, evidence, section)


def _write_direct(text, agent, category,
                  confidence, evidence, section):
    """Fallback writer if shared_context is unavailable."""
    import uuid

    assumption = {
        "assumption_id": f"ASS-{str(uuid.uuid4())[:6].upper()}",
        "assumption_text": text,
        "made_by_agent": agent,
        "category": category,
        "confidence": confidence,
        "evidence_support": evidence,
        "stress_tested": False,
        "stress_test_result": None,
        "section_reference": section,
        "created_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r", encoding="utf-8") as f:
            ledger = json.load(f)
    else:
        ledger = {
            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "total": 0,
            "assumptions": []
        }

    # Dedup on (assumption_text, made_by_agent), matching the pattern
    # already used in evidence_db.py's DELETE-before-INSERT loaders --
    # without this, a resumed/re-run pipeline appends a fresh UUID-keyed
    # duplicate every call since assumption_id is always freshly generated.
    duplicate = any(
        a["assumption_text"] == text and a["made_by_agent"] == agent
        for a in ledger["assumptions"]
    )
    if duplicate:
        return

    ledger["assumptions"].append(assumption)
    ledger["total"] = len(ledger["assumptions"])

    with open(LEDGER_FILE, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)


# ============================================================
# LEDGER READER
# ============================================================
def load_ledger():
    """
    Loads assumption_ledger.json.
    Returns empty ledger if file does not exist.
    """
    if not os.path.exists(LEDGER_FILE):
        print(f"  ✗ {LEDGER_FILE} not found")
        print("  → Run the agent pipeline first")
        return {"total": 0, "assumptions": []}

    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# STATISTICS
# ============================================================
def compute_statistics(assumptions):
    """
    Computes summary statistics across all assumptions.
    Returns a dict of counts and breakdowns.
    """
    if not assumptions:
        return {
            "total": 0,
            "by_confidence": {},
            "by_category": {},
            "by_agent": {},
            "stress_tested": 0,
            "untested": 0,
            "high_risk": []
        }

    by_confidence = {}
    by_category   = {}
    by_agent      = {}
    stress_tested = 0
    high_risk     = []

    for a in assumptions:
        # Confidence breakdown
        conf = a.get("confidence", "MEDIUM")
        by_confidence[conf] = by_confidence.get(conf, 0) + 1

        # Category breakdown
        cat = a.get("category", "behavioral")
        by_category[cat] = by_category.get(cat, 0) + 1

        # Agent breakdown
        agent = a.get("made_by_agent", "unknown")
        by_agent[agent] = by_agent.get(agent, 0) + 1

        # Stress tested
        if a.get("stress_tested"):
            stress_tested += 1

        # High risk = LOW confidence + not stress tested
        if (conf == "LOW" and
                not a.get("stress_tested")):
            high_risk.append(a)

    return {
        "total": len(assumptions),
        "by_confidence": by_confidence,
        "by_category": by_category,
        "by_agent": by_agent,
        "stress_tested": stress_tested,
        "untested": len(assumptions) - stress_tested,
        "high_risk": high_risk
    }


# ============================================================
# REPORT GENERATOR
# Produces the readable Appendix D text
# ============================================================
def generate_report(ledger):
    """
    Formats assumption_ledger.json into a readable
    Appendix D text report.
    Returns the full report as a string.
    """
    assumptions = ledger.get("assumptions", [])
    stats = compute_statistics(assumptions)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []

    # ── Header ──────────────────────────────────────────────
    lines += [
        "═" * 65,
        "  APPENDIX D — ASSUMPTION LEDGER",
        "  Tanzania Behavioral Lifecycle Tax Compliance Strategy",
        f"  Generated: {timestamp}",
        "═" * 65,
        "",
        "PURPOSE",
        "─" * 40,
        "This ledger documents every assumption made by every",
        "agent in the pipeline. Each assumption is categorized,",
        "confidence-rated, and linked to a report section.",
        "Stress-tested assumptions are flagged accordingly.",
        "",
        "METHODOLOGY NOTE",
        "─" * 40,
        "Confidence ratings:",
        "  HIGH   — supported by survey data, API-verified",
        "           statistics, or published study findings",
        "  MEDIUM — plausible given comparable country evidence",
        "           but not directly verified for Tanzania",
        "  LOW    — working assumption requiring pilot validation",
        "",
    ]

    # ── Summary statistics ──────────────────────────────────
    lines += [
        "SUMMARY STATISTICS",
        "─" * 40,
        f"  Total assumptions logged:   {stats['total']}",
        f"  Stress tested:              {stats['stress_tested']}",
        f"  Awaiting stress test:       {stats['untested']}",
        f"  High risk (LOW, untested):  {len(stats['high_risk'])}",
        "",
        "  By confidence level:",
    ]
    for conf, count in sorted(stats["by_confidence"].items()):
        label = CONFIDENCE_LABELS.get(conf, conf)
        pct = round(count / stats["total"] * 100) \
            if stats["total"] > 0 else 0
        lines.append(f"    {conf:<8} {count:>3}  ({pct}%)  "
                     f"— {label}")

    lines += [
        "",
        "  By category:",
    ]
    for cat, count in sorted(
        stats["by_category"].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"    {label:<35} {count:>3}")

    lines += [
        "",
        "  By agent:",
    ]
    for agent, count in sorted(
        stats["by_agent"].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        lines.append(f"    {agent:<45} {count:>3}")

    # ── High risk assumptions ────────────────────────────────
    if stats["high_risk"]:
        lines += [
            "",
            "HIGH RISK ASSUMPTIONS (LOW confidence, not yet tested)",
            "─" * 40,
            "These require priority attention before final report.",
            "",
        ]
        for a in stats["high_risk"]:
            lines += [
                f"  ID:      {a.get('assumption_id', 'N/A')}",
                f"  Agent:   {a.get('made_by_agent', 'N/A')}",
                f"  Section: {a.get('section_reference', 'N/A')}",
                f"  Text:    {a.get('assumption_text', '')}",
                "",
            ]

    # ── Full assumption register ─────────────────────────────
    lines += [
        "",
        "═" * 65,
        "  FULL ASSUMPTION REGISTER",
        "═" * 65,
        "",
    ]

    # Group by category for readability
    by_cat = {}
    for a in assumptions:
        cat = a.get("category", "behavioral")
        by_cat.setdefault(cat, []).append(a)

    for cat in sorted(by_cat.keys()):
        cat_label = CATEGORY_LABELS.get(cat, cat).upper()
        lines += [
            f"{'─' * 65}",
            f"  {cat_label} ASSUMPTIONS",
            f"{'─' * 65}",
            "",
        ]

        for a in by_cat[cat]:
            conf = a.get("confidence", "MEDIUM")
            tested = "✓ Tested" if a.get("stress_tested") \
                else "○ Awaiting test"
            aid = a.get("assumption_id", "N/A")

            lines += [
                f"  [{aid}]  Confidence: {conf}  |  {tested}",
                f"  Agent:   {a.get('made_by_agent', 'N/A')}",
                f"  Section: {a.get('section_reference', 'N/A')}",
                "",
                f"  ASSUMPTION:",
                f"  {a.get('assumption_text', '')}",
                "",
            ]

            evidence = a.get("evidence_support")
            if evidence:
                lines += [
                    f"  EVIDENCE:",
                    f"  {evidence}",
                    "",
                ]

            result = a.get("stress_test_result")
            if result:
                lines += [
                    f"  STRESS TEST RESULT:",
                    f"  {result}",
                    "",
                ]

            lines.append("  " + "·" * 60)
            lines.append("")

    # ── Footer ───────────────────────────────────────────────
    lines += [
        "═" * 65,
        "  END OF APPENDIX D",
        f"  Tanzania Policy Design Agent — {timestamp}",
        "  FinScope Tanzania 2023 data used under FSDT",
        "  data usage agreement for non-profit research.",
        "═" * 65,
    ]

    return "\n".join(lines)


# ============================================================
# SUMMARY JSON
# Structured version for agent_v4.py to use
# ============================================================
def generate_summary_json(ledger):
    """
    Produces a structured JSON summary of the ledger
    for agent_v4.py to embed in the final report.
    """
    assumptions = ledger.get("assumptions", [])
    stats = compute_statistics(assumptions)

    summary = {
        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "statistics": {
            "total": stats["total"],
            "stress_tested": stats["stress_tested"],
            "untested": stats["untested"],
            "high_risk_count": len(stats["high_risk"]),
            "by_confidence": stats["by_confidence"],
            "by_category":   stats["by_category"],
            "by_agent":      stats["by_agent"],
        },
        "high_risk_assumptions": [
            {
                "id":       a.get("assumption_id"),
                "agent":    a.get("made_by_agent"),
                "text":     a.get("assumption_text"),
                "section":  a.get("section_reference"),
            }
            for a in stats["high_risk"]
        ],
        "all_assumptions": assumptions,
        "methodology": (
            "Every assumption made by every agent in the "
            "Tanzania Policy Design Agent pipeline is logged "
            "here with its confidence rating, supporting "
            "evidence, and stress test status. HIGH confidence "
            "assumptions are backed by FinScope Tanzania 2023 "
            "microdata, World Bank API figures, or IMF "
            "DataMapper statistics. MEDIUM assumptions draw "
            "on comparable country evidence. LOW assumptions "
            "are flagged for pilot validation before national "
            "rollout."
        )
    }

    return summary


# ============================================================
# MAIN RUNNER
# ============================================================
def run_assumption_ledger():
    """
    Master function.
    Reads the ledger, generates the report and summary,
    saves both to disk.
    """
    print("\n" + "═" * 60)
    print("  ASSUMPTION LEDGER")
    print("  Formatting Appendix D")
    print("═" * 60 + "\n")

    # Step 1: Load ledger
    print("STEP 1: LOADING ASSUMPTION LEDGER")
    print("-" * 40)
    ledger = load_ledger()
    total = ledger.get("total", 0)
    print(f"  Assumptions found: {total}")

    if total == 0:
        print("\n  No assumptions logged yet.")
        print("  Run the agent pipeline first, then re-run")
        print("  this file to generate Appendix D.")
        return

    # Step 2: Compute statistics
    print("\nSTEP 2: COMPUTING STATISTICS")
    print("-" * 40)
    assumptions = ledger.get("assumptions", [])
    stats = compute_statistics(assumptions)

    print(f"  By confidence:")
    for conf, count in sorted(
            stats["by_confidence"].items()):
        print(f"    {conf}: {count}")

    print(f"  High risk (LOW + untested): "
          f"{len(stats['high_risk'])}")
    print(f"  Stress tested: {stats['stress_tested']}")

    # Step 3: Generate readable report
    print("\nSTEP 3: GENERATING APPENDIX D REPORT")
    print("-" * 40)
    report_text = generate_report(ledger)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  ✓ Saved: {REPORT_FILE}")

    # Step 4: Generate structured JSON
    print("\nSTEP 4: GENERATING STRUCTURED SUMMARY")
    print("-" * 40)
    summary = generate_summary_json(ledger)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved: {SUMMARY_FILE}")

    # Final summary
    print("\n" + "═" * 60)
    print("  ASSUMPTION LEDGER COMPLETE")
    print("═" * 60)
    print(f"\n  Total assumptions documented: {total}")
    print(f"  High risk flags:              "
          f"{len(stats['high_risk'])}")
    print(f"\n  Files produced:")
    print(f"  → {REPORT_FILE}  (Appendix D)")
    print(f"  → {SUMMARY_FILE}")
    print(f"\n  Next step: Run agent_v3c.py")
    print("═" * 60)


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    run_assumption_ledger()
    