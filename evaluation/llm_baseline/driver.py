"""
LLM baseline comparison driver (Section 3.5.2).

Sends identical prompts to two systems:
  1. SurfSense  – via Orchestrator.process(), with forecast data injected from
                  the snapshot so both systems see the same input.
  2. GPT-4o-mini – via Azure OpenAI (same deployment as orchestrator)

Three runs per system per scenario → 6 outputs per scenario.
Scenarios are defined in scenarios/scenarios.json.  Existing files are skipped
unless --force is passed.

Usage:
    python -m evaluation.llm_baseline.driver --scenario guincho_24h
    python -m evaluation.llm_baseline.driver --all
    python -m evaluation.llm_baseline.driver --all --force
    python -m evaluation.llm_baseline.driver --list
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

RUNS_DIR    = Path("evaluation/llm_baseline/runs")
PROMPTS     = Path("evaluation/llm_baseline")
SCENARIOS   = Path("scenarios/scenarios.json")
N_RUNS      = 3


# ---------------------------------------------------------------------------
# Scenario config
# ---------------------------------------------------------------------------

def _load_scenarios() -> list[dict]:
    with open(SCENARIOS) as f:
        return json.load(f)["scenarios"]


def _spot_search_name(spot: str, overrides: dict[str, str]) -> str:
    return overrides.get(spot, spot)


# ---------------------------------------------------------------------------
# Snapshot / prompt helpers
# ---------------------------------------------------------------------------

def _load_snapshot(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _build_forecast_table(forecast: dict) -> str:
    rows = []
    for fc in forecast.get("forecasts", []):
        ts       = fc.get("timestamp", "")[:16]
        wave_avg = fc.get("waves", {}).get("avg_m", "?")
        swell_h  = fc.get("swell", {}).get("height_m", "?")
        swell_t  = fc.get("swell", {}).get("period_s", "?")
        wind_s   = fc.get("wind", {}).get("speed_kph", "?")
        wind_d   = fc.get("wind", {}).get("direction", "?")
        offshore = "Y" if fc.get("wind", {}).get("is_offshore") else "N"
        rows.append(
            f"{ts} | {wave_avg:>5} | {swell_h:>5} | {swell_t:>5} | "
            f"{wind_s:>5} | {wind_d:>3} | {offshore}"
        )
    header = "timestamp        | wave  | sw_h  | sw_t  | wind  | dir | off"
    sep    = "-" * len(header)
    return "\n".join([header, sep] + rows)


def _build_prompt(snapshot_path: str, skill_level: str = "intermediate") -> str:
    template = (PROMPTS / "prompt_template.txt").read_text()
    forecast  = _load_snapshot(snapshot_path)
    spot_name = forecast.get("spot", "Unknown")
    hours     = forecast.get("forecast_count", len(forecast.get("forecasts", [])))
    table     = _build_forecast_table(forecast)

    skill_thresholds = {
        "beginner":     {"wave": 1.5 * 1.5, "wind": 15.0 * 1.5},
        "intermediate": {"wave": 2.5 * 1.5, "wind": 20.0 * 1.5},
        "advanced":     {"wave": 5.0 * 1.5, "wind": 30.0 * 1.5},
    }
    th = skill_thresholds.get(skill_level, skill_thresholds["intermediate"])

    return template.format(
        skill_level=skill_level,
        spot_name=spot_name,
        hours=hours,
        forecast_table=table,
        unsafe_wave_m=th["wave"],
        unsafe_wind_kph=th["wind"],
    )


def _prompt_hash(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# System clients
# ---------------------------------------------------------------------------

def _call_gpt(prompt: str) -> str:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
    resp = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content or ""


async def _call_surfsense(
    snapshot_path: str,
    skill_level: str,
    overrides: dict[str, str],
) -> str:
    from config.settings import Settings
    from app.core.llm_service import LLMService
    from app.agents.orchestrator import Orchestrator

    settings = Settings()
    llm      = LLMService.from_settings(settings)
    orch     = Orchestrator(llm, settings)

    forecast    = _load_snapshot(snapshot_path)
    spot        = forecast.get("spot", "Unknown")
    search_spot = _spot_search_name(spot, overrides)
    snap_date   = forecast.get("date")

    # Inject the snapshot so SurfSense uses the same forecast data as GPT-4o-mini.
    # The orchestrator calls fetch_forecast which normally hits the live API.
    # Replacing it with a function that returns the snapshot ensures the two
    # systems are evaluated on identical input.
    orch._forecast_agent.fetch_forecast = lambda *args, **kwargs: forecast

    timestamps = [fc["timestamp"] for fc in forecast.get("forecasts", [])]
    if timestamps:
        start_date = timestamps[0][:10]
        end_date   = timestamps[-1][:10]
        date_range = start_date if start_date == end_date else f"{start_date} to {end_date}"
    else:
        date_range = None

    if snap_date:
        user_msg = (
            f"I'm a {skill_level} surfer. Please check the surf conditions at "
            f"{search_spot} on {snap_date}. Rate each hour as ideal, suitable, "
            f"challenging, or unsafe, flag any unsafe hours, and identify the best "
            f"surf windows. No need to ask for further details."
        )
    elif date_range:
        user_msg = (
            f"I'm a {skill_level} surfer. Please check the surf conditions at "
            f"{search_spot} for {date_range}. Rate each hour as ideal, suitable, "
            f"challenging, or unsafe, flag any unsafe hours, and identify the best "
            f"surf windows. No need to ask for further details."
        )
    else:
        user_msg = (
            f"I'm a {skill_level} surfer. Please check the current conditions at "
            f"{search_spot} and identify the best surf windows. "
            f"No need to ask for further details."
        )
    return await orch.process(user_msg)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_scenario(
    scenario: dict,
    overrides: dict[str, str],
    force: bool = False,
) -> None:
    scenario_id    = scenario["id"]
    snapshot_path  = scenario["snapshot"]
    skill_level    = scenario["skill_level"]

    prompt = _build_prompt(snapshot_path, skill_level)
    phash  = _prompt_hash(prompt)

    for run_idx in range(1, N_RUNS + 1):
        for system in ("surfsense", "gpt4o_mini"):
            out_dir   = RUNS_DIR / scenario_id / system
            out_path  = out_dir / f"run_{run_idx}.txt"
            meta_path = out_dir / "prompt_hash.txt"

            if out_path.exists() and not force:
                print(f"  [skip] {out_path}")
                continue

            out_dir.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(phash)

            print(f"  [{system}] run {run_idx}/{N_RUNS} …", end=" ", flush=True)
            try:
                if system == "surfsense":
                    response = asyncio.run(
                        _call_surfsense(snapshot_path, skill_level, overrides)
                    )
                else:
                    response = _call_gpt(prompt)

                out_path.write_text(response)
                print("done")
            except Exception as exc:
                out_path.write_text(f"ERROR: {exc}")
                print(f"error: {exc}")


def run_all(force: bool = False) -> None:
    config    = json.loads(SCENARIOS.read_text())
    scenarios = config["scenarios"]
    overrides = config.get("spot_search_overrides", {})

    for sc in scenarios:
        snap = Path(sc["snapshot"])
        if not snap.exists():
            print(f"\n[WARN] Snapshot missing for '{sc['id']}': {snap}  (skipping)")
            continue
        print(f"\nScenario: {sc['id']}  (skill: {sc['skill_level']})")
        run_scenario(sc, overrides, force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=str, default=None,
                        help="ID of a specific scenario (from scenarios.json)")
    parser.add_argument("--all", action="store_true",
                        help="Run all scenarios defined in scenarios.json")
    parser.add_argument("--force", action="store_true",
                        help="Re-query even if output file exists")
    parser.add_argument("--list", action="store_true",
                        help="List all configured scenarios and exit")
    args = parser.parse_args()

    if args.list:
        config = json.loads(SCENARIOS.read_text())
        for sc in config["scenarios"]:
            snap   = Path(sc["snapshot"])
            exists = "✓" if snap.exists() else "✗"
            print(f"  [{exists}] {sc['id']:35s}  skill={sc['skill_level']:12s}  {sc['description']}")
        sys.exit(0)

    config    = json.loads(SCENARIOS.read_text())
    overrides = config.get("spot_search_overrides", {})

    if args.scenario:
        matches = [s for s in config["scenarios"] if s["id"] == args.scenario]
        if not matches:
            print(f"Scenario '{args.scenario}' not found. Use --list to see options.")
            sys.exit(1)
        sc   = matches[0]
        snap = Path(sc["snapshot"])
        if not snap.exists():
            print(f"Snapshot missing: {snap}")
            sys.exit(1)
        print(f"Scenario: {sc['id']}  (skill: {sc['skill_level']})")
        run_scenario(sc, overrides, force=args.force)
    elif args.all:
        run_all(force=args.force)
    else:
        parser.print_help()
