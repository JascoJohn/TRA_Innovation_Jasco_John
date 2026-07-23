"""
Regenerates every data file the TRA Innovation 2 dashboard reads, fully
standalone -- no dependency on the sibling tanzania_policy_agent project.

Order matters: economic_model.py's run_economic_model() reads
finscope_summary.json if present (to overlay real FinScope-measured
values over its hardcoded defaults), and intervention_registrar.py's
register_all() reads both report_sections.json and economic_model.json.
The tier-migration simulation is deliberately NOT part of
run_economic_model() itself (see the "D.2" comment above
run_tier_migration_simulation() in economic_model.py for why -- it's
additive by design, not part of the main 15-step orchestration), so it's
run here as its own step and merged into the same economic_model.json
run_economic_model() just wrote. finscope_region_activity_loader.py is
independent of the other three (reads FinScope.csv directly) but run
last for a clean single pass.

Usage:
    python run_all.py
"""

import json

import finscope_analysis
import economic_model
import intervention_registrar
import finscope_region_activity_loader


def main():
    print("=" * 60)
    print("STEP 1: FinScope summary statistics")
    print("=" * 60)
    finscope_analysis.run_finscope_analysis()

    print("\n" + "=" * 60)
    print("STEP 2: Economic model (15 components)")
    print("=" * 60)
    economic_model.run_economic_model()

    print("\n" + "=" * 60)
    print("STEP 3: Tier-migration simulation (Enterprise dashboard)")
    print("=" * 60)
    with open("economic_model.json", encoding="utf-8") as f:
        base_parameters = json.load(f)["base_parameters"]
    tier_result = economic_model.run_tier_migration_simulation(
        base_parameters, n_agents=500_000, n_years=10
    )
    with open("economic_model.json", encoding="utf-8") as f:
        model = json.load(f)
    model["tier_migration_simulation"] = tier_result
    with open("economic_model.json", "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("STEP 4: Intervention register")
    print("=" * 60)
    intervention_registrar.register_all(force=True)

    print("\n" + "=" * 60)
    print("STEP 5: FinScope region x activity prevalence")
    print("=" * 60)
    finscope_region_activity_loader.build_finscope_region_activity_data()

    print("\n" + "=" * 60)
    print("DONE -- all files regenerated in this directory")
    print("=" * 60)


if __name__ == "__main__":
    main()
