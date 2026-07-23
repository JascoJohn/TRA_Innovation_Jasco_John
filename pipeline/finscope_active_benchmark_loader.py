"""
FinScope Tanzania 2023 region x business-activity benchmark loader,
for the Active stage's Mzani wa Kodi tool.

Extends finscope_region_activity_loader.py's region x IncomeMain
cross-tab (same four business-activity categories, same regions) with
two more real, respondent-level fields per cell:

  - fasx: FinScope's own financial access strand -- Banked / Other
    formal non-bank / Informal only / Excluded. This is FinScope's
    flagship, internationally standard measure of financial/economic
    engagement -- the closest real, respondent-level proxy this
    dataset has for "how economically active is this business," in
    the total absence of any income or turnover variable.
  - D6_4a: business registration status (Yes/No; a small number of
    blank responses exist and are excluded from the registered-rate
    denominator rather than silently counted as "No").

Investigated before writing (not assumed):
  - Confirmed FinScope 2023 has no income-AMOUNT or turnover variable
    anywhere (see finscope_region_activity_loader.py's own
    investigation notes) -- which is exactly why this loader outputs a
    strand *distribution* and a registration *rate* per cell, never a
    shilling figure. Turning either of those into a presumptive-tax
    category is an illustrative interpretive step, done downstream in
    tdj_lib/benchmark_adapters.py (clearly tagged as such there), not
    a claim made by this file.
  - Per-cell sample sizes are small: median respondent_count across
    the 124 region x activity cells is 14, and 42 of 124 cells have
    fewer than 10 respondents. This loader does not hide that --
    respondent_count is written to every row so the dashboard can
    (and does) refuse an estimate when a cell is too thin, rather than
    presenting a confident-looking number built on a handful of people.
"""

import os
import json

import pandas as pd

CSV_PATH = "FinScope.csv"
OUTPUT_PATH = "finscope_active_benchmark.json"

# Same four categories as finscope_region_activity_loader.py -- the
# IncomeMain values that represent an actual own-account economic
# activity a presumptive-tax tool would apply to.
BUSINESS_ACTIVITY_CATEGORIES = [
    "Traders - non-agricultural",
    "Traders - agricultural products",
    "Service providers",
    "Farmers and fishers",
]

STRAND_CATEGORIES = ["Banked", "Other formal non-bank", "Informal only", "Excluded"]


def build_finscope_active_benchmark_data(csv_path=CSV_PATH, output_path=OUTPUT_PATH):
    """
    Computes a Household_weight-weighted region x business-activity
    benchmark table -- sample size, weighted population, financial
    access strand distribution, and registration rate per cell -- from
    FinScope 2023 microdata, and writes it to output_path as JSON.
    Returns the same dict it wrote.
    """
    print("\n  Building FinScope Active-stage benchmark cells...")
    if not os.path.exists(csv_path):
        print(f"  ERROR: {csv_path} not found")
        return None

    df = pd.read_csv(
        csv_path,
        usecols=["reg_name", "IncomeMain", "Household_weight", "fasx", "D6_4a"],
        low_memory=False,
    )
    biz = df[df["IncomeMain"].isin(BUSINESS_ACTIVITY_CATEGORIES)].copy()
    if biz.empty:
        print("  ERROR: no business-activity respondents found -- check IncomeMain values")
        return None

    rows = []
    for region, region_df in biz.groupby("reg_name"):
        for activity, cell_df in region_df.groupby("IncomeMain"):
            cell_weight = cell_df["Household_weight"].sum()
            if cell_weight <= 0:
                continue

            strand_pct = {}
            for strand in STRAND_CATEGORIES:
                strand_mask = cell_df["fasx"].astype(str).str.strip() == strand
                strand_weight = cell_df.loc[strand_mask, "Household_weight"].sum()
                strand_pct[strand] = round(float(strand_weight / cell_weight * 100), 1)

            # D6_4a has a small number of blank/whitespace responses in
            # the raw data (not just Yes/No) -- excluded from the
            # denominator rather than folded into "not registered".
            reg_valid = cell_df[cell_df["D6_4a"].astype(str).str.strip().isin(["Yes", "No"])]
            reg_valid_weight = reg_valid["Household_weight"].sum()
            registered_weight = reg_valid.loc[
                reg_valid["D6_4a"].astype(str).str.strip() == "Yes", "Household_weight"
            ].sum()
            registered_pct = (
                round(float(registered_weight / reg_valid_weight * 100), 1)
                if reg_valid_weight > 0 else None
            )

            rows.append({
                "region": region,
                "activity": activity,
                "respondent_count": int(len(cell_df)),
                "weighted_population": float(cell_weight),
                "strand_distribution_pct": strand_pct,
                "registered_pct": registered_pct,
                "registered_respondent_count": int(len(reg_valid)),
            })

    out = {
        "source": "FinScope Tanzania 2023 (n=9,915, weighted by Household_weight)",
        "methodology": (
            "For each region x business-activity (IncomeMain) cell: real "
            "respondent count and weighted population (same cells as "
            "finscope_region_activity.json), the weighted distribution across "
            "FinScope's own financial access strand (fasx: Banked / Other "
            "formal non-bank / Informal only / Excluded), and the weighted "
            "business-registration rate (D6_4a). No income, turnover, or "
            "revenue amount is estimated anywhere in this file -- FinScope "
            "2023 has no such variable. Any mapping from these real cell "
            "characteristics to a presumptive-tax category is an illustrative "
            "interpretive step performed downstream by the dashboard, not a "
            "claim made by this loader."
        ),
        "strand_categories": STRAND_CATEGORIES,
        "rows": rows,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    n_thin = sum(1 for r in rows if r["respondent_count"] < 8)
    print(f"  OK: {len(rows)} region x activity benchmark cells written to {output_path} "
          f"({n_thin} cells have fewer than 8 respondents)")
    return out


if __name__ == "__main__":
    build_finscope_active_benchmark_data()
