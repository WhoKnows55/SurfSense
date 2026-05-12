"""
Agent-level evaluation runner (Section 3.5 companion to LLM baseline).

For each scenario in scenarios.json, calls the deterministic agents directly
(using the scenario snapshot as the forecast source) and scores their outputs
with per-agent metrics defined in metrics.py.

The research agent is optional — it requires live API calls (Tavily + Azure
OpenAI) and caches results under evaluation/agent_eval/research_cache/.

Usage
-----
    # All scenarios, rule scoring (default)
    python -m evaluation.agent_eval.runner

    # ML scoring mode
    python -m evaluation.agent_eval.runner --ml

    # Include research agent evaluation (needs Tavily + Azure keys)
    python -m evaluation.agent_eval.runner --research

    # Single scenario
    python -m evaluation.agent_eval.runner --scenario guincho_24h
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.agent_eval.metrics import (
    score_research_agent,
    score_forecast_agent,
    score_condition_agent,
    score_trip_planning_agent,
    score_orchestrator,
)

SCENARIOS_CFG        = Path("scenarios/scenarios.json")
RESEARCH_CACHE       = Path("evaluation/agent_eval/research_cache")
RESULTS_CSV          = Path("evaluation/agent_eval/results.csv")
ORCH_RESULTS_CSV     = Path("evaluation/agent_eval/orchestrator_results.csv")


def _expected_hours(scenario_id: str) -> int:
    if "24h" in scenario_id:
        return 24
    if "5d" in scenario_id:
        return 5 * 24
    return 24


def _load_snapshot(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _format_score(v: float | None) -> str:
    return "N/A" if v is None else f"{round(v, 4)}"


def _build_settings(scoring_mode: str = "rule"):
    os.environ["SCORING_MODE"] = scoring_mode
    from config.settings import Settings
    return Settings()


def _call_research_agent(spot_name: str, settings, overrides: dict) -> dict:
    from app.core.llm_service import LLMService
    from app.agents.research_agent import ResearchAgent

    llm   = LLMService.from_settings(settings)
    agent = ResearchAgent(llm, settings)
    query = overrides.get(spot_name, spot_name)
    try:
        result = asyncio.run(agent.research_spot(query=query))
        return result or {}
    except Exception as exc:
        print(f"    [research] API error: {exc}")
        return {}


def _evaluate_research(
    spot_name: str,
    settings,
    overrides: dict,
) -> dict:
    cache_key  = spot_name.lower().replace(" ", "_")
    cache_file = RESEARCH_CACHE / f"{cache_key}.json"
    RESEARCH_CACHE.mkdir(parents=True, exist_ok=True)

    if cache_file.exists():
        print(f"  [research] cached  ({cache_file.name})")
        with open(cache_file) as f:
            output = json.load(f)
    else:
        print(f"  [research] calling agent for '{spot_name}' …", end=" ", flush=True)
        output = _call_research_agent(spot_name, settings, overrides)
        cache_file.write_text(json.dumps(output, indent=2))
        print("done" if output else "failed (empty)")

    return output


def evaluate_scenario(
    scenario: dict,
    overrides: dict,
    scoring_mode: str = "rule",
    run_research: bool = False,
) -> list[dict]:
    scenario_id   = scenario["id"]
    snapshot_path = scenario["snapshot"]
    skill_level   = scenario["skill_level"]

    if not Path(snapshot_path).exists():
        print(f"  [WARN] Snapshot missing: {snapshot_path} (skipping)")
        return []

    forecast = _load_snapshot(snapshot_path)
    spot_name = forecast.get("spot", scenario_id)
    expected_hours = _expected_hours(scenario_id)

    settings = _build_settings(scoring_mode)
    rows: list[dict] = []

    def _add(agent: str, scores: dict[str, float | None]) -> None:
        for metric, score in scores.items():
            rows.append({
                "scenario":    scenario_id,
                "skill_level": skill_level,
                "agent":       agent,
                "metric":      metric,
                "score":       _format_score(score),
            })
        label_width = max(len(m) for m in scores) + 2
        for metric, score in scores.items():
            print(f"    {metric:<{label_width}}{_format_score(score)}")

    # --- Research Agent (optional) ---
    if run_research:
        print("  [research_agent]")
        output = _evaluate_research(spot_name, settings, overrides)
        _add("research_agent", score_research_agent(output))
    else:
        print("  [research_agent]  skipped (pass --research to enable)")

    # --- Forecast Data Agent ---
    print("  [forecast_agent]")
    _add("forecast_agent", score_forecast_agent(forecast, expected_hours))

    # --- Condition Assessment Agent ---
    print("  [condition_agent]")
    from app.agents.condition_agent import ConditionAssessmentAgent
    condition_agent = ConditionAssessmentAgent(settings)
    assessments = condition_agent.assess_conditions(forecast, skill_level)
    _add("condition_agent", score_condition_agent(assessments, skill_level))

    # --- Trip Planning Agent ---
    print("  [trip_planning_agent]")
    from app.agents.trip_planning_agent import TripPlanningAgent
    trip_agent = TripPlanningAgent()
    windows = trip_agent.find_surf_windows(assessments, min_hours=2)
    _add("trip_planning_agent", score_trip_planning_agent(windows, assessments, min_hours=2))

    return rows


def _build_user_query(scenario: dict, spot_name: str) -> str:
    skill = scenario["skill_level"]
    if "5d" in scenario["id"]:
        return (
            f"I'm a {skill} surfer planning a 5-day trip to {spot_name}. "
            "When are the best times to surf and which windows would you recommend?"
        )
    return (
        f"I'm a {skill} surfer. What are the surf conditions at {spot_name} today? "
        "Are there any good windows to surf?"
    )


def evaluate_orchestrator_scenario(
    scenario: dict,
    scoring_mode: str = "rule",
) -> list[dict]:
    scenario_id   = scenario["id"]
    snapshot_path = scenario["snapshot"]
    skill_level   = scenario["skill_level"]

    if not Path(snapshot_path).exists():
        print(f"  [WARN] Snapshot missing: {snapshot_path} (skipping)")
        return []

    snapshot  = _load_snapshot(snapshot_path)
    spot_name = snapshot.get("spot", scenario_id)
    settings  = _build_settings(scoring_mode)

    from app.core.llm_service import LLMService
    from app.agents.orchestrator import Orchestrator

    llm  = LLMService.from_settings(settings)
    orch = Orchestrator(llm, settings)

    # Patch fetch_forecast to replay the snapshot — no Open-Meteo calls
    async def _snapshot_fetch(**_):
        return snapshot

    # Patch research_spot to return a minimal stub — no live search calls
    async def _stub_research(**_):
        coords = snapshot.get("coordinates", {})
        return {
            "name": spot_name,
            "latitude": coords.get("lat"),
            "longitude": coords.get("lon"),
            "break_type": "beach break",
            "wave_direction": "W",
            "bottom": "sand",
            "skill_minimum": "beginner",
            "skill_recommended": "intermediate",
            "beginner_friendly": skill_level == "beginner",
            "hazards": ["rip currents"],
            "best_swell_direction": "W",
            "description": f"Surf spot: {spot_name}",
        }

    orch._forecast_agent.fetch_forecast = _snapshot_fetch
    orch._research_agent.research_spot  = _stub_research

    user_query = _build_user_query(scenario, spot_name)
    print(f"  query: {user_query!r}")

    asyncio.run(orch.process(user_query))

    scores = score_orchestrator(orch._messages, orch._session_data, skill_level)

    rows: list[dict] = []
    label_width = max(len(m) for m in scores) + 2
    for metric, score in scores.items():
        print(f"    {metric:<{label_width}}{_format_score(score)}")
        rows.append({
            "scenario":    scenario_id,
            "skill_level": skill_level,
            "agent":       "orchestrator",
            "metric":      metric,
            "score":       _format_score(score),
        })
    return rows


def run_orchestrator(
    scoring_mode: str = "rule",
    scenario_filter: str | None = None,
) -> None:
    config    = json.loads(SCENARIOS_CFG.read_text())
    scenarios = config["scenarios"]

    all_rows: list[dict] = []
    for sc in scenarios:
        if scenario_filter and sc["id"] != scenario_filter:
            continue
        if not Path(sc["snapshot"]).exists():
            print(f"\n[WARN] Snapshot missing for '{sc['id']}': {sc['snapshot']}  (skipping)")
            continue
        print(f"\nScenario: {sc['id']}  (skill: {sc['skill_level']})")
        rows = evaluate_orchestrator_scenario(sc, scoring_mode=scoring_mode)
        all_rows.extend(rows)

    ORCH_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(ORCH_RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scenario", "skill_level", "agent", "metric", "score"],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows  {ORCH_RESULTS_CSV}")


def run_all(
    scoring_mode: str = "rule",
    run_research: bool = False,
    scenario_filter: str | None = None,
) -> None:
    config    = json.loads(SCENARIOS_CFG.read_text())
    scenarios = config["scenarios"]
    overrides = config.get("spot_search_overrides", {})

    all_rows: list[dict] = []
    for sc in scenarios:
        if scenario_filter and sc["id"] != scenario_filter:
            continue
        if not Path(sc["snapshot"]).exists():
            print(f"\n[WARN] Snapshot missing for '{sc['id']}': {sc['snapshot']}  (skipping)")
            continue
        print(f"\nScenario: {sc['id']}  (skill: {sc['skill_level']})")
        rows = evaluate_scenario(sc, overrides, scoring_mode=scoring_mode, run_research=run_research)
        all_rows.extend(rows)

    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scenario", "skill_level", "agent", "metric", "score"],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nWrote {len(all_rows)} rows  {RESULTS_CSV}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Per-agent evaluation harness")
    parser.add_argument("--scenario", type=str, default=None,
                        help="Evaluate a single scenario ID (default: all)")
    parser.add_argument("--ml", action="store_true",
                        help="Use ML scoring mode instead of rule-based")
    parser.add_argument("--research", action="store_true",
                        help="Also evaluate the research agent (requires Tavily + Azure keys)")
    parser.add_argument("--orchestrator", action="store_true",
                        help="Evaluate orchestrator coherence (requires Azure OpenAI key; uses snapshots for sub-agents)")
    args = parser.parse_args()

    scoring_mode = "ml" if args.ml else "rule"
    if args.orchestrator:
        run_orchestrator(scoring_mode=scoring_mode, scenario_filter=args.scenario)
    else:
        run_all(
            scoring_mode=scoring_mode,
            run_research=args.research,
            scenario_filter=args.scenario,
    )
