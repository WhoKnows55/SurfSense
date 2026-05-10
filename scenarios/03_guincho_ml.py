"""
Scenario 3: ML-Enhanced Condition Assessment – Praia do Guincho (beginner, 24 h).

Thesis anchor: Section 3.4.3, Scenario 3.

Identical inputs to Scenario 1 but with SCORING_MODE=ml. The orchestrator
surfaces SHAP-derived feature explanations in its response (system prompt
instructs it to name the top positive and negative contributors).

Output: scenarios/results/scenario_03_ml_demo.txt

Prerequisites:
    python -m ml.train   (creates ml/models/surf_condition_model.joblib)

Usage:
    python -m scenarios.03_guincho_ml
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["SCORING_MODE"] = "ml"

import json

from config.settings import Settings
from app.core.llm_service import LLMService
from app.agents.orchestrator import Orchestrator

OUTPUT = "scenarios/results/scenario_03_ml_demo.txt"
SNAPSHOT = "scenarios/snapshots/guincho_24h.json"

USER_MESSAGE = (
    "I'm a beginner surfer planning to surf Praia do Guincho today. "
    "Please check if the conditions are safe for my level, rate each hour "
    "as ideal, suitable, challenging, or unsafe, flag any unsafe windows, "
    "tell me the best time to go, and explain the main factors driving each rating. "
    "No need to ask for further details."
)


async def run() -> str:
    settings = Settings()
    assert settings.scoring.scoring_mode == "ml", (
        "SCORING_MODE must be 'ml' — run `python -m ml.train` first."
    )

    llm = LLMService.from_settings(settings)
    orch = Orchestrator(llm, settings)
    _data = json.loads(Path(SNAPSHOT).read_text())
    orch._forecast_agent.fetch_forecast = lambda spot_name, days=3, snapshot_path=None: _data

    print(f"[S3] Scoring mode: {settings.scoring.scoring_mode}")
    print(f"[S3] User: {USER_MESSAGE}\n")
    response = await orch.process(USER_MESSAGE)

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT).write_text(response)
    print(f"[S3] SurfSense:\n{response}")
    print(f"\n[S3] Saved → {OUTPUT}")
    return response


if __name__ == "__main__":
    asyncio.run(run())
