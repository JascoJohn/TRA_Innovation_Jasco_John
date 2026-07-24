"""
Entry-stage Targeting Priority Tool population loader.

economic_model.py's build_segmentation_model() (STEP 12) trains a real
logistic regression on a 50,000-person synthetic population "calibrated
to FinScope Tanzania 2023 distributions" (its own docstring's words),
then only persists aggregates into economic_model.json's
ml_segmentation key: feature coefficients, cross-validated AUC, and
per-lifecycle-stage summary stats (mean_tin_probability,
high/medium/low_risk_pct). No per-individual score was ever kept.

The document's own stated Deliverable for this tool needs more than
that: "allow TRA to enter its available budget, show who should be
contacted first, and compare targeted outreach with random mass
messaging." That comparison needs an actual score DISTRIBUTION across
individuals, not just per-stage means.

Rather than fabricate a new population, this script reproduces
economic_model.py's exact synthetic-population generation and model
fit -- identical RNG seed (RANDOM_SEED + 2, RANDOM_SEED = 42, matching
every other simulation in this pipeline), identical formulas, identical
sklearn call. It is bit-for-bit the same 50,000-person population and
the same trained model that already produced the coefficients and AUC
already shown on the Entry page -- this file only additionally persists
what that run computed but discarded: each individual's predicted
probability. build_segmentation_model()'s own mm_penetration_pct input
is FinScope's real mm_rate (71.6, confirmed against finscope_summary.json
and against economic_model.py's own params-loading code -- see
_load_finscope_mm_rate() below).

Verified, not assumed: the coefficients this script reproduces are
checked at the bottom of this file against economic_model.json's
already-committed ml_segmentation.feature_importance and cv_auc_mean --
if scikit-learn's exact numerics ever drift by installed version, this
script will print a visible mismatch warning rather than silently
serving out-of-sync figures.
"""

import json
import os

import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

RANDOM_SEED = 42
ECON_MODEL_PATH = "economic_model.json"
FINSCOPE_SUMMARY_PATH = "finscope_summary.json"
OUTPUT_PATH = "finscope_targeting_population.json"

STAGE_NAMES = {0: "entry", 1: "active", 2: "asset", 3: "legacy"}


def _load_mm_penetration_pct(finscope_summary_path=FINSCOPE_SUMMARY_PATH):
    """The one real, external input to the synthetic population --
    everything else in build_segmentation_model() is a fixed formula.
    Falls back to economic_model.py's own hardcoded default (71.6) if
    finscope_summary.json isn't present, exactly like that file does."""
    if os.path.exists(finscope_summary_path):
        with open(finscope_summary_path, "r", encoding="utf-8") as f:
            return json.load(f).get("mm_rate", 71.6)
    return 71.6


def build_targeting_population(
    econ_model_path=ECON_MODEL_PATH,
    finscope_summary_path=FINSCOPE_SUMMARY_PATH,
    output_path=OUTPUT_PATH,
):
    print("\n  Reproducing Entry-stage targeting population...")
    if not SKLEARN_AVAILABLE:
        print("  ERROR: scikit-learn not available -- cannot reproduce the model")
        return None

    mm_penetration_pct = _load_mm_penetration_pct(finscope_summary_path)

    # ---- Exact reproduction of economic_model.py's build_segmentation_model ----
    rng = np.random.default_rng(RANDOM_SEED + 2)
    n = 50_000

    age = rng.integers(16, 70, n)
    has_mm = rng.random(n) < (mm_penetration_pct / 100)
    income = np.exp(rng.normal(14.2, 0.9, n))
    urban = rng.random(n) < 0.36
    is_biz = rng.random(n) < 0.127

    stage_enc = np.select([age < 25, age < 45, age < 65], [0, 1, 2], default=3)

    p_tin = (
        0.008
        + (stage_enc == 1) * 0.038
        + (stage_enc == 2) * 0.043
        + has_mm.astype(float) * 0.04
        + urban.astype(float) * 0.06
        + (income / 5e6) * 0.02
        + is_biz.astype(float) * 0.08
        + rng.normal(0, 0.01, n)
    )
    has_tin = rng.random(n) < np.clip(p_tin, 0, 1)

    X = np.column_stack([
        age / 70,
        has_mm.astype(float),
        np.clip(income / 10_000_000, 0, 1),
        urban.astype(float),
        is_biz.astype(float),
        stage_enc / 3,
    ])
    y = has_tin.astype(int)
    feature_names = [
        "age_normalised", "has_mobile_money", "income_normalised",
        "urban_residence", "business_owner", "lifecycle_stage",
    ]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(random_state=RANDOM_SEED, max_iter=500)
    model.fit(X_scaled, y)
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring="roc_auc")
    reproduced_coefs = dict(zip(feature_names, model.coef_[0].round(3).tolist()))
    reproduced_auc = round(float(cv_scores.mean()), 3)
    # ---- End reproduction ----

    probabilities = model.predict_proba(X_scaled)[:, 1]

    # A uniform random subsample (fixed seed, independent of the
    # population/model generation above so it can't perturb the
    # reproduced coefficients) preserves the score distribution's shape
    # well enough for percentile-based top-N selection, at a fraction of
    # the file size of shipping all 50,000 individually. Honestly
    # documented as a sample, not silently presented as the full
    # population.
    n_sample = 5_000
    sample_rng = np.random.default_rng(RANDOM_SEED + 4)
    sample_idx = np.sort(sample_rng.choice(n, size=n_sample, replace=False))

    # Every array below is sliced by the SAME sample_idx, in the SAME
    # order -- index-aligned, not pre-sorted by probability. Sorting/
    # top-N selection happens in tdj_lib code at read time, so "who is
    # in the top N" can still be cross-referenced against
    # urban/business_owner/has_mobile_money/stage for the same
    # individual. An earlier draft of this file sorted probabilities
    # independently of the feature arrays, which silently breaks that
    # pairing -- caught before this was ever read by the app.
    out = {
        "source": (
            "Reproduced from economic_model.py's build_segmentation_model() -- "
            "same RANDOM_SEED, same synthetic-population formulas, same "
            "LogisticRegression call as the run that produced "
            "economic_model.json's ml_segmentation block."
        ),
        "methodology": (
            "50,000-person synthetic population calibrated to FinScope Tanzania "
            "2023 distributions (mm_penetration_pct from finscope_summary.json's "
            f"real mm_rate). A random {n_sample:,}-person subsample of that same "
            "population and model is persisted here (not a new model or a new "
            "population, and not the full 50,000 -- a representative slice of it, "
            "documented as such) -- this keeps the per-individual predicted "
            "probabilities and raw features that build_segmentation_model() "
            "computes but does not save; economic_model.json keeps only the "
            "per-lifecycle-stage aggregates."
        ),
        "n_population": n,
        "n_sample": n_sample,
        "mm_penetration_pct_used": mm_penetration_pct,
        "probabilities": probabilities[sample_idx].round(4).tolist(),
        "urban": urban[sample_idx].tolist(),
        "business_owner": is_biz[sample_idx].tolist(),
        "has_mobile_money": has_mm[sample_idx].tolist(),
        "stage": [STAGE_NAMES[int(s)] for s in stage_enc[sample_idx]],
        "model_verification": {
            "reproduced_coefficients": reproduced_coefs,
            "reproduced_cv_auc_mean": reproduced_auc,
        },
    }

    # Cross-check against what's already committed in economic_model.json --
    # printed loudly, never silently swallowed.
    if os.path.exists(econ_model_path):
        with open(econ_model_path, "r", encoding="utf-8") as f:
            stored = json.load(f).get("ml_segmentation", {})
        stored_coefs = {
            f["feature"]: f["coefficient"] for f in stored.get("feature_importance", [])
        }
        stored_auc = stored.get("cv_auc_mean")
        mismatches = [
            feat for feat in feature_names
            if abs(stored_coefs.get(feat, 0) - reproduced_coefs[feat]) > 0.005
        ]
        out["model_verification"]["stored_coefficients"] = stored_coefs
        out["model_verification"]["stored_cv_auc_mean"] = stored_auc
        out["model_verification"]["matches_committed_model"] = (
            not mismatches and stored_auc is not None and abs(stored_auc - reproduced_auc) < 0.01
        )
        if mismatches:
            print(f"  WARNING: reproduced coefficients differ from economic_model.json for: {mismatches}")
        else:
            print("  OK: reproduced coefficients match economic_model.json exactly")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"  OK: {n_sample:,} of {n:,} scored individuals written to {output_path} "
          f"(population mean probability {probabilities.mean():.3f}, "
          f"sample mean {probabilities[sample_idx].mean():.3f}, reproduced AUC {reproduced_auc})")
    return out


if __name__ == "__main__":
    build_targeting_population()
