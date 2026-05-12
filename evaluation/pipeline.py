"""
Unified evaluation pipeline runner (Section 3.5.2).

Chains: driver (generate LLM outputs) → score (compute metrics) → summary.

Usage:
    python -m evaluation.pipeline                          # run all, skip existing
    python -m evaluation.pipeline --force                  # regenerate all runs
    python -m evaluation.pipeline --score-only             # skip runs, just score
    python -m evaluation.pipeline --scenario guincho_24h  # one scenario only
    python -m evaluation.pipeline --list                   # list configured scenarios
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCENARIOS_CFG = Path("scenarios/scenarios.json")
RESULTS_CSV   = Path("evaluation/llm_baseline/results.csv")
RUNS_DIR      = Path("evaluation/llm_baseline/runs")


def _load_scenarios() -> list[dict]:
    with open(SCENARIOS_CFG) as f:
        return json.load(f)["scenarios"]


def _run_driver(scenario_id: str | None = None, force: bool = False) -> int:
    cmd = [sys.executable, "-m", "evaluation.llm_baseline.driver"]
    if scenario_id:
        cmd += ["--scenario", scenario_id]
    else:
        cmd += ["--all"]
    if force:
        cmd += ["--force"]
    return subprocess.run(cmd).returncode


def _run_scorer() -> int:
    return subprocess.run(
        [sys.executable, "-m", "evaluation.llm_baseline.score"]
    ).returncode


def _print_summary() -> None:
    if not RESULTS_CSV.exists():
        print("  [no results.csv found]")
        return

    import csv
    rows: dict[tuple, dict] = {}
    with open(RESULTS_CSV) as f:
        for r in csv.DictReader(f):
            rows[(r["scenario"], r["system"], r["dimension"])] = r["score"]

    scenarios = sorted({k[0] for k in rows})
    systems   = sorted({k[1] for k in rows})
    dims      = ["factual_consistency", "safety_enforcement",
                 "temporal_optimisation", "explainability", "consistency"]

    # Header
    col_w = 22
    header = f"{'scenario':<30} {'system':<14}" + "".join(f"{d[:col_w]:>{col_w}}" for d in dims)
    print("\n" + header)
    print("-" * len(header))

    for sc in scenarios:
        for sys_name in systems:
            scores = [rows.get((sc, sys_name, d), "–") for d in dims]
            row = f"{sc:<30} {sys_name:<14}" + "".join(f"{s:>{col_w}}" for s in scores)
            print(row)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="SurfSense LLM evaluation pipeline")
    parser.add_argument("--scenario", type=str, default=None,
                        help="Run a single scenario by ID")
    parser.add_argument("--force", action="store_true",
                        help="Regenerate run files even if they already exist")
    parser.add_argument("--score-only", action="store_true",
                        help="Skip generating runs; only run the scorer and print summary")
    parser.add_argument("--list", action="store_true",
                        help="List all configured scenarios and exit")
    args = parser.parse_args()

    if args.list:
        scenarios = _load_scenarios()
        print(f"\n{'ID':<35} {'skill':12} description")
        print("-" * 90)
        for sc in scenarios:
            snap   = Path(sc["snapshot"])
            exists = "✓" if snap.exists() else "✗ missing"
            runs   = (RUNS_DIR / sc["id"]).exists()
            run_mark = "runs✓" if runs else "runs✗"
            print(f"  {sc['id']:<33} {sc['skill_level']:12} {sc['description']}  [{exists}] [{run_mark}]")
        print()
        return

    if not args.score_only:
        print("=" * 60)
        print("Step 1 / 2 — generating LLM outputs")
        print("=" * 60)
        rc = _run_driver(scenario_id=args.scenario, force=args.force)
        if rc != 0:
            print(f"\n[WARN] driver exited with code {rc}. Continuing to scorer.")

    print("\n" + "=" * 60)
    print("Step 2 / 2 — scoring outputs")
    print("=" * 60)
    rc = _run_scorer()
    if rc != 0:
        print(f"\n[ERROR] scorer exited with code {rc}.")
        sys.exit(rc)

    print("\n" + "=" * 60)
    print("Results summary")
    print("=" * 60)
    _print_summary()
    print(f"\nFull results: {RESULTS_CSV}")


if __name__ == "__main__":
    main()
