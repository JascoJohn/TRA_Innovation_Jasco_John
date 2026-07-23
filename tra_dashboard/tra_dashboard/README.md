# The Taxpayer Development Journey — Interactive Dashboard

A 6-page Streamlit app, one page per lifecycle stage, matching the figures and
mechanisms in the written submission. Most pages now read **real, live data**
from this project's own pipeline (`../../pipeline/`) rather than hardcoded
numbers — every page still captions clearly which figures are real and which
remain illustrative, and why.

## Project layout

```
TRA Innovation 2/
├── pipeline/                  ← standalone data/computation layer (see below)
└── tra_dashboard/
    └── tra_dashboard/         ← this Streamlit app
        ├── Home.py
        ├── common.py          ← thin re-export shim, kept for backward compatibility
        ├── tdj_lib/           ← the actual reusable code
        │   ├── styling.py     ← palette, CSS, evidence-tier tags (no data dependency)
        │   ├── stages.py      ← 6-stage registry + cross-page nav (no data dependency)
        │   └── pipeline_data.py  ← reads pipeline/'s JSON output, never guesses
        ├── pages/
        │   ├── 1_Seed.py       (illustrative — see "Current status" below)
        │   ├── 2_Entry.py      (live)
        │   ├── 3_Active.py     (live)
        │   ├── 4_Enterprise.py (live)
        │   ├── 5_Asset.py      (illustrative)
        │   └── 6_Legacy.py     (partially live)
        └── requirements.txt
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

That's it for the dashboard itself — `pipeline_data.py` reads `pipeline/`'s
already-generated JSON files at startup. You don't need to run the pipeline
to see live data; it ships with output already in place.

## Regenerating the underlying data

Everything the dashboard reads is computed by `../../pipeline/`, fully
standalone — no dependency on any other project. To regenerate all of it from
the raw FinScope microdata:

```bash
cd ../../pipeline
pip install -r requirements.txt
python run_all.py
```

This runs, in order: FinScope summary statistics → the 15-component economic
model → a standalone tier-migration simulation (Enterprise's tier chart) →
the intervention register (parses the 8 LLM-generated interventions in
`report_sections.json` plus the 6 Python-modeled ones) → the FinScope
region×activity prevalence table (Active's page). See `pipeline/run_all.py`
for the exact order and why it matters, and the docstring at the top of each
script for what it computes and from what real source.

Note: `pipeline/intervention_registrar.py` mints fresh random intervention
IDs on every run (`register_all(force=True)`), so re-running it will change
the specific IDs `pipeline_data.py` looks up interventions by *title*, not
ID, so this doesn't break anything — but don't expect IDs to stay stable
across regenerations.

## Current status per page

- **Seed** (`1_Seed.py`): fully illustrative by design — no real model exists
  for this mechanism in either project (tagged HYPOTHESIS in the written
  submission; revenue is deliberately not scored for this stage).
- **Entry** (`2_Entry.py`): **live.** Cost/revenue/ROI read from
  `economic_model.json`. The scoring gauge uses the real trained logistic
  regression's coefficients (AUC 0.630 ± 0.018) — the *scaling* is
  illustrative (no trained intercept is stored in the JSON), captioned as
  such on the page.
- **Active** (`3_Active.py`): **live.** Cost/revenue/ROI read from
  `economic_model.json`. The region selector shows a real, weighted
  FinScope-derived business-activity prevalence table (31 regions × 4
  activity categories). This is a prevalence table, not a turnover-band
  calculator — FinScope 2023 has no turnover/income-amount variable at all
  (checked exhaustively against the codebook and raw columns), so a real
  turnover calculator isn't buildable from this dataset, not just "not yet
  wired in."
- **Enterprise** (`4_Enterprise.py`): **live cost**, from
  `intervention_register.json`. Revenue/ROI remain illustrative — seen
  below. The tier-migration chart is real: a standalone 500,000-agent
  simulation (`pipeline/economic_model.py`'s `run_tier_migration_simulation`)
  using the exact tier thresholds shown on the page.
- **Asset** (`5_Asset.py`): fully illustrative by design — tagged HYPOTHESIS
  in the written submission (reciprocity mechanism, revenue not modeled).
- **Legacy** (`6_Legacy.py`): **live cost**, from `intervention_register.json`.
  Revenue/ROI remain illustrative — see below. Component weights in the
  score-builder are corrected to sum to a true 100 (the written submission's
  own example sums to 100 but is labeled 92/100 — worth fixing there too).

**Known real gap, not a "todo":** Enterprise's and Legacy's revenue/ROI have
no live source. Computing those requires
`economic_model_per_intervention.py`, which was deliberately *not* migrated
into `pipeline/` — it depends on a much broader evidence base
(`tanzania_policy_agent`'s full evidence store) that's out of scope for this
dashboard's own pipeline. `pipeline_data.py` returns this as an honest,
captioned gap rather than reusing a stale figure.

## Deploying to share.streamlit.io

1. Create a new **public** GitHub repo and push `tra_dashboard/tra_dashboard/`
   to it — `Home.py`, `common.py`, `tdj_lib/`, `pages/`, and
   `requirements.txt` all need to be at the repo root.
2. Go to **share.streamlit.io**, sign in with GitHub, click **New app**.
3. Point it at your repo, branch `main`, main file path `Home.py`. Deploy.
4. You'll get one link, e.g. `https://tra-taxpayer-journey.streamlit.app` —
   every stage page is reachable under it (`/Seed`, `/Entry`, `/Active`,
   `/Enterprise`, `/Asset`, `/Legacy`).

**Important:** `pipeline/` (40MB+ of raw FinScope data) is deliberately
**not** part of the dashboard's own repo — don't push it alongside
`tra_dashboard/`. On a deploy that doesn't include `pipeline/`'s JSON output
files, every page automatically falls back to its illustrative values (the
same honest-gap behavior as running locally without the pipeline present) —
nothing breaks, it just reads as a fresh, un-migrated checkout. If you want
live data on the deployed version too, either commit `pipeline/`'s small
JSON outputs (not the 40MB CSV) into the same repo, or point
`TDJ_PIPELINE_DIR` at wherever you host them.

## Live Demo
https://trainnovationjascojohn-mdfppq2bztb4yyxubibhww.streamlit.app
