"""
Scenario 3: Guincho with ML scoring – identical inputs to Scenario 1, SCORING_MODE=ml.

Thesis anchor: Section 3.4, Scenario 3.

Reuses scenarios/snapshots/guincho_24h.json (byte-identical forecast to Scenario 1)
so the only difference between output files is the scoring path.

Each assessment record in the output includes 'feature_contributions' (SHAP values)
satisfying success criterion 4 of Section 3.5.3.

Prerequisites:
    python -m ml.data.collect
    python -m ml.train
    # Then run this script with SCORING_MODE=ml (or just run it directly –
    # the script forces ml mode regardless of the environment variable).

Output: scenarios/results/scenario_03_ml.json
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Force ML mode for this scenario regardless of .env
os.environ["SCORING_MODE"] = "ml"

from config.settings import Settings
from app.agents.forecast_data_agent import ForecastDataAgent
from app.agents.condition_agent import ConditionAssessmentAgent
from app.agents.research_agent import ResearchAgent

SNAPSHOT = "scenarios/snapshots/guincho_24h.json"
OUTPUT   = "scenarios/results/scenario_03_ml.json"
SPOT     = "Praia do Guincho"
SKILL    = "beginner"
DAYS     = 1


async def run() -> dict:
    settings = Settings()
    assert settings.scoring.scoring_mode == "ml", (
        "SCORING_MODE must be 'ml' for Scenario 3. "
        "Run `python -m ml.train` first."
    )

    from app.core.llm_service import get_llm_provider
    llm = get_llm_provider(settings)

    research_agent  = ResearchAgent(llm, settings)
    forecast_agent  = ForecastDataAgent(settings)
    condition_agent = ConditionAssessmentAgent(settings)

    print(f"[S3] Researching {SPOT} …")
    research = await research_agent.research_spot(SPOT)
    if "error" in research:
        raise RuntimeError(f"Research failed: {research['error']}")
    forecast_agent.set_research_data(SPOT, research)

    print(f"[S3] Loading forecast from snapshot {SNAPSHOT} …")
    if not Path(SNAPSHOT).exists():
        raise FileNotFoundError(
            f"Snapshot not found: {SNAPSHOT}\n"
            "Run scenarios/01_single_spot_guincho.py first to create it."
        )
    forecast = await forecast_agent.fetch_forecast(SPOT, days=DAYS, snapshot_path=SNAPSHOT)
    print(f"[S3] {forecast['forecast_count']} forecast points")

    print(f"[S3] Assessing conditions (ML mode) …")
    assessments = condition_agent.assess_conditions(forecast, skill_level=SKILL)

    missing_contrib = [a for a in assessments if "feature_contributions" not in a]
    if missing_contrib:
        print(f"[S3] Warning: {len(missing_contrib)} records missing feature_contributions")

    result = {
        "scenario":     "03_guincho_ml",
        "spot":         SPOT,
        "skill_level":  SKILL,
        "scoring_mode": "ml",
        "model_path":   settings.scoring.ml_model_path,
        "assessments":  assessments,
    }

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(result, f, default=str, indent=2)
    print(f"[S3] Wrote {len(assessments)} records → {OUTPUT}")
    return result


if __name__ == "__main__":
    asyncio.run(run())
