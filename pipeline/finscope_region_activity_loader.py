"""
FinScope Tanzania 2023 region x business-activity prevalence loader
(standalone copy for TRA Innovation 2 -- see the original in
tanzania_policy_agent/finscope_region_activity_loader.py for the full
investigation notes on why this is a prevalence table, not a turnover
calculator).

Differs from the original only in HOW it persists: the original writes
to tanzania_policy_agent's shared evidence_store.db via evidence_db.py's
helpers (appropriate there, since that database is the shared home for
every survey this project loads). This standalone copy has no such
database -- it exists purely to serve this one dashboard -- so it writes
directly to JSON instead of round-tripping through SQLite. Same
computation, same real FinScope data, simpler plumbing.

Investigated before writing (not assumed):
  - D5 (the codebook's only variable with an explicit "business
    activity" value list) is answered by only 496 of 9,915 respondents
    -- a narrow services-only sub-question, too sparse for a real
    regional cross-tab.
  - IncomeMain is populated for the full sample and already
    distinguishes trading/farming/service livelihood categories -- the
    real, usable "activity" dimension.
  - No turnover or income-AMOUNT variable exists anywhere in FinScope
    2023 (checked every codebook label and raw column name).
"""

import os
import json

import pandas as pd

CSV_PATH = "FinScope.csv"
OUTPUT_PATH = "finscope_region_activity.json"

# The four IncomeMain categories that represent an actual own-account
# economic activity a presumptive-tax calculator would apply to.
BUSINESS_ACTIVITY_CATEGORIES = [
    "Traders - non-agricultural",
    "Traders - agricultural products",
    "Service providers",
    "Farmers and fishers",
]


def build_finscope_region_activity_data(csv_path=CSV_PATH, output_path=OUTPUT_PATH):
    """
    Computes a Household_weight-weighted region x business-activity
    prevalence table from FinScope 2023 microdata and writes it to
    output_path as JSON. Returns the same dict it wrote.
    """
    print("\n  Building FinScope region x activity prevalence...")
    if not os.path.exists(csv_path):
        print(f"  ✗ {csv_path} not found")
        return None

    df = pd.read_csv(
        csv_path, usecols=["reg_name", "IncomeMain", "Household_weight"],
        low_memory=False,
    )
    biz = df[df["IncomeMain"].isin(BUSINESS_ACTIVITY_CATEGORIES)].copy()
    if biz.empty:
        print("  ✗ no business-activity respondents found -- check IncomeMain values")
        return None

    rows = []
    for region, region_df in biz.groupby("reg_name"):
        region_total_weight = region_df["Household_weight"].sum()
        for activity, activity_df in region_df.groupby("IncomeMain"):
            weighted_pop = activity_df["Household_weight"].sum()
            pct = (weighted_pop / region_total_weight * 100) if region_total_weight else 0.0
            rows.append({
                "region": region,
                "activity": activity,
                "weighted_population": float(weighted_pop),
                "pct_of_region_business_activity": round(float(pct), 2),
                "respondent_count": int(len(activity_df)),
            })

    out = {
        "source": "FinScope Tanzania 2023 (n=9,915, weighted by Household_weight)",
        "methodology": (
            "Weighted prevalence of four business-activity IncomeMain categories "
            "(Traders - non-agricultural, Traders - agricultural products, Service "
            "providers, Farmers and fishers) within each region. This is a "
            "population-share table, not a turnover/income-amount distribution -- "
            "FinScope 2023 contains no turnover or income-amount variable, checked "
            "exhaustively against the codebook and raw columns."
        ),
        "rows": rows,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"  ✓ {len(rows)} region x activity rows written to {output_path} "
          f"({biz['reg_name'].nunique()} regions x {len(BUSINESS_ACTIVITY_CATEGORIES)} activities)")
    return out


if __name__ == "__main__":
    build_finscope_region_activity_data()
