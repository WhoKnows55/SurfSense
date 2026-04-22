"""
Scenario 1: Single-spot assessment – Praia do Guincho (beginner, 24 h, rule mode).

Thesis anchor: Section 3.4, Scenario 1.

Inputs  : spot = Praia do Guincho, skill = beginner, horizon = 1 day, scoring = rule
Snapshot: scenarios/snapshots/guincho_24h.json  (written on first run, replayed after)
Output  : scenarios/results/scenario_01_rule.json

Usage:
    python -m scenarios.01_single_spot_guincho
    SCORING_MODE=rule python scenarios/01_single_spot_guincho.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from app.agents.forecast_data_agent import ForecastDataAgent
from app.agents.condition_agent import ConditionAssessmentAgent
from app.agents.research_agent import ResearchAgent

SNAPSHOT = "scenarios/snapshots/guincho_24h.json"
OUTPUT   = "scenarios/results/scenario_01_rule.json"
SPOT     = "Praia do Guincho"
SKILL    = "beginner"
DAYS     = 1


async def run() -> dict:
    settings = Settings()

    # ResearchAgent needs an LLM provider; import here to keep script self-contained
    from app.core.llm_service import LLMService
    llm = LLMService.from_settings(settings)

    research_agent    = ResearchAgent(llm, settings)
    forecast_agent    = ForecastDataAgent(settings)
    condition_agent   = ConditionAssessmentAgent(settings)

    print(f"[S1] Researching {SPOT} …")
    research = await research_agent.research_spot(SPOT)
    if "error" in research:
        raise RuntimeError(f"Research failed: {research['error']}")
    forecast_agent.set_research_data(SPOT, research)

    print(f"[S1] Fetching forecast (snapshot={SNAPSHOT}) …")
    forecast = await forecast_agent.fetch_forecast(SPOT, days=DAYS, snapshot_path=SNAPSHOT)
    if "error" in forecast:
        raise RuntimeError(f"Forecast failed: {forecast['error']}")
    print(f"[S1] {forecast['forecast_count']} forecast points")

    print(f"[S1] Assessing conditions for {SKILL} …")
    assessments = condition_agent.assess_conditions(forecast, skill_level=SKILL)

    result = {
        "scenario": "01_single_spot_rule",
        "spot": SPOT,
        "skill_level": SKILL,
        "scoring_mode": "rule",
        "forecast_source": forecast.get("source"),
        "assessments": assessments,
    }

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(result, f, default=str, indent=2)
    print(f"[S1] Wrote {len(assessments)} records → {OUTPUT}")
    return result


if __name__ == "__main__":
    asyncio.run(run())
