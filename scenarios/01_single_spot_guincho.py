"""
Scenario 1: Single-Spot Condition Assessment – Praia do Guincho (beginner, 24 h).

Thesis anchor: Section 3.4.1, Scenario 1.

Drives the full orchestrated pipeline via a single natural user message:
  research_spot → fetch_forecast → assess_conditions → find_surf_windows

Output: scenarios/results/scenario_01_demo.txt

Usage:
    python -m scenarios.01_single_spot_guincho
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from app.core.llm_service import LLMService
from app.agents.orchestrator import Orchestrator

OUTPUT = "scenarios/results/scenario_01_demo.txt"

USER_MESSAGE = (
    "I'm a beginner surfer planning to surf Praia do Guincho today. "
    "Please check if the conditions are safe for my level, rate each hour "
    "as ideal, suitable, challenging, or unsafe, flag any unsafe windows, "
    "and tell me the best time to go. No need to ask for further details."
)


async def run() -> str:
    settings = Settings()
    llm = LLMService.from_settings(settings)
    orch = Orchestrator(llm, settings)

    print(f"[S1] User: {USER_MESSAGE}\n")
    response = await orch.process(USER_MESSAGE)

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT).write_text(response)
    print(f"[S1] SurfSense:\n{response}")
    print(f"\n[S1] Saved → {OUTPUT}")
    return response


if __name__ == "__main__":
    asyncio.run(run())
