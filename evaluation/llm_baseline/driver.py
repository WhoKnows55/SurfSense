"""
LLM baseline comparison driver (Section 3.5.2).

Sends identical prompts to three systems:
  1. SurfSense  – via Orchestrator.process()
  2. GPT-4o     – via Azure OpenAI (AZURE_OPENAI_* env vars, same deployment as orchestrator)
  3. Claude      – via anthropic.messages.create (temperature 0.7)

Three runs per system per scenario → 9 outputs per scenario.
All responses are cached to disk immediately; existing files are not re-queried
unless --force is passed.

Usage:
    python -m evaluation.llm_baseline.driver --scenario scenarios/snapshots/guincho_24h.json
    python -m evaluation.llm_baseline.driver --all
    python -m evaluation.llm_baseline.driver --all --force
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

RUNS_DIR  = Path("evaluation/llm_baseline/runs")
PROMPTS   = Path("evaluation/llm_baseline")
N_RUNS    = 3


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


def _call_claude(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text if msg.content else ""


async def _call_surfsense(snapshot_path: str, skill_level: str) -> str:
    from config.settings import Settings
    from app.core.llm_service import get_llm_provider
    from app.agents.orchestrator import Orchestrator

    settings = Settings()
    llm      = get_llm_provider(settings)
    orch     = Orchestrator(llm, settings)

    forecast = _load_snapshot(snapshot_path)
    spot     = forecast.get("spot", "Unknown")
    user_msg = (
        f"I'm a {skill_level} surfer. Please evaluate the conditions at {spot} "
        f"for every hour shown in the forecast and tell me the best windows."
    )
    return await orch.process(user_msg)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_scenario(
    snapshot_path: str,
    skill_level: str = "intermediate",
    force: bool = False,
) -> None:
    scenario_name = Path(snapshot_path).stem
    prompt = _build_prompt(snapshot_path, skill_level)
    phash  = _prompt_hash(prompt)

    for run_idx in range(1, N_RUNS + 1):
        for system in ("surfsense", "gpt4o", "claude"):
            out_dir  = RUNS_DIR / scenario_name / system
            out_path = out_dir / f"run_{run_idx}.txt"
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
                        _call_surfsense(snapshot_path, skill_level)
                    )
                elif system == "gpt4o":
                    response = _call_gpt(prompt)
                else:
                    response = _call_claude(prompt)

                out_path.write_text(response)
                print("done")
            except Exception as exc:
                out_path.write_text(f"ERROR: {exc}")
                print(f"error: {exc}")


def run_all(force: bool = False) -> None:
    snapshot_dir = Path("scenarios/snapshots")
    snapshots = list(snapshot_dir.glob("*.json"))
    if not snapshots:
        print("No snapshots found in scenarios/snapshots/. Run scenario scripts first.")
        return
    for snap in sorted(snapshots):
        print(f"\nScenario: {snap.name}")
        run_scenario(str(snap), force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=str, default=None,
                        help="Path to a specific snapshot JSON file")
    parser.add_argument("--all", action="store_true",
                        help="Run all snapshots in scenarios/snapshots/")
    parser.add_argument("--force", action="store_true",
                        help="Re-query even if output file exists")
    args = parser.parse_args()

    if args.scenario:
        run_scenario(args.scenario, force=args.force)
    elif args.all:
        run_all(force=args.force)
    else:
        parser.print_help()
