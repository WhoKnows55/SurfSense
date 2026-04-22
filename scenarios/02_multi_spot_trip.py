"""
Scenario 2: Multi-spot trip planning – Ericeira, Peniche, Sagres (intermediate, 5 days).

Thesis anchor: Section 3.4, Scenario 2.

Inputs  : spots = [Ericeira, Peniche/Supertubos, Sagres/Tonel]
          skill = intermediate, horizon = 5 days, scoring = rule
Snapshots: scenarios/snapshots/{ericeira,peniche,sagres}_5d.json
Output  : scenarios/results/scenario_02_rule.json

Usage:
    python -m scenarios.02_multi_spot_trip
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from app.agents.forecast_data_agent import ForecastDataAgent
from app.agents.condition_agent import ConditionAssessmentAgent
from app.agents.research_agent import ResearchAgent
from app.agents.trip_planning_agent import TripPlanningAgent

SPOTS = [
    ("Ericeira",          "scenarios/snapshots/ericeira_5d.json"),
    ("Peniche Supertubos","scenarios/snapshots/peniche_5d.json"),
    ("Sagres Tonel",      "scenarios/snapshots/sagres_5d.json"),
]
SKILL  = "intermediate"
DAYS   = 5
OUTPUT = "scenarios/results/scenario_02_rule.json"


async def run() -> dict:
    settings = Settings()

    from app.core.llm_service import LLMService
    llm = LLMService.from_settings(settings)

    research_agent  = ResearchAgent(llm, settings)
    forecast_agent  = ForecastDataAgent(settings)
    condition_agent = ConditionAssessmentAgent(settings)
    trip_agent      = TripPlanningAgent()

    spots_data: dict[str, dict] = {}

    for spot_name, snapshot in SPOTS:
        print(f"[S2] Researching {spot_name} …")
        research = await research_agent.research_spot(spot_name)
        if "error" in research:
            print(f"[S2] Warning: research failed for {spot_name}: {research['error']}")
            continue
        forecast_agent.set_research_data(spot_name, research)

        print(f"[S2] Fetching forecast …")
        forecast = await forecast_agent.fetch_forecast(spot_name, days=DAYS, snapshot_path=snapshot)
        if "error" in forecast:
            print(f"[S2] Warning: forecast failed for {spot_name}: {forecast['error']}")
            continue

        assessments = condition_agent.assess_conditions(forecast, skill_level=SKILL)
        windows     = trip_agent.find_surf_windows(assessments=assessments)
        spots_data[spot_name] = {
            "research":    research,
            "forecast":    forecast,
            "assessments": assessments,
            "windows":     windows,
        }

    print("[S2] Planning itinerary …")
    itinerary = trip_agent.plan_itinerary(
        spot_names=list(spots_data.keys()),
        spots_data=spots_data,
        skill_level=SKILL,
        days=DAYS,
    )

    result = {
        "scenario":    "02_multi_spot_rule",
        "spots":       list(spots_data.keys()),
        "skill_level": SKILL,
        "scoring_mode":"rule",
        "itinerary":   itinerary,
        "spots_data":  {
            name: {
                "assessments": d["assessments"],
                "windows":     d["windows"],
            }
            for name, d in spots_data.items()
        },
    }

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(result, f, default=str, indent=2)
    print(f"[S2] Wrote itinerary for {len(spots_data)} spots → {OUTPUT}")
    return result


if __name__ == "__main__":
    asyncio.run(run())
