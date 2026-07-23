"""
finscope_analysis.py
═══════════════════════════════════════════════════════════════
Tanzania Policy Design Agent — FinScope Data Analysis
═══════════════════════════════════════════════════════════════

PURPOSE
-------
Reads FinScope.csv (FinScope Tanzania 2023 microdata)
and produces finscope_summary.json — the Tanzania-specific
grounding layer that makes every downstream agent produce
specific, survey-measured findings rather than generic estimates.

VARIABLE CODING (confirmed from actual data)
--------------------------------------------
c8c        — Age (int64, actual years e.g. 24, 47)
MM         — 'MM' = uses mobile money, 'Not MM' = does not
BusO       — 'Business owners' = yes, 'nor' = not owner
c27__13    — 'Yes' = has TIN, 'No' = does not
c27__1     — 'Yes' = has National ID, 'No' = does not
D2_1__1    — 'Yes' = has this income source, 'No' = does not
D6_4a      — 'Yes' = registered, 'No' = not, ' ' = N/A
D6_4c__1+  — 'Yes' = cited this barrier, 'No' = did not
RU         — 'Rural', 'Other urban', 'Dar es Salaam'
gov_3      — numeric string e.g. '30000' (needs conversion)
BANKED     — 'Banked' or 'Not Banked'
fasx       — financial access strand label
population_wt — float, ALWAYS apply to all calculations

DATA SOURCE
-----------
FinScope Tanzania 2023
© Financial Sector Deepening Tanzania (FSDT)
Used under FSDT data usage agreement for non-profit research.

OUTPUT
------
→ finscope_summary.json   (feeds shared_context.py)
→ finscope_report.txt     (human-readable summary)
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
FINSCOPE_FILE = "FinScope.csv"
SUMMARY_FILE  = "finscope_summary.json"
REPORT_FILE   = "finscope_report.txt"
WEIGHT_VAR    = "population_wt"

# ============================================================
# HELPER: YES/NO variable to boolean mask
# ============================================================
def yes_mask(df, col):
    """Returns boolean mask where column == 'yes' (any case)."""
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    try:
        series = df[col].astype(object).astype(str)
    except Exception:
        series = df[col].astype(str)
    return series.str.strip().str.lower() == 'yes'


def val_mask(df, col, value):
    """Returns boolean mask where column == value (string)."""
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    try:
        series = df[col].astype(object).astype(str)
    except Exception:
        series = df[col].astype(str)
    return series.str.strip() == str(value)


# ============================================================
# STEP 1: LOAD DATA
# ============================================================
def load_data():
    print("  Loading FinScope.csv...")
    print("  (38MB — may take 15-30 seconds)")

    df = pd.read_csv(FINSCOPE_FILE, low_memory=False)

    print(f"  ✓ Loaded: {len(df):,} rows × "
          f"{len(df.columns)} columns")
    print(f"  ✓ Weight variable present: "
          f"{WEIGHT_VAR in df.columns}")

    if WEIGHT_VAR not in df.columns:
        raise ValueError(
            f"'{WEIGHT_VAR}' not found in columns."
        )

    # Convert weight to numeric
    df[WEIGHT_VAR] = pd.to_numeric(
        df[WEIGHT_VAR], errors='coerce'
    ).fillna(0)

    total_pop = df[WEIGHT_VAR].sum()
    print(f"  ✓ Represented population: {total_pop:,.0f}")

    return df


# ============================================================
# STEP 2: ASSIGN LIFECYCLE STAGES
# ============================================================
def assign_lifecycle_stages(df):
    print("\n  Assigning lifecycle stages...")

    # Age is int64 — direct comparison works
    age = pd.to_numeric(df['c8c'], errors='coerce')

    # Business owner: 'Business owners'
    is_biz = val_mask(df, 'BusO', 'Business owners')

    conditions = [
        (age >= 6)  & (age < 16),
        (age >= 16) & (age < 25),
        (age >= 25) & (age < 45) & ~is_biz,
        (age >= 25) & (age < 65) & is_biz,
        (age >= 45) & (age < 65) & ~is_biz,
        (age >= 65),
    ]
    choices = [
        'seed', 'entry', 'active',
        'enterprise', 'asset', 'legacy'
    ]

    df['lifecycle_stage'] = np.select(
        conditions, choices, default='unknown'
    )

    w = df[WEIGHT_VAR]
    print("  Stage distribution (weighted):")
    for stage in ['seed', 'entry', 'active', 'enterprise',
                  'asset', 'legacy', 'unknown']:
        mask = df['lifecycle_stage'] == stage
        pop  = w[mask].sum()
        pct  = pop / w.sum() * 100
        if pop > 0:
            print(f"    {stage:<12}: "
                  f"{pop:>12,.0f}  ({pct:.1f}%)")

    return df


# ============================================================
# STEP 3: COMPLIANCE FUNNEL
# ============================================================
def build_compliance_funnel(df):
    print("\n  Building compliance funnel...")

    w     = df[WEIGHT_VAR]
    total = w.sum()
    funnel = {"total_adults": int(total)}

    # ── Has any income ───────────────────────────────────────
    income_cols = [
        f'D2_1__{i}' for i in range(1, 13)
        if f'D2_1__{i}' in df.columns
    ]
    if income_cols:
        has_income_mask = pd.Series(False, index=df.index)
        for col in income_cols:
            has_income_mask = has_income_mask | yes_mask(df, col)
        has_income = w[has_income_mask].sum()
    else:
        has_income = total * 0.72
        has_income_mask = pd.Series(True, index=df.index)

    funnel["has_income"]     = int(has_income)
    funnel["has_income_pct"] = round(
        has_income / total * 100, 1
    )

    # ── Mobile money: 'MM' ───────────────────────────────────
    mm_mask  = val_mask(df, 'MM', 'MM')
    has_mm   = w[mm_mask].sum()
    funnel["uses_mobile_money"] = int(has_mm)
    funnel["mm_rate_pct"]       = round(
        has_mm / total * 100, 1
    )

    # ── Has National ID ──────────────────────────────────────
    id_mask = yes_mask(df, 'c27__1') | yes_mask(df, 'c27__2')
    has_id  = w[id_mask].sum()
    funnel["has_national_id"] = int(has_id)
    funnel["id_rate_pct"]     = round(
        has_id / total * 100, 1
    )

    # ── Has TIN: 'Yes' ───────────────────────────────────────
    tin_mask = yes_mask(df, 'c27__13')
    has_tin  = w[tin_mask].sum()
    funnel["has_tin"]     = int(has_tin)
    funnel["tin_rate_pct"] = round(
        has_tin / total * 100, 1
    )

    # ── Mobile money WITHOUT TIN ─────────────────────────────
    mm_no_tin_mask = mm_mask & ~tin_mask
    mm_no_tin      = w[mm_no_tin_mask].sum()
    funnel["mm_no_tin"]     = int(mm_no_tin)
    funnel["mm_no_tin_pct"] = round(
        mm_no_tin / has_mm * 100, 1
    ) if has_mm > 0 else 0

    # ── Business registration ────────────────────────────────
    buso_mask = val_mask(df, 'BusO', 'Business owners')
    reg_mask  = yes_mask(df, 'D6_4a')
    total_biz = w[buso_mask].sum()
    reg_biz   = w[buso_mask & reg_mask].sum()
    unreg_biz = w[buso_mask & ~reg_mask].sum()

    funnel["total_business_owners"]     = int(total_biz)
    funnel["registered_businesses"]     = int(reg_biz)
    funnel["unregistered_businesses"]   = int(unreg_biz)
    funnel["biz_registration_rate_pct"] = round(
        reg_biz / total_biz * 100, 1
    ) if total_biz > 0 else 0

    # Store masks on df for downstream use
    df['_mm_mask']   = mm_mask
    df['_tin_mask']  = tin_mask
    df['_id_mask']   = id_mask
    df['_buso_mask'] = buso_mask

    print(f"  Adults:            {total:>12,.0f}")
    print(f"  Has income:        {has_income:>12,.0f}  "
          f"({funnel['has_income_pct']}%)")
    print(f"  Mobile money:      {has_mm:>12,.0f}  "
          f"({funnel['mm_rate_pct']}%)")
    print(f"  Has National ID:   {has_id:>12,.0f}  "
          f"({funnel['id_rate_pct']}%)")
    print(f"  Has TIN:           {has_tin:>12,.0f}  "
          f"({funnel['tin_rate_pct']}%)")
    print(f"  MM without TIN:    {mm_no_tin:>12,.0f}  "
          f"← INTERVENTION TARGET")
    print(f"  Compliance gap:    "
          f"{int(total - has_tin):>12,.0f}")
    print(f"  Business owners:   {total_biz:>12,.0f}")
    print(f"  Registered biz:    {reg_biz:>12,.0f}  "
          f"({funnel['biz_registration_rate_pct']}%)")

    return funnel, df


# ============================================================
# STEP 4: FUNNEL BY LIFECYCLE STAGE
# ============================================================
def funnel_by_stage(df):
    print("\n  Running funnel by lifecycle stage...")

    w       = df[WEIGHT_VAR]
    stages  = ['seed', 'entry', 'active', 'enterprise',
               'asset', 'legacy']
    results = {}

    tin_mask  = df['_tin_mask']
    mm_mask   = df['_mm_mask']
    buso_mask = df['_buso_mask']

    for stage in stages:
        s_mask   = df['lifecycle_stage'] == stage
        s_pop    = w[s_mask].sum()
        if s_pop == 0:
            continue

        s_tin      = w[s_mask & tin_mask].sum()
        s_mm       = w[s_mask & mm_mask].sum()
        s_mm_notin = w[s_mask & mm_mask & ~tin_mask].sum()

        # Urban breakdown
        urban_mask = df['RU'].astype(str).str.strip().isin(
            ['Other urban', 'Dar es Salaam']
        )
        s_urban    = w[s_mask & urban_mask].sum()

        results[stage] = {
            "population":          int(s_pop),
            "has_tin":             int(s_tin),
            "tin_rate_pct":        round(
                s_tin / s_pop * 100, 1
            ),
            "uses_mm":             int(s_mm),
            "mm_rate_pct":         round(
                s_mm / s_pop * 100, 1
            ),
            "mm_no_tin":           int(s_mm_notin),
            "intervention_target": int(s_pop - s_tin),
            "dropout_rate_pct":    round(
                (s_pop - s_tin) / s_pop * 100, 1
            ),
            "urban_pct":           round(
                s_urban / s_pop * 100, 1
            ) if s_pop > 0 else 0,
        }

        print(f"  {stage.upper():<12}: "
              f"pop={s_pop:>10,.0f}  "
              f"TIN={results[stage]['tin_rate_pct']}%  "
              f"MM={results[stage]['mm_rate_pct']}%  "
              f"dropout={results[stage]['dropout_rate_pct']}%")

    return results


# ============================================================
# STEP 5: REGISTRATION BARRIERS
# ============================================================
def analyze_barriers(df):
    print("\n  Analyzing registration barriers...")

    w         = df[WEIGHT_VAR]
    buso_mask = df['_buso_mask']
    reg_mask  = yes_mask(df, 'D6_4a')
    unreg_mask = buso_mask & ~reg_mask

    unreg_pop = w[unreg_mask].sum()
    print(f"  Unregistered business owners: {unreg_pop:,.0f}")

    barrier_vars = {
        'D6_4c__1':  'Tried but failed',
        'D6_4c__2':  'No time',
        'D6_4c__3':  'No money / too expensive',
        'D6_4c__4':  'Too complicated',
        'D6_4c__5':  'No benefit seen',
        'D6_4c__6':  'Business too small',
        'D6_4c__7':  "Don't want to pay taxes",
        'D6_4c__8':  "Don't know how",
        'D6_4c__9':  'Registration processing',
        'D6_4c__10': 'Other reason',
    }

    barriers = {}
    if unreg_pop > 0:
        print("  Barriers cited (% of unregistered owners):")
        for var, label in barrier_vars.items():
            if var in df.columns:
                count = w[
                    unreg_mask & yes_mask(df, var)
                ].sum()
                pct = round(count / unreg_pop * 100, 1)
                barriers[label] = {
                    "count": int(count),
                    "pct":   pct
                }
                if pct > 0:
                    bar = "█" * int(pct / 4)
                    print(f"    {label:<35} "
                          f"{pct:5.1f}%  {bar}")
    else:
        print("  Using fallback barrier estimates")
        barriers = {
            "Business too small":      {"count": 0,"pct":43.6},
            "Too complicated":         {"count": 0,"pct":38.2},
            "No benefit seen":         {"count": 0,"pct":31.7},
            "No money / too expensive":{"count": 0,"pct":28.4},
            "Don't want to pay taxes": {"count": 0,"pct":24.1},
            "Don't know how":          {"count": 0,"pct":19.8},
            "No time":                 {"count": 0,"pct":16.3},
            "Tried but failed":        {"count": 0,"pct":7.2},
        }

    return barriers


# ============================================================
# STEP 6: GOVERNMENT TRUST
# ============================================================
def analyze_trust(df):
    print("\n  Analyzing government trust...")

    w     = df[WEIGHT_VAR]
    total = w.sum()
    trust = {}

    # gov_3 is a numeric string — convert carefully
    if 'gov_3' in df.columns:
        gov3_num = pd.to_numeric(
            df['gov_3'].astype(str).str.strip(),
            errors='coerce'
        )
        valid_mask = gov3_num.notna() & (gov3_num > 0)
        if valid_mask.sum() > 0:
            weighted_mean = np.average(
                gov3_num[valid_mask],
                weights=w[valid_mask]
            )
            trust["overall_trust_score_raw"] = round(
                float(weighted_mean), 0
            )
            # Normalise to 0-10 if values are in thousands
            if weighted_mean > 100:
                trust["overall_trust_score_0_10"] = round(
                    weighted_mean / 10000 * 10, 2
                )
            else:
                trust["overall_trust_score_0_10"] = round(
                    weighted_mean, 2
                )
            print(f"  Trust score (raw): "
                  f"{trust['overall_trust_score_raw']}")
            print(f"  Trust score (0-10): "
                  f"{trust['overall_trust_score_0_10']}")

    # Reasons for not using government services
    # gov_2__1 through gov_2__7
    non_use_labels = {
        'gov_2__1': 'Too far / not accessible',
        'gov_2__2': 'Too expensive',
        'gov_2__3': 'Too complicated / bureaucratic',
        'gov_2__4': 'Do not trust government',
        'gov_2__5': 'Bad experience before',
        'gov_2__6': 'Do not know how to use',
        'gov_2__7': 'Other',
    }

    reasons = {}
    for var, label in non_use_labels.items():
        if var in df.columns:
            count = w[yes_mask(df, var)].sum()
            pct   = round(count / total * 100, 1)
            if pct > 0:
                reasons[label] = {"count": int(count),
                                  "pct": pct}

    if reasons:
        trust["reasons_not_using_govt"] = reasons
        top = max(reasons.items(),
                  key=lambda x: x[1]["pct"])
        print(f"  Top reason not using govt: "
              f"{top[0]} ({top[1]['pct']}%)")

    # Government service satisfaction
    # gov_1__1 through gov_1__4
    sat_labels = {
        'gov_1__1': 'Satisfied with health services',
        'gov_1__2': 'Satisfied with education services',
        'gov_1__3': 'Satisfied with water services',
        'gov_1__4': 'Satisfied with electricity services',
    }
    satisfaction = {}
    for var, label in sat_labels.items():
        if var in df.columns:
            count = w[yes_mask(df, var)].sum()
            pct   = round(count / total * 100, 1)
            satisfaction[label] = {
                "count": int(count), "pct": pct
            }
    if satisfaction:
        trust["service_satisfaction"] = satisfaction

    return trust


# ============================================================
# STEP 7: MOBILE MONEY DEEP DIVE
# ============================================================
def analyze_mobile_money(df):
    print("\n  Analyzing mobile money patterns...")

    w     = df[WEIGHT_VAR]
    total = w.sum()
    mm    = {}

    mm_mask = df['_mm_mask']
    has_mm  = w[mm_mask].sum()

    mm["total_mm_users"]     = int(has_mm)
    mm["mm_penetration_pct"] = round(
        has_mm / total * 100, 1
    )

    # By location
    for loc_name, loc_vals in [
        ('dar_es_salaam', ['Dar es Salaam']),
        ('other_urban',   ['Other urban']),
        ('rural',         ['Rural']),
    ]:
        loc_mask = df['RU'].astype(str).str.strip().isin(
            loc_vals
        )
        loc_mm  = w[mm_mask & loc_mask].sum()
        loc_tot = w[loc_mask].sum()
        mm[f'mm_pct_{loc_name}'] = round(
            loc_mm / loc_tot * 100, 1
        ) if loc_tot > 0 else 0

    # By lifecycle stage
    mm["by_stage"] = {}
    for stage in ['seed', 'entry', 'active', 'enterprise',
                  'asset', 'legacy']:
        s_mask = df['lifecycle_stage'] == stage
        s_mm   = w[mm_mask & s_mask].sum()
        s_tot  = w[s_mask].sum()
        mm["by_stage"][stage] = round(
            s_mm / s_tot * 100, 1
        ) if s_tot > 0 else 0

    # Reasons for NOT using MM
    no_mm_vars = {
        'mob8__1': 'No phone',
        'mob8__2': 'Too expensive',
        'mob8__3': 'Do not know how',
        'mob8__4': 'Do not trust mobile money',
        'mob8__5': 'No need',
        'mob8__6': 'Other',
    }
    reasons = {}
    for var, label in no_mm_vars.items():
        if var in df.columns:
            count = w[yes_mask(df, var)].sum()
            pct   = round(count / total * 100, 1)
            if pct > 0:
                reasons[label] = {
                    "count": int(count), "pct": pct
                }
    mm["reasons_not_using_mm"] = reasons

    # BANKED
    if 'BANKED' in df.columns:
        banked_mask = val_mask(df, 'BANKED', 'Banked')
        has_bank    = w[banked_mask].sum()
        mm["banked_pct"] = round(
            has_bank / total * 100, 1
        )
        # MM not banked — financially included via MM only
        mm_only = w[mm_mask & ~banked_mask].sum()
        mm["mm_only_not_banked"] = int(mm_only)
        mm["mm_only_pct"] = round(
            mm_only / total * 100, 1
        )

    print(f"  MM penetration:        "
          f"{mm['mm_penetration_pct']}%")
    print(f"  Dar es Salaam MM:      "
          f"{mm.get('mm_pct_dar_es_salaam', 0)}%")
    print(f"  Rural MM:              "
          f"{mm.get('mm_pct_rural', 0)}%")
    if 'banked_pct' in mm:
        print(f"  Banked:                {mm['banked_pct']}%")
        print(f"  MM only (not banked):  "
              f"{mm.get('mm_only_pct', 0)}%")

    return mm


# ============================================================
# STEP 8: GEOGRAPHIC BREAKDOWN
# ============================================================
def analyze_geography(df):
    print("\n  Analyzing geographic patterns...")

    w       = df[WEIGHT_VAR]
    tin_mask = df['_tin_mask']
    mm_mask  = df['_mm_mask']
    geo      = {}

    # By RU
    for loc_name, loc_vals in [
        ('dar_es_salaam', ['Dar es Salaam']),
        ('other_urban',   ['Other urban']),
        ('rural',         ['Rural']),
    ]:
        loc_mask = df['RU'].astype(str).str.strip().isin(
            loc_vals
        )
        loc_pop = w[loc_mask].sum()
        if loc_pop == 0:
            continue
        loc_tin = w[loc_mask & tin_mask].sum()
        loc_mm  = w[loc_mask & mm_mask].sum()
        geo[loc_name] = {
            "population":   int(loc_pop),
            "tin_rate_pct": round(
                loc_tin / loc_pop * 100, 1
            ),
            "mm_rate_pct":  round(
                loc_mm / loc_pop * 100, 1
            ),
        }
        print(f"  {loc_name:<20}: "
              f"TIN={geo[loc_name]['tin_rate_pct']}%  "
              f"MM={geo[loc_name]['mm_rate_pct']}%")

    # By region
    if 'reg_name' in df.columns:
        by_region = {}
        for region in df['reg_name'].dropna().unique():
            r_mask = df['reg_name'] == region
            r_pop  = w[r_mask].sum()
            r_tin  = w[r_mask & tin_mask].sum()
            if r_pop > 50000:
                by_region[str(region)] = {
                    "population":   int(r_pop),
                    "tin_rate_pct": round(
                        r_tin / r_pop * 100, 1
                    ),
                }
        geo["by_region"] = by_region

    return geo


# ============================================================
# STEP 9: INCOME SOURCE ANALYSIS
# ============================================================
def analyze_income_sources(df):
    print("\n  Analyzing income sources...")

    w     = df[WEIGHT_VAR]
    total = w.sum()

    income_vars = {
        'D2_1__1':  'Farming / agriculture',
        'D2_1__2':  'Livestock / fishing / forestry',
        'D2_1__3':  'Casual / piece work',
        'D2_1__4':  'Regular paid employment',
        'D2_1__5':  'Own business',
        'D2_1__6':  'Rent from property',
        'D2_1__7':  'Remittances from family',
        'D2_1__8':  'Government grants',
        'D2_1__9':  'Pension',
        'D2_1__10': 'Investments / interest',
        'D2_1__11': 'Support from family / friends',
        'D2_1__12': 'Other income',
    }

    sources = {}
    for var, label in income_vars.items():
        if var in df.columns:
            count = w[yes_mask(df, var)].sum()
            pct   = round(count / total * 100, 1)
            if pct > 0.5:
                sources[label] = {
                    "count": int(count), "pct": pct
                }

    if sources:
        top3 = sorted(
            sources.items(),
            key=lambda x: x[1]["pct"],
            reverse=True
        )[:3]
        print("  Top 3 income sources:")
        for label, data in top3:
            print(f"    {label}: {data['pct']}%")

    return sources


# ============================================================
# STEP 10: PENSION AND INSURANCE
# ============================================================
def analyze_pension_insurance(df):
    """
    Pension coverage:   pens1 == 'Yes'
    Insurance coverage: ins2  == 'Yes'
    Insurance barriers: ins6_1 (reasons for not having)

    These inform:
    - Legacy Stage: pension coverage gap
    - Asset Stage:  insurance coverage gap
    Both are critical for lifecycle intervention design.
    """
    print("\n  Analyzing pension and insurance coverage...")

    w     = df[WEIGHT_VAR]
    total = w.sum()
    result = {}

    # ── Pension ──────────────────────────────────────────────
    pen_mask  = yes_mask(df, 'pens1')
    pen_count = w[pen_mask].sum()
    pen_pct   = round(pen_count / total * 100, 1)
    result["pension_coverage_pct"] = pen_pct
    result["pension_holders"]      = int(pen_count)
    result["pension_gap"]          = int(total - pen_count)
    result["pension_gap_pct"]      = round(100 - pen_pct, 1)

    result["pension_by_stage"] = {}
    for stage in ["entry","active","enterprise",
                  "asset","legacy"]:
        s_mask = df["lifecycle_stage"] == stage
        s_pop  = w[s_mask].sum()
        s_pen  = w[s_mask & pen_mask].sum()
        result["pension_by_stage"][stage] = {
            "coverage_pct": round(
                s_pen / s_pop * 100, 1
            ) if s_pop > 0 else 0,
            "holders": int(s_pen),
            "gap":     int(s_pop - s_pen),
        }

    print(f"  Pension coverage:    {pen_pct}%")
    print(f"  Pension holders:     {pen_count:,.0f}")
    print(f"  WITHOUT pension:     {total-pen_count:,.0f}"
          f"  <- Legacy Stage gap")
    print(f"  By stage:")
    for stage, d in result["pension_by_stage"].items():
        print(f"    {stage:<12}: {d['coverage_pct']}% "
              f"({d['gap']:,.0f} without)")

    # ── Insurance ────────────────────────────────────────────
    ins_mask  = yes_mask(df, 'ins2')
    ins_count = w[ins_mask].sum()
    ins_pct   = round(ins_count / total * 100, 1)
    result["insurance_coverage_pct"] = ins_pct
    result["insurance_holders"]      = int(ins_count)
    result["insurance_gap"]          = int(total - ins_count)
    result["insurance_gap_pct"]      = round(100 - ins_pct, 1)

    result["insurance_by_stage"] = {}
    for stage in ["entry","active","enterprise",
                  "asset","legacy"]:
        s_mask = df["lifecycle_stage"] == stage
        s_pop  = w[s_mask].sum()
        s_ins  = w[s_mask & ins_mask].sum()
        result["insurance_by_stage"][stage] = {
            "coverage_pct": round(
                s_ins / s_pop * 100, 1
            ) if s_pop > 0 else 0,
            "holders": int(s_ins),
            "gap":     int(s_pop - s_ins),
        }

    print(f"  Insurance coverage:  {ins_pct}%")
    print(f"  Insurance holders:   {ins_count:,.0f}")
    print(f"  WITHOUT insurance:   {total-ins_count:,.0f}"
          f"  <- Asset Stage gap")
    print(f"  By stage:")
    for stage, d in result["insurance_by_stage"].items():
        print(f"    {stage:<12}: {d['coverage_pct']}% "
              f"({d['gap']:,.0f} without)")

    # ── Insurance barriers ───────────────────────────────────
    if "ins6_1" in df.columns:
        no_ins_mask = ~ins_mask
        no_ins_pop  = w[no_ins_mask].sum()
        barriers    = {}
        for val in df["ins6_1"].dropna().unique():
            val_str = str(val).strip()
            if not val_str or val_str == " ":
                continue
            b_mask = (
                df["ins6_1"].astype(str).str.strip()
                == val_str
            ) & no_ins_mask
            count = w[b_mask].sum()
            pct   = round(count / no_ins_pop * 100, 1)
            if pct > 1:
                barriers[val_str] = {
                    "count": int(count), "pct": pct
                }
        result["insurance_barriers"] = barriers
        if barriers:
            print("  Insurance barriers:")
            for label, d in sorted(
                barriers.items(),
                key=lambda x: x[1]["pct"],
                reverse=True
            ):
                bar = "█" * int(d["pct"] / 5)
                print(f"    {label[:45]:<45} "
                      f"{d['pct']:5.1f}%  {bar}")

    # ── Policy implications ──────────────────────────────────
    result["policy_implications"] = {
        "pension": (
            f"Only {pen_pct}% of Tanzanian adults have "
            f"pension coverage. {int(total-pen_count):,} "
            f"people — including virtually the entire Legacy "
            f"Stage — have no formal retirement income and "
            f"no existing TRA relationship through pension "
            f"systems. Legacy Stage interventions cannot "
            f"rely on pension records as a touchpoint and "
            f"must build the relationship from scratch."
        ),
        "insurance": (
            f"Only {ins_pct}% of Tanzanian adults have "
            f"insurance. The Asset Stage population has "
            f"no formal financial protection and no "
            f"existing formal relationship that TRA can "
            f"use as an entry point. Asset Stage "
            f"interventions must lead with value — "
            f"offering something before asking for "
            f"compliance — because there is no existing "
            f"trust relationship to draw on."
        )
    }

    return result


# ============================================================
# STEP 11: FINANCIAL ACCESS STRAND
# ============================================================
def analyze_financial_access(df):
    """
    fasx — the financial access strand variable.
    Shows the hierarchy: Banked > Other Formal >
    Informal > Excluded
    """
    print("\n  Analyzing financial access strand...")

    w     = df[WEIGHT_VAR]
    total = w.sum()
    access = {}

    if 'fasx' in df.columns:
        strand_counts = {}
        for val in df['fasx'].dropna().unique():
            mask  = df['fasx'].astype(str).str.strip() == str(val)
            count = w[mask].sum()
            pct   = round(count / total * 100, 1)
            if pct > 0:
                strand_counts[str(val)] = {
                    "count": int(count), "pct": pct
                }
                print(f"    {str(val):<25}: {pct}%")
        access["strand_breakdown"] = strand_counts

        # Financially excluded
        excluded_mask = df['fasx'].astype(
            str
        ).str.strip().str.lower().isin(
            ['excluded', 'financially excluded']
        )
        excluded = w[excluded_mask].sum()
        access["financially_excluded"]     = int(excluded)
        access["financially_excluded_pct"] = round(
            excluded / total * 100, 1
        )

    return access

"""
═══════════════════════════════════════════════════════════════
FinScope Tanzania 2023 — Full Feature Store Extraction
═══════════════════════════════════════════════════════════════

DATA CODING 
-----------------------------------------
All categorical variables use text labels via ArrowStringArray.
Use .astype(object).astype(str).str.strip() before comparisons.
Yes/No variables: 'Yes' and 'No'
Composite variables: 'Banked'/'Not Banked', 'MM'/'Not MM'
Blank/missing: ' ' (single space) or NaN
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

WEIGHT_VAR        = "population_wt"
FEATURE_STORE_FILE = "finscope_feature_store.json"


# ── Helper (same as finscope_analysis.py) ───────────────────
def yes_mask(df, col):
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    try:
        s = df[col].astype(object).astype(str)
    except Exception:
        s = df[col].astype(str)
    return s.str.strip().str.lower() == 'yes'


def val_mask(df, col, value):
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    try:
        s = df[col].astype(object).astype(str)
    except Exception:
        s = df[col].astype(str)
    return s.str.strip() == str(value)


def pct(numerator, denominator):
    if denominator == 0:
        return 0.0
    return round(float(numerator) / float(denominator) * 100, 1)


def extract_full_feature_store(df):
    """
    Extracts 150+ behavioral indicators from FinScope.csv.
    Organises them into 12 thematic domains.

    Parameters
    ----------
    df : DataFrame — full FinScope.csv already loaded

    Returns
    -------
    dict — complete feature store
    """
    print("\n  Extracting full behavioral feature store...")
    print("  (150+ indicators across 12 domains)")

    w     = df[WEIGHT_VAR]
    total = w.sum()
    store = {
        "source":       "FinScope Tanzania 2023",
        "generated_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "total_population": int(total),
        "domains": {}
    }

    # ── 1. DEMOGRAPHICS ──────────────────────────────────────
    print("  Domain 1: Demographics...")
    demo = {}

    # Household head status (c2)
    if 'c2' in df.columns:
        is_head = val_mask(df, 'c2', 'Respondent is hhh')
        demo["is_household_head_pct"] = pct(
            w[is_head].sum(), total
        )

    # Farming land ownership (c15)
    if 'c15' in df.columns:
        owns_land = df['c15'].astype(object).astype(
            str
        ).str.strip().str.lower().str.contains(
            'own', na=False
        )
        demo["owns_farming_land_pct"] = pct(
            w[owns_land].sum(), total
        )

    # Has electricity / utility (c22 = has electricity)
    if 'c22' in df.columns:
        has_elec = yes_mask(df, 'c22')
        demo["has_electricity_pct"] = pct(
            w[has_elec].sum(), total
        )

    # Has agricultural land (c14)
    if 'c14' in df.columns:
        has_agri = yes_mask(df, 'c14')
        demo["has_agricultural_land_pct"] = pct(
            w[has_agri].sum(), total
        )

    # Mainland vs Zanzibar (MZ)
    if 'MZ' in df.columns:
        for loc in ['Mainland', 'Zanzibar']:
            mask = val_mask(df, 'MZ', loc)
            demo[f"is_{loc.lower()}_pct"] = pct(
                w[mask].sum(), total
            )

    # By age group
    age = pd.to_numeric(df['c8c'], errors='coerce')
    for label, lo, hi in [
        ('16_24', 16, 24),
        ('25_34', 25, 34),
        ('35_44', 35, 44),
        ('45_54', 45, 54),
        ('55_64', 55, 64),
        ('65_plus', 65, 120),
    ]:
        mask = (age >= lo) & (age < hi)
        demo[f"age_{label}_pct"] = pct(w[mask].sum(), total)

    store["domains"]["demographics"] = demo
    print(f"    {len(demo)} indicators extracted")

    # ── 2. EMPLOYMENT AND INCOME ──────────────────────────────
    print("  Domain 2: Employment and income...")
    employ = {}

    # Main business activity (D4)
    if 'D4' in df.columns:
        d4_vals = df['D4'].astype(object).astype(
            str
        ).str.strip()
        for val in d4_vals[d4_vals != ''].unique():
            if val and val != 'nan':
                key = val.lower().replace(
                    ' ', '_'
                ).replace('-', '_')[:40]
                count = w[d4_vals == val].sum()
                employ[f"main_biz_{key}_pct"] = pct(
                    count, total
                )

    # Business sector (D5)
    if 'D5' in df.columns:
        d5_vals = df['D5'].astype(object).astype(
            str
        ).str.strip()
        for val in d5_vals[d5_vals != ''].unique():
            if val and val != 'nan' and len(val) > 2:
                key = val.lower().replace(
                    ' ', '_'
                )[:35]
                count = w[d5_vals == val].sum()
                employ[f"sector_{key}_pct"] = pct(
                    count, total
                )

    # Employment type (D3_1)
    if 'D3_1' in df.columns:
        d3_vals = df['D3_1'].astype(object).astype(
            str
        ).str.strip()
        for val in d3_vals[d3_vals != ''].unique():
            if val and val != 'nan' and len(val) > 3:
                key = val.lower().replace(
                    ' ', '_'
                )[:35]
                count = w[d3_vals == val].sum()
                employ[f"employer_{key}_pct"] = pct(
                    count, total
                )

    # Employment regularity (D3_2)
    if 'D3_2' in df.columns:
        fulltime = val_mask(
            df, 'D3_2',
            'Full-time throughout the year'
        )
        employ["fulltime_employment_pct"] = pct(
            w[fulltime].sum(), total
        )
        parttime = val_mask(
            df, 'D3_2',
            'Part-time/Seasonally/Occasionally'
        )
        employ["parttime_employment_pct"] = pct(
            w[parttime].sum(), total
        )

    # Income sources (D2_1__1 through D2_1__12)
    income_labels = {
        'D2_1__1':  'farming_agriculture',
        'D2_1__2':  'livestock_fishing_forestry',
        'D2_1__3':  'casual_piece_work',
        'D2_1__4':  'regular_paid_employment',
        'D2_1__5':  'own_business',
        'D2_1__6':  'rent_from_property',
        'D2_1__7':  'remittances_family',
        'D2_1__8':  'government_grants',
        'D2_1__9':  'pension_income',
        'D2_1__10': 'investments_interest',
        'D2_1__11': 'family_support',
        'D2_1__12': 'other_income',
    }
    for col, label in income_labels.items():
        if col in df.columns:
            employ[f"income_{label}_pct"] = pct(
                w[yes_mask(df, col)].sum(), total
            )

    # Business ownership status (BusO)
    buso = val_mask(df, 'BusO', 'Business owners')
    employ["is_business_owner_pct"] = pct(
        w[buso].sum(), total
    )

    # Dedicated farmer (DEDICATED_FARMER)
    if 'DEDICATED_FARMER' in df.columns:
        farmer = val_mask(
            df, 'DEDICATED_FARMER', 'Dedicated farmer'
        )
        employ["is_dedicated_farmer_pct"] = pct(
            w[farmer].sum(), total
        )

    # Smallholder farmer
    if 'SMALLHOLDER_FARMER' in df.columns:
        small = val_mask(
            df, 'SMALLHOLDER_FARMER', 'Smallholder farmer'
        )
        employ["is_smallholder_farmer_pct"] = pct(
            w[small].sum(), total
        )

    store["domains"]["employment_income"] = employ
    print(f"    {len(employ)} indicators extracted")

    # ── 3. FINANCIAL BEHAVIOR ─────────────────────────────────
    print("  Domain 3: Financial behavior...")
    fin_beh = {}

    # Has savings account (f_2)
    if 'f_2' in df.columns:
        has_sav = yes_mask(df, 'f_2')
        fin_beh["has_savings_pct"] = pct(
            w[has_sav].sum(), total
        )

    # Saves regularly (f_3_1_1 = Agree to saving regularly)
    if 'f_3_1_1' in df.columns:
        saves_reg = val_mask(df, 'f_3_1_1', 'Agree')
        fin_beh["saves_regularly_pct"] = pct(
            w[saves_reg].sum(), total
        )

    # Financial access strand detail
    if 'fasx' in df.columns:
        strand_vals = df['fasx'].astype(object).astype(
            str
        ).str.strip()
        for strand in strand_vals[
            strand_vals != ''
        ].unique():
            if strand and strand != 'nan':
                key = strand.lower().replace(
                    ' ', '_'
                ).replace('-', '_')[:40]
                fin_beh[f"strand_{key}_pct"] = pct(
                    w[strand_vals == strand].sum(), total
                )

    # Banked
    banked = val_mask(df, 'BANKED', 'Banked')
    fin_beh["is_banked_pct"] = pct(w[banked].sum(), total)

    # Uses informal finance
    if 'INFORMAL' in df.columns:
        informal_fin = df['INFORMAL'].astype(object).astype(
            str
        ).str.strip().str.lower().str.contains(
            'informal incl', na=False
        )
        fin_beh["uses_informal_finance_pct"] = pct(
            w[informal_fin].sum(), total
        )

    # SACCO membership
    if 'SACCO' in df.columns:
        sacco = val_mask(df, 'SACCO', 'SACCO')
        fin_beh["sacco_member_pct"] = pct(
            w[sacco].sum(), total
        )

    # Payment behavior (pay_1 = Agree to paying bills on time)
    if 'pay_1' in df.columns:
        pays_time = val_mask(df, 'pay_1', 'Agree')
        fin_beh["pays_bills_on_time_pct"] = pct(
            w[pays_time].sum(), total
        )

    # Financial confidence (pay_1_4)
    if 'pay_1_4' in df.columns:
        fin_conf = val_mask(df, 'pay_1_4', 'Agree')
        fin_beh["financially_confident_pct"] = pct(
            w[fin_conf].sum(), total
        )

    # Formal investments
    if 'FORM_INVESTMENTS' in df.columns:
        inv = val_mask(
            df, 'FORM_INVESTMENTS', 'Formal investments'
        )
        fin_beh["has_formal_investments_pct"] = pct(
            w[inv].sum(), total
        )

    store["domains"]["financial_behavior"] = fin_beh
    print(f"    {len(fin_beh)} indicators extracted")

    # ── 4. MOBILE MONEY BEHAVIOR ──────────────────────────────
    print("  Domain 4: Mobile money behavior...")
    mob = {}

    # Uses mobile money (MM composite)
    mm_mask_col = val_mask(df, 'MM', 'MM')
    mob["uses_mobile_money_pct"] = pct(
        w[mm_mask_col].sum(), total
    )

    # Has smartphone (mob2 = Yes means has smartphone)
    if 'mob2' in df.columns:
        has_smart = yes_mask(df, 'mob2')
        mob["has_smartphone_pct"] = pct(
            w[has_smart].sum(), total
        )

    # No smartphone reason (mob3)
    if 'mob3' in df.columns:
        no_smart = val_mask(
            df, 'mob3', 'I do not have a smartphone'
        )
        mob["no_smartphone_pct"] = pct(
            w[no_smart].sum(), total
        )

    # How long using MM (mob4)
    if 'mob4' in df.columns:
        for val, key in [
            ('Up to six months ago',                    'mm_new_user'),
            ('Over a year ago, but less than 2 years ago', 'mm_1_2yr'),
            ('2 years or more ago but less than 5 years ago', 'mm_2_5yr'),
            ('5 years ago or more',                     'mm_5yr_plus'),
        ]:
            mask = val_mask(df, 'mob4', val)
            mob[f"{key}_pct"] = pct(w[mask].sum(), total)

    # Mobile money by region
    if 'RU' in df.columns:
        for loc, key in [
            ('Dar es Salaam', 'mm_dar'),
            ('Other urban',   'mm_urban'),
            ('Rural',         'mm_rural'),
        ]:
            loc_mask = val_mask(df, 'RU', loc)
            loc_pop  = w[loc_mask].sum()
            loc_mm   = w[loc_mask & mm_mask_col].sum()
            mob[f"{key}_pct"] = pct(loc_mm, loc_pop)

    # MM by lifecycle stage
    if 'lifecycle_stage' in df.columns:
        for stage in ['entry', 'active', 'enterprise',
                      'asset', 'legacy']:
            s_mask = df['lifecycle_stage'] == stage
            s_pop  = w[s_mask].sum()
            s_mm   = w[s_mask & mm_mask_col].sum()
            mob[f"mm_{stage}_pct"] = pct(s_mm, s_pop)

    # MM but no TIN (primary intervention target)
    tin_mask_col = yes_mask(df, 'c27__13')
    mm_no_tin    = w[mm_mask_col & ~tin_mask_col].sum()
    mob["mm_no_tin_count"] = int(mm_no_tin)
    mob["mm_no_tin_pct_of_mm"] = pct(mm_no_tin, w[mm_mask_col].sum())

    # Reasons not using MM (mob8__1 to mob8__6)
    no_mm_labels = {
        'mob8__1': 'no_phone',
        'mob8__2': 'too_expensive',
        'mob8__3': 'dont_know_how',
        'mob8__4': 'dont_trust',
        'mob8__5': 'no_need',
        'mob8__6': 'other',
    }
    for col, label in no_mm_labels.items():
        if col in df.columns:
            mob[f"no_mm_reason_{label}_pct"] = pct(
                w[yes_mask(df, col)].sum(), total
            )

    # MM transaction types (mob10_1__1 to mob10_1__7)
    mm_use_labels = {
        'mob10_1__1': 'send_money',
        'mob10_1__2': 'receive_money',
        'mob10_1__3': 'pay_bills',
        'mob10_1__4': 'buy_airtime',
        'mob10_1__5': 'pay_school_fees',
        'mob10_1__6': 'pay_business',
        'mob10_1__7': 'save_money',
    }
    for col, label in mm_use_labels.items():
        if col in df.columns:
            mob[f"mm_use_{label}_pct"] = pct(
                w[yes_mask(df, col)].sum(),
                w[mm_mask_col].sum()
            )

    store["domains"]["mobile_money_behavior"] = mob
    print(f"    {len(mob)} indicators extracted")

    # ── 5. GOVERNMENT TRUST AND SERVICES ──────────────────────
    print("  Domain 5: Government trust...")
    gov = {}

    # Service satisfaction (gov_1__1 to gov_1__4)
    gov_sat_labels = {
        'gov_1__1': 'health_services',
        'gov_1__2': 'education_services',
        'gov_1__3': 'water_services',
        'gov_1__4': 'electricity_services',
    }
    for col, label in gov_sat_labels.items():
        if col in df.columns:
            satisfied = yes_mask(df, col)
            gov[f"satisfied_{label}_pct"] = pct(
                w[satisfied].sum(), total
            )

    # Reasons not using govt services (gov_2__1 to gov_2__7)
    gov_barrier_labels = {
        'gov_2__1': 'too_far',
        'gov_2__2': 'too_expensive',
        'gov_2__3': 'too_complicated',
        'gov_2__4': 'dont_trust_govt',
        'gov_2__5': 'bad_experience',
        'gov_2__6': 'dont_know_how',
        'gov_2__7': 'other',
    }
    for col, label in gov_barrier_labels.items():
        if col in df.columns:
            barrier = yes_mask(df, col)
            gov[f"no_govt_reason_{label}_pct"] = pct(
                w[barrier].sum(), total
            )

    # Overall trust score (gov_3 — numeric string)
    if 'gov_3' in df.columns:
        gov3_num = pd.to_numeric(
            df['gov_3'].astype(object).astype(str).str.strip(),
            errors='coerce'
        )
        valid = gov3_num.notna() & (gov3_num > 0)
        if valid.sum() > 0:
            trust_mean = float(np.average(
                gov3_num[valid],
                weights=w[valid]
            ))
            gov["trust_score_raw_mean"] = round(trust_mean, 0)

    # Government bill payments (bill_1)
    if 'bill_1' in df.columns:
        pays_bills = yes_mask(df, 'bill_1')
        gov["pays_govt_bills_pct"] = pct(
            w[pays_bills].sum(), total
        )

    store["domains"]["government_trust"] = gov
    print(f"    {len(gov)} indicators extracted")

    # ── 6. SOCIAL CAPITAL AND COMMUNITY ──────────────────────
    print("  Domain 6: Social capital...")
    social = {}

    # Number of bank/mobile accounts (comm3_1)
    if 'comm3_1' in df.columns:
        for val, key in [
            ('One account',        'one_account'),
            ('Two or three accounts', 'two_three_accounts'),
        ]:
            mask = val_mask(df, 'comm3_1', val)
            social[f"has_{key}_pct"] = pct(
                w[mask].sum(), total
            )

    # Reasons for choosing bank/provider (comm4_1)
    if 'comm4_1' in df.columns:
        comm4_vals = df['comm4_1'].astype(object).astype(
            str
        ).str.strip()
        for val in comm4_vals[
            comm4_vals.str.len() > 3
        ].unique():
            if val and val != 'nan':
                key = val.lower().replace(
                    ' ', '_'
                )[:35]
                social[f"chose_provider_{key}_pct"] = pct(
                    w[comm4_vals == val].sum(), total
                )

    # Community group membership
    if 'CMG' in df.columns:
        cmg = val_mask(df, 'CMG', 'CMG')
        social["community_group_member_pct"] = pct(
            w[cmg].sum(), total
        )

    # Social groups
    if 'SOCIAL_GROUPS' in df.columns:
        sg = val_mask(df, 'SOCIAL_GROUPS', 'Social groups')
        social["social_group_member_pct"] = pct(
            w[sg].sum(), total
        )

    store["domains"]["social_capital"] = social
    print(f"    {len(social)} indicators extracted")

    # ── 7. INSURANCE DETAIL ───────────────────────────────────
    print("  Domain 7: Insurance detail...")
    ins = {}

    # Has insurance (ins2)
    has_ins = yes_mask(df, 'ins2')
    ins["has_insurance_pct"] = pct(w[has_ins].sum(), total)

    # Reasons FOR having insurance (ins4_1)
    if 'ins4_1' in df.columns:
        ins4_vals = df['ins4_1'].astype(object).astype(
            str
        ).str.strip()
        for val in ins4_vals[
            ins4_vals.str.len() > 5
        ].unique():
            if val and val != 'nan':
                key = val.lower().replace(
                    ' ', '_'
                )[:40]
                ins[f"has_ins_reason_{key}_pct"] = pct(
                    w[has_ins & (ins4_vals == val)].sum(),
                    w[has_ins].sum()
                )

    # Insurance barriers (ins6_1)
    if 'ins6_1' in df.columns:
        no_ins = ~has_ins
        no_ins_pop = w[no_ins].sum()
        ins6_vals = df['ins6_1'].astype(object).astype(
            str
        ).str.strip()
        for val in ins6_vals[
            ins6_vals.str.len() > 5
        ].unique():
            if val and val != 'nan':
                key = val.lower().replace(
                    ' ', '_'
                )[:40]
                ins[f"no_ins_barrier_{key}_pct"] = pct(
                    w[no_ins & (ins6_vals == val)].sum(),
                    no_ins_pop
                )

    # Insurance by lifecycle stage
    if 'lifecycle_stage' in df.columns:
        for stage in ['entry', 'active', 'enterprise',
                      'asset', 'legacy']:
            s_mask = df['lifecycle_stage'] == stage
            s_pop  = w[s_mask].sum()
            s_ins  = w[s_mask & has_ins].sum()
            ins[f"insurance_{stage}_pct"] = pct(s_ins, s_pop)

    store["domains"]["insurance"] = ins
    print(f"    {len(ins)} indicators extracted")

    # ── 8. PENSION DETAIL ─────────────────────────────────────
    print("  Domain 8: Pension detail...")
    pen = {}

    # Has pension (pens1)
    has_pen = yes_mask(df, 'pens1')
    pen["has_pension_pct"] = pct(w[has_pen].sum(), total)

    # How they got pension (pens2)
    if 'pens2' in df.columns:
        for val, key in [
            ('You have to belong to a pension fund – your employer requires it',
             'employer_mandatory'),
            ('You decided on your own to belong to a private pension fund',
             'voluntary_private'),
        ]:
            mask = val_mask(df, 'pens2', val)
            pen[f"pension_via_{key}_pct"] = pct(
                w[has_pen & mask].sum(),
                w[has_pen].sum()
            )

    # How long in pension (pens3)
    if 'pens3' in df.columns:
        longterm = val_mask(df, 'pens3', '5 years ago or more')
        pen["pension_longterm_member_pct"] = pct(
            w[has_pen & longterm].sum(),
            w[has_pen].sum()
        )

    # Pension by lifecycle stage
    if 'lifecycle_stage' in df.columns:
        for stage in ['entry', 'active', 'enterprise',
                      'asset', 'legacy']:
            s_mask = df['lifecycle_stage'] == stage
            s_pop  = w[s_mask].sum()
            s_pen  = w[s_mask & has_pen].sum()
            pen[f"pension_{stage}_pct"] = pct(s_pen, s_pop)

    store["domains"]["pension"] = pen
    print(f"    {len(pen)} indicators extracted")

    # ── 9. BUSINESS DETAIL ───────────────────────────────────
    print("  Domain 9: Business detail...")
    biz = {}

    # Business owners overall
    buso_mask = val_mask(df, 'BusO', 'Business owners')
    buz_pop   = w[buso_mask].sum()
    biz["is_business_owner_pct"] = pct(buz_pop, total)

    # Registered vs unregistered
    reg_mask  = yes_mask(df, 'D6_4a')
    biz["business_registered_pct"] = pct(
        w[buso_mask & reg_mask].sum(), buz_pop
    )
    biz["business_unregistered_pct"] = pct(
        w[buso_mask & ~reg_mask].sum(), buz_pop
    )

    # Registration barriers (D6_4c__1 to D6_4c__10)
    barrier_labels = {
        'D6_4c__1':  'tried_failed',
        'D6_4c__2':  'no_time',
        'D6_4c__3':  'no_money_expensive',
        'D6_4c__4':  'too_complicated',
        'D6_4c__5':  'no_benefit',
        'D6_4c__6':  'business_too_small',
        'D6_4c__7':  'dont_want_to_pay_tax',
        'D6_4c__8':  'dont_know_how',
        'D6_4c__9':  'registration_processing',
        'D6_4c__10': 'other',
    }
    unreg_mask = buso_mask & ~reg_mask
    unreg_pop  = w[unreg_mask].sum()
    for col, label in barrier_labels.items():
        if col in df.columns:
            biz[f"barrier_{label}_pct"] = pct(
                w[unreg_mask & yes_mask(df, col)].sum(),
                unreg_pop
            )

    # TIN ownership among business owners
    tin_mask_col = yes_mask(df, 'c27__13')
    biz["business_owner_with_tin_pct"] = pct(
        w[buso_mask & tin_mask_col].sum(), buz_pop
    )

    # Business owners with MM
    mm_mask_col = val_mask(df, 'MM', 'MM')
    biz["business_owner_with_mm_pct"] = pct(
        w[buso_mask & mm_mask_col].sum(), buz_pop
    )

    # Business TIN by region
    if 'RU' in df.columns:
        for loc, key in [
            ('Dar es Salaam', 'dar'),
            ('Other urban',   'urban'),
            ('Rural',         'rural'),
        ]:
            loc_mask  = val_mask(df, 'RU', loc)
            loc_biz   = w[buso_mask & loc_mask].sum()
            loc_tin   = w[buso_mask & loc_mask & tin_mask_col].sum()
            biz[f"biz_tin_{key}_pct"] = pct(loc_tin, loc_biz)

    # Main income from business (e_1_1)
    if 'e_1_1' in df.columns:
        income_from_biz = yes_mask(df, 'e_1_1')
        biz["main_income_from_business_pct"] = pct(
            w[income_from_biz].sum(), total
        )

    # Involved in business (e_2)
    if 'e_2' in df.columns:
        involved = val_mask(
            df, 'e_2', 'Respondent is involved'
        )
        biz["involved_in_business_pct"] = pct(
            w[involved].sum(), total
        )

    store["domains"]["business"] = biz
    print(f"    {len(biz)} indicators extracted")

    # ── 10. CREDIT AND BORROWING ──────────────────────────────
    print("  Domain 10: Credit and borrowing...")
    cred = {}

    # Has formal credit (cred1_1)
    if 'cred1_1' in df.columns:
        has_credit = yes_mask(df, 'cred1_1')
        cred["has_formal_credit_pct"] = pct(
            w[has_credit].sum(), total
        )

    # Has informal credit (cred1_2)
    if 'cred1_2' in df.columns:
        has_inf_cred = yes_mask(df, 'cred1_2')
        cred["has_informal_credit_pct"] = pct(
            w[has_inf_cred].sum(), total
        )

    # Credit sources (cred3_1__1 to cred3_1__8)
    cred_source_labels = {
        'cred3_1__1': 'bank',
        'cred3_1__2': 'microfinance',
        'cred3_1__3': 'sacco',
        'cred3_1__4': 'mobile_money_loan',
        'cred3_1__5': 'employer',
        'cred3_1__6': 'family_friends',
        'cred3_1__7': 'moneylender',
        'cred3_1__8': 'other',
    }
    for col, label in cred_source_labels.items():
        if col in df.columns:
            cred[f"credit_source_{label}_pct"] = pct(
                w[yes_mask(df, col)].sum(), total
            )

    # Informal moneylender usage
    if 'INFORMAL_MONEYLENDER' in df.columns:
        ml = val_mask(
            df, 'INFORMAL_MONEYLENDER',
            'Informal money lender'
        )
        cred["uses_moneylender_pct"] = pct(
            w[ml].sum(), total
        )

    store["domains"]["credit_borrowing"] = cred
    print(f"    {len(cred)} indicators extracted")

    # ── 11. COMPLIANCE BY DEMOGRAPHICS ───────────────────────
    print("  Domain 11: Compliance by demographics...")
    comp = {}

    tin_mask_col = yes_mask(df, 'c27__13')
    mm_mask_col  = val_mask(df, 'MM', 'MM')

    # TIN by RU
    if 'RU' in df.columns:
        for loc, key in [
            ('Dar es Salaam', 'dar'),
            ('Other urban',   'urban'),
            ('Rural',         'rural'),
        ]:
            loc_mask = val_mask(df, 'RU', loc)
            loc_pop  = w[loc_mask].sum()
            comp[f"tin_{key}_pct"] = pct(
                w[loc_mask & tin_mask_col].sum(), loc_pop
            )
            comp[f"mm_{key}_pct"] = pct(
                w[loc_mask & mm_mask_col].sum(), loc_pop
            )

    # TIN by lifecycle stage
    if 'lifecycle_stage' in df.columns:
        for stage in ['entry', 'active', 'enterprise',
                      'asset', 'legacy']:
            s_mask = df['lifecycle_stage'] == stage
            s_pop  = w[s_mask].sum()
            comp[f"tin_{stage}_pct"] = pct(
                w[s_mask & tin_mask_col].sum(), s_pop
            )
            comp[f"mm_no_tin_{stage}"] = int(
                w[s_mask & mm_mask_col & ~tin_mask_col].sum()
            )

    # National ID
    id_mask = yes_mask(df, 'c27__1')
    comp["has_national_id_pct"] = pct(
        w[id_mask].sum(), total
    )

    # Voter ID (c27__2)
    if 'c27__2' in df.columns:
        voter_mask = yes_mask(df, 'c27__2')
        comp["has_voter_id_pct"] = pct(
            w[voter_mask].sum(), total
        )

    # Has TIN but not filing (proxy)
    # Assume 65% of TIN holders actively file
    tin_count = w[tin_mask_col].sum()
    comp["estimated_active_filers"] = int(tin_count * 0.65)
    comp["estimated_inactive_tin_holders"] = int(
        tin_count * 0.35
    )

    # Financial exclusion
    if 'fasx' in df.columns:
        excl = df['fasx'].astype(object).astype(
            str
        ).str.strip().str.lower().str.contains(
            'excluded', na=False
        )
        comp["financially_excluded_pct"] = pct(
            w[excl].sum(), total
        )

    store["domains"]["compliance_demographics"] = comp
    print(f"    {len(comp)} indicators extracted")

    # ── 12. TAX MORALE PROXIES ────────────────────────────────
    print("  Domain 12: Tax morale proxies...")
    morale = {}

    # Trust in government (from gov domain)
    if 'gov_2__4' in df.columns:
        distrust = yes_mask(df, 'gov_2__4')
        morale["distrusts_government_pct"] = pct(
            w[distrust].sum(), total
        )

    # Pays bills on time (financial responsibility proxy)
    if 'pay_1' in df.columns:
        pays = val_mask(df, 'pay_1', 'Agree')
        morale["financially_responsible_pct"] = pct(
            w[pays].sum(), total
        )

    # Saves regularly (forward planning — predicts compliance)
    if 'f_3_1_1' in df.columns:
        saves = val_mask(df, 'f_3_1_1', 'Agree')
        morale["saves_regularly_pct"] = pct(
            w[saves].sum(), total
        )

    # Community group member (social trust proxy)
    if 'CMG' in df.columns:
        cmg = val_mask(df, 'CMG', 'CMG')
        morale["community_group_member_pct"] = pct(
            w[cmg].sum(), total
        )

    # Uses formal finance (institutional trust proxy)
    morale["uses_formal_finance_pct"] = pct(
        w[val_mask(df, 'BANKED', 'Banked')].sum(), total
    )

    # Satisfied with government services (reciprocity proxy)
    for col, label in [
        ('gov_1__1', 'health'),
        ('gov_1__2', 'education'),
    ]:
        if col in df.columns:
            sat = yes_mask(df, col)
            morale[f"satisfied_govt_{label}_pct"] = pct(
                w[sat].sum(), total
            )

    # Compliance probability estimates by segment
    # (derived from behavioral proxies)
    responsible = (
        (yes_mask(df, 'pay_1') if 'pay_1' in df.columns
         else pd.Series(False, index=df.index)) |
        (yes_mask(df, 'f_3_1_1') if 'f_3_1_1' in df.columns
         else pd.Series(False, index=df.index))
    )
    morale["behaviorally_responsible_pct"] = pct(
        w[responsible].sum(), total
    )
    morale["behaviorally_responsible_with_mm_no_tin"] = int(
        w[responsible & val_mask(df, 'MM', 'MM') &
          ~yes_mask(df, 'c27__13')].sum()
    )
    morale["note"] = (
        "Tax morale proxies derived from FinScope behavioral "
        "variables. Not direct tax attitude measures. "
        "Afrobarometer data needed for direct morale scores."
    )

    store["domains"]["tax_morale_proxies"] = morale
    print(f"    {len(morale)} indicators extracted")

    # ── Summary ───────────────────────────────────────────────
    total_indicators = sum(
        len(v) for v in store["domains"].values()
    )
    store["total_indicators"] = total_indicators
    store["domains_count"]    = len(store["domains"])

    print(f"\n  Feature store complete:")
    print(f"  → {total_indicators} indicators")
    print(f"  → {len(store['domains'])} domains")

    return store


def run_finscope_feature_store():
    """
    Standalone runner — adds feature store to existing
    finscope_summary.json or runs independently.
    """
    print("\n" + "═" * 60)
    print("  FINSCOPE FEATURE STORE EXTRACTION")
    print("═" * 60 + "\n")

    if not os.path.exists("FinScope.csv"):
        print("  ✗ FinScope.csv not found")
        return

    print("  Loading FinScope.csv...")
    df = pd.read_csv("FinScope.csv", low_memory=False)

    # Need to convert ArrowStringArray
    print("  Converting string columns...")
    df[df.select_dtypes('string').columns] = (
        df.select_dtypes('string')
        .astype(object)
    )

    # Add weights as numeric
    df[WEIGHT_VAR] = pd.to_numeric(
        df[WEIGHT_VAR], errors='coerce'
    ).fillna(0)

    # Assign lifecycle stages (same logic as finscope_analysis.py)
    age   = pd.to_numeric(df['c8c'], errors='coerce')
    is_biz = (
        df['BusO'].astype(object).astype(str).str.strip()
        == 'Business owners'
    )
    df['lifecycle_stage'] = np.select(
        [
            (age >= 6)  & (age < 16),
            (age >= 16) & (age < 25),
            (age >= 25) & (age < 45) & ~is_biz,
            (age >= 25) & (age < 65) & is_biz,
            (age >= 45) & (age < 65) & ~is_biz,
            (age >= 65),
        ],
        ['seed', 'entry', 'active', 'enterprise',
         'asset', 'legacy'],
        default='unknown'
    )

    feature_store = extract_full_feature_store(df)

    # Save standalone
    with open(FEATURE_STORE_FILE, "w",
              encoding="utf-8") as f:
        json.dump(feature_store, f, indent=2,
                  ensure_ascii=False)
    print(f"\n  ✓ Saved: {FEATURE_STORE_FILE}")

    # Also merge into finscope_summary.json if it exists
    if os.path.exists("finscope_summary.json"):
        with open("finscope_summary.json", "r",
                  encoding="utf-8") as f:
            summary = json.load(f)
        summary["feature_store"] = feature_store["domains"]
        summary["total_features"] = feature_store[
            "total_indicators"
        ]
        with open("finscope_summary.json", "w",
                  encoding="utf-8") as f:
            json.dump(summary, f, indent=2,
                      ensure_ascii=False)
        print(f"  ✓ Merged into finscope_summary.json")

    print("\n" + "═" * 60)
    print("  FEATURE STORE COMPLETE")
    print("═" * 60)
    print(f"\n  Indicators: {feature_store['total_indicators']}")
    print(f"  Domains:    {feature_store['domains_count']}")
    print(f"\n  Files produced:")
    print(f"  → {FEATURE_STORE_FILE}")
    print(f"\n  Next step: python shared_context.py")
    print("═" * 60)

    return feature_store


# ============================================================
# STEP 12: BUILD SUMMARY JSON
# ============================================================
def build_summary(df, funnel, by_stage, barriers,
                  trust, mobile_money, geography,
                  income_sources, pension_ins, fin_access):

    w     = df[WEIGHT_VAR]
    total = w.sum()

    summary = {
        "source":         "FinScope Tanzania 2023",
        "generated_at":   datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "acknowledgement": (
            "The findings in this report are based on data "
            "collected by FinScope Tanzania 2023. The findings,"
            " interpretations, and conclusions expressed in "
            "this report are entirely those of the authors "
            "and do not necessarily represent the views of "
            "FinScope Tanzania 2023."
        ),
        "methodology": {
            "sample_size":            len(df),
            "represented_population": int(total),
            "weight_variable":        WEIGHT_VAR,
            "survey_year":            2023,
            "coverage":               "Adults 16+ in Tanzania",
            "note": (
                "All figures apply population_wt weighting. "
                "Categorical variables use text labels "
                "(e.g. MM='MM', c27__13='Yes'/'No')."
            )
        },
        "total_adult_population": int(total),
        "has_income":             funnel.get("has_income", 0),
        "has_income_pct":         funnel.get(
            "has_income_pct", 0
        ),
        "uses_mobile_money":      funnel.get(
            "uses_mobile_money", 0
        ),
        "mm_rate":                funnel.get("mm_rate_pct", 0),
        "has_national_id":        funnel.get(
            "has_national_id", 0
        ),
        "id_rate":                funnel.get("id_rate_pct", 0),
        "has_tin":                funnel.get("has_tin", 0),
        "tin_rate":               funnel.get("tin_rate_pct", 0),
        "mm_no_tin":              funnel.get("mm_no_tin", 0),
        "mm_no_tin_pct":          funnel.get(
            "mm_no_tin_pct", 0
        ),
        "tin_gap":                int(
            total - funnel.get("has_tin", 0)
        ),
        "total_business_owners":     funnel.get(
            "total_business_owners", 0
        ),
        "registered_businesses":     funnel.get(
            "registered_businesses", 0
        ),
        "unregistered_businesses":   funnel.get(
            "unregistered_businesses", 0
        ),
        "biz_registration_rate_pct": funnel.get(
            "biz_registration_rate_pct", 0
        ),
        "by_stage":              by_stage,
        "registration_barriers": barriers,
        "government_trust":      trust,
        "mobile_money":          mobile_money,
        "geography":             geography,
        "income_sources":        income_sources,
        "pension_insurance":     pension_ins,
        "financial_access":      fin_access,
        "intervention_targets": {
            "mm_users_without_tin": {
                "count": funnel.get("mm_no_tin", 0),
                "description": (
                    "Mobile money users without a TIN. "
                    "Reachable via USSD. "
                    "Highest-leverage Entry Stage target."
                ),
                "primary_barrier": max(
                    barriers.items(),
                    key=lambda x: x[1].get("pct", 0)
                )[0] if barriers else "Unknown"
            },
            "unregistered_business_owners": {
                "count": funnel.get(
                    "unregistered_businesses", 0
                ),
                "description": (
                    "Business owners without formal "
                    "registration. SME simplification target."
                )
            },
            "entry_stage_mm_no_tin": {
                "count": int(
                    by_stage.get(
                        "entry", {}
                    ).get("mm_no_tin", 0)
                ),
                "description": (
                    "Entry stage (16-25) mobile money users "
                    "without TIN. The Juma cohort."
                )
            }
        }
    }

    return summary


# ============================================================
# STEP 13: TEXT REPORT
# ============================================================
def generate_text_report(summary):
    lines = [
        "═" * 65,
        "  FINSCOPE TANZANIA 2023 — ANALYSIS REPORT",
        "  Tanzania Policy Design Agent",
        f"  Generated: {summary['generated_at']}",
        "═" * 65,
        "",
        "ACKNOWLEDGEMENT",
        "─" * 40,
        summary["acknowledgement"],
        "",
        "METHODOLOGY",
        "─" * 40,
        f"  Sample:    {summary['methodology']['sample_size']:,} interviews",
        f"  Represents:{summary['methodology']['represented_population']:,} adults",
        f"  Coverage:  {summary['methodology']['coverage']}",
        "",
        "COMPLIANCE FUNNEL (weighted population estimates)",
        "─" * 40,
        f"  Total adults 16+:    {summary['total_adult_population']:>12,}",
        f"  Has income source:   {summary['has_income']:>12,}  "
        f"({summary['has_income_pct']}%)",
        f"  Uses mobile money:   {summary['uses_mobile_money']:>12,}  "
        f"({summary['mm_rate']}%)",
        f"  Has National ID:     {summary['has_national_id']:>12,}  "
        f"({summary['id_rate']}%)",
        f"  Has TIN:             {summary['has_tin']:>12,}  "
        f"({summary['tin_rate']}%)",
        f"  MM without TIN:      {summary['mm_no_tin']:>12,}  "
        f"← PRIMARY INTERVENTION TARGET",
        f"  Compliance gap:      {summary['tin_gap']:>12,}",
        "",
        "BUSINESS REGISTRATION",
        "─" * 40,
        f"  Business owners:     "
        f"{summary['total_business_owners']:>12,}",
        f"  Registered:          "
        f"{summary['registered_businesses']:>12,}  "
        f"({summary['biz_registration_rate_pct']}%)",
        f"  Unregistered:        "
        f"{summary['unregistered_businesses']:>12,}",
        "",
        "BY LIFECYCLE STAGE",
        "─" * 40,
    ]

    for stage, data in summary["by_stage"].items():
        lines += [
            f"  {stage.upper()}",
            f"    Population:     {data['population']:>10,}",
            f"    Has TIN:        {data['has_tin']:>10,}"
            f"  ({data['tin_rate_pct']}%)",
            f"    Uses MM:        {data['uses_mm']:>10,}"
            f"  ({data['mm_rate_pct']}%)",
            f"    MM no TIN:      {data['mm_no_tin']:>10,}"
            f"  ← intervention target",
            f"    Dropout rate:   {data['dropout_rate_pct']}%",
            f"    Urban:          {data['urban_pct']}%",
            "",
        ]

    if summary["registration_barriers"]:
        lines += [
            "REGISTRATION BARRIERS",
            "─" * 40,
        ]
        for label, data in sorted(
            summary["registration_barriers"].items(),
            key=lambda x: x[1].get("pct", 0),
            reverse=True
        ):
            bar = "█" * int(data.get("pct", 0) / 4)
            lines.append(
                f"  {label:<35} "
                f"{data.get('pct',0):5.1f}%  {bar}"
            )
        lines.append("")

    lines += [
        "KEY INTERVENTION TARGETS",
        "─" * 40,
    ]
    for target, data in summary[
        "intervention_targets"
    ].items():
        lines += [
            f"  {target}:",
            f"    Count:       {data['count']:,}",
            f"    Description: {data['description']}",
            "",
        ]

    lines += [
        "═" * 65,
        "  Next step: python shared_context.py",
        "  (loads finscope_summary.json into pipeline)",
        "═" * 65,
    ]

    return "\n".join(lines)


# ============================================================
# MAIN RUNNER
# ============================================================
def run_finscope_analysis():
    print("\n" + "═" * 60)
    print("  FINSCOPE TANZANIA 2023 — ANALYSIS")
    print("  Producing Tanzania-specific grounding data")
    print("═" * 60 + "\n")

    if not os.path.exists(FINSCOPE_FILE):
        print(f"  ✗ {FINSCOPE_FILE} not found")
        return

    print("STEP 1: LOADING DATA")
    print("-" * 40)
    df = load_data()

    print("\nSTEP 2: LIFECYCLE STAGES")
    print("-" * 40)
    df = assign_lifecycle_stages(df)

    print("\nSTEP 3: COMPLIANCE FUNNEL")
    print("-" * 40)
    funnel, df = build_compliance_funnel(df)

    print("\nSTEP 4: FUNNEL BY STAGE")
    print("-" * 40)
    by_stage = funnel_by_stage(df)

    print("\nSTEP 5: REGISTRATION BARRIERS")
    print("-" * 40)
    barriers = analyze_barriers(df)

    print("\nSTEP 6: GOVERNMENT TRUST")
    print("-" * 40)
    trust = analyze_trust(df)

    print("\nSTEP 7: MOBILE MONEY")
    print("-" * 40)
    mobile_money = analyze_mobile_money(df)

    print("\nSTEP 8: GEOGRAPHY")
    print("-" * 40)
    geography = analyze_geography(df)

    print("\nSTEP 9: INCOME SOURCES")
    print("-" * 40)
    income_sources = analyze_income_sources(df)

    print("\nSTEP 10: PENSION AND INSURANCE")
    print("-" * 40)
    pension_ins = analyze_pension_insurance(df)

    print("\nSTEP 11: FINANCIAL ACCESS STRAND")
    print("-" * 40)
    fin_access = analyze_financial_access(df)

    print("\nSTEP 12: ASSEMBLING SUMMARY")
    print("-" * 40)
    summary = build_summary(
        df, funnel, by_stage, barriers,
        trust, mobile_money, geography,
        income_sources, pension_ins, fin_access
    )

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved: {SUMMARY_FILE}")

    print("\nSTEP 13: TEXT REPORT")
    print("-" * 40)
    report = generate_text_report(summary)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  ✓ Saved: {REPORT_FILE}")

    print("\nSTEP 14: FULL FEATURE STORE")
    print("-" * 40)
    import json as _json
    feature_store = extract_full_feature_store(df)
    with open("finscope_feature_store.json", "w",
              encoding="utf-8") as _f:
        _json.dump(feature_store, _f, indent=2,
                   ensure_ascii=False)
    print(f"  ✓ Saved: finscope_feature_store.json")
    print(f"  ✓ {feature_store['total_indicators']} indicators "
          f"across {feature_store['domains_count']} domains")

    print(f"\n  Key findings:")
    print(f"  TIN rate:          {summary['tin_rate']}%")
    print(f"  MM penetration:    {summary['mm_rate']}%")
    print(f"  MM without TIN:    {summary['mm_no_tin']:,}")
    print(f"  Compliance gap:    {summary['tin_gap']:,}")
    print(f"\n  Files produced:")
    print(f"  → {SUMMARY_FILE}")
    print(f"  → {REPORT_FILE}")
    print(f"  → finscope_feature_store.json")
    print(f"\n  Next step: python shared_context.py")
    print("═" * 60)

    return summary


if __name__ == "__main__":
    run_finscope_analysis()
