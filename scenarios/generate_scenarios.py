"""
Generates and maintains scenarios/scenarios.json from a declarative coverage matrix.

The matrix covers all available snapshots × all three skill levels, producing a
complete, reproducible scenario set that can be run automatically via driver.py.

Usage:
    python -m scenarios.generate_scenarios          # print coverage report only
    python -m scenarios.generate_scenarios --apply  # write scenarios.json
    python -m scenarios.generate_scenarios --apply --run   # write + run all scenarios
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCENARIOS_FILE = Path("scenarios/scenarios.json")
SNAPSHOTS_DIR  = Path("scenarios/snapshots")

# ---------------------------------------------------------------------------
# Coverage matrix
# Each entry: (snapshot_id, spot_display_name, window_label, skill_levels)
# ---------------------------------------------------------------------------
MATRIX = [
    ("guincho_24h",        "Praia do Guincho", "24h",          ["beginner", "intermediate", "advanced"]),
    ("guincho_winter_24h", "Praia do Guincho", "24h winter",   ["beginner", "intermediate", "advanced"]),
    ("ericeira_5d",        "Ericeira",          "5d",           ["beginner", "intermediate", "advanced"]),
    ("peniche_5d",         "Peniche",           "5d",           ["beginner", "intermediate", "advanced"]),
    ("sagres_5d",          "Sagres",            "5d",           ["beginner", "intermediate", "advanced"]),
    ("hossegor_5d",        "Hossegor",          "5d",           ["beginner", "intermediate", "advanced"]),
    ("jeffreys_bay_5d",    "Jeffreys Bay",      "5d",           ["beginner", "intermediate", "advanced"]),
]

# Search-name overrides forwarded to the orchestrator (spot name → search query).
SPOT_SEARCH_OVERRIDES = {
    "Sagres Tonel": "Sagres, Portugal",
    "Peniche Supertubos": "Peniche, Portugal",
    "Hossegor": "Hossegor, France",
    "Jeffreys Bay": "Jeffreys Bay, South Africa",
}

# ---------------------------------------------------------------------------
# ID derivation: stable, human-readable scenario IDs.
# Existing IDs that were manually assigned before this script existed are
# mapped explicitly so that runs/ directories are not invalidated.
# ---------------------------------------------------------------------------
_LEGACY_IDS: dict[tuple[str, str], str] = {
    ("guincho_24h",        "beginner"):     "guincho_24h",
    ("guincho_24h",        "intermediate"): "guincho_intermediate_24h",
    ("guincho_winter_24h", "beginner"):     "guincho_winter_24h",
    ("ericeira_5d",        "intermediate"): "ericeira_5d",
    ("ericeira_5d",        "advanced"):     "ericeira_advanced_5d",
    ("peniche_5d",         "intermediate"): "peniche_5d",
    ("peniche_5d",         "beginner"):     "peniche_beginner_5d",
    ("sagres_5d",          "intermediate"): "sagres_5d",
    ("sagres_5d",          "advanced"):     "sagres_advanced_5d",
    ("hossegor_5d",        "intermediate"): "hossegor_5d",
    ("jeffreys_bay_5d",    "advanced"):     "jeffreys_bay_5d",
}


def _scenario_id(snapshot_id: str, skill: str) -> str:
    legacy = _LEGACY_IDS.get((snapshot_id, skill))
    if legacy:
        return legacy
    # New IDs follow the pattern {snapshot_id}_{skill}
    return f"{snapshot_id}_{skill}"


def _description(spot: str, window: str, skill: str) -> str:
    cap = skill.capitalize()
    return f"{cap} surfer, {window} window, {spot}"


def build_scenarios() -> list[dict]:
    entries = []
    for snapshot_id, spot, window, skills in MATRIX:
        snap_path = f"scenarios/snapshots/{snapshot_id}.json"
        for skill in skills:
            entries.append({
                "id":          _scenario_id(snapshot_id, skill),
                "snapshot":    snap_path,
                "skill_level": skill,
                "description": _description(spot, window, skill),
            })
    return entries


def coverage_report(entries: list[dict], existing_ids: set[str]) -> None:
    new_ids = {e["id"] for e in entries}
    added   = new_ids - existing_ids
    kept    = new_ids & existing_ids

    snapshot_counts: dict[str, int] = {}
    for e in entries:
        sid = Path(e["snapshot"]).stem
        snapshot_counts[sid] = snapshot_counts.get(sid, 0) + 1

    print(f"\n{'='*60}")
    print(f"  Coverage matrix: {len(MATRIX)} snapshots × 3 skill levels")
    print(f"  Total scenarios : {len(entries)}")
    print(f"  Already present : {len(kept)}")
    print(f"  New to add      : {len(added)}")
    print(f"{'='*60}")
    print(f"\n  Per-snapshot breakdown:")
    for snap_id, _, _, skills in MATRIX:
        snap_path = SNAPSHOTS_DIR / f"{snap_id}.json"
        snap_ok   = "[✓]" if snap_path.exists() else "[✗ missing snapshot]"
        print(f"    {snap_ok} {snap_id:30s}  ×{len(skills)} skills = {snapshot_counts.get(snap_id,0)} scenarios")

    if added:
        print(f"\n  New scenario IDs:")
        for sc in entries:
            if sc["id"] in added:
                snap_path = Path(sc["snapshot"])
                snap_ok   = "✓" if snap_path.exists() else "✗ snapshot missing"
                print(f"    + {sc['id']:45s}  ({snap_ok})")

    missing_snaps = [
        e["id"] for e in entries
        if not Path(e["snapshot"]).exists()
    ]
    if missing_snaps:
        print(f"\n  WARNING: {len(missing_snaps)} scenarios reference missing snapshot files.")
        print(f"  Run `python -m scenarios.generate_snapshots --all` first.\n")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Write updated scenarios.json (default: report only)")
    parser.add_argument("--run", action="store_true",
                        help="After writing, run `driver.py --all` for new scenarios")
    args = parser.parse_args()

    current_config = json.loads(SCENARIOS_FILE.read_text()) if SCENARIOS_FILE.exists() else {}
    existing_ids   = {s["id"] for s in current_config.get("scenarios", [])}

    entries = build_scenarios()
    coverage_report(entries, existing_ids)

    if not args.apply:
        print("  (dry run — pass --apply to write scenarios.json)\n")
        return

    new_config = {
        "scenarios": entries,
        "spot_search_overrides": SPOT_SEARCH_OVERRIDES,
    }
    SCENARIOS_FILE.write_text(json.dumps(new_config, indent=2))
    print(f"  Written {len(entries)} scenarios to {SCENARIOS_FILE}\n")

    if args.run:
        print("  Running driver.py --all …\n")
        result = subprocess.run(
            [sys.executable, "-m", "evaluation.llm_baseline.driver", "--all"],
            check=False,
        )
        if result.returncode != 0:
            print(f"\n  driver.py exited with code {result.returncode}")
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
