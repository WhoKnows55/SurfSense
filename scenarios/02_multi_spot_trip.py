"""
Scenario 2: Multi-Spot Trip Planning – Ericeira, Peniche, Sagres (intermediate, 5 days).

Thesis anchor: Section 3.4.2, Scenario 2.

Drives the full orchestrated pipeline via a single natural user message:
  research_spot (×3) → fetch_forecast (×3) → assess_conditions (×3)
  → find_surf_windows (×3) → plan_itinerary

Output: scenarios/results/scenario_02_demo.txt

Usage:
    python -m scenarios.02_multi_spot_trip
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import Settings
from app.core.llm_service import LLMService
from app.agents.orchestrator import Orchestrator

OUTPUT = "scenarios/results/scenario_02_demo.txt"

USER_MESSAGE = (
    "I'm an intermediate surfer planning a 5-day surf trip along the Portuguese "
    "coastline starting today. Please check conditions at Ericeira, "
    "Peniche/Supertubos, and Sagres/Tonel, assess each spot for my skill level, "
    "flag any unsafe windows, and suggest the best day-by-day itinerary. "
    "No need to ask for further details."
)


async def run() -> str:
    settings = Settings()
    llm = LLMService.from_settings(settings)
    orch = Orchestrator(llm, settings)

    print(f"[S2] User: {USER_MESSAGE}\n")
    response = await orch.process(USER_MESSAGE)

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUTPUT).write_text(response)
    print(f"[S2] SurfSense:\n{response}")
    print(f"\n[S2] Saved → {OUTPUT}")
    return response


if __name__ == "__main__":
    asyncio.run(run())
