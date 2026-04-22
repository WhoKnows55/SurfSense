"""
LLM baseline scoring rubric (Section 3.5.2).

Scores each system's output on five dimensions:
  1. factual_consistency  – numerical claims match the forecast within 10 %
  2. safety_enforcement   – unsafe hours are explicitly flagged
  3. temporal_optimisation – at least one explicit time window identified
  4. consistency          – normalised edit distance across 3 runs
  5. explainability       – fraction of ratings that cite a specific number

Usage:
    python -m evaluation.llm_baseline.score
    # Writes evaluation/llm_baseline/results.csv
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import Levenshtein  # python-Levenshtein; install with: pip install python-Levenshtein

RUNS_DIR    = Path("evaluation/llm_baseline/runs")
RESULTS_CSV = Path("evaluation/llm_baseline/results.csv")
SNAPSHOTS   = Path("scenarios/snapshots")

_NUM_RE   = re.compile(r"(\d+(?:\.\d+)?)\s*(m|ft|kph|km/h|s)\b", re.IGNORECASE)
_RATING_RE = re.compile(r"\b(ideal|suitable|challenging|unsafe)\b", re.IGNORECASE)
_TIME_RE   = re.compile(r"\b(\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2})\b")


def _load_snapshot(scenario_name: str) -> dict:
    for path in SNAPSHOTS.glob("*.json"):
        if path.stem.startswith(scenario_name.split("_")[0]) or path.stem == scenario_name:
            with open(path) as f:
                return json.load(f)
    return {}


def _forecast_numbers(forecast: dict) -> list[tuple[float, str]]:
    """Extract (value, unit) pairs that appear in the forecast data."""
    nums = []
    for fc in forecast.get("forecasts", []):
        waves = fc.get("waves", {})
        swell = fc.get("swell", {})
        wind  = fc.get("wind",  {})
        if waves.get("avg_m"): nums.append((float(waves["avg_m"]), "m"))
        if swell.get("period_s"): nums.append((float(swell["period_s"]), "s"))
        if wind.get("speed_kph"):  nums.append((float(wind["speed_kph"]), "kph"))
    return nums


def score_factual_consistency(text: str, forecast: dict) -> float:
    """Proportion of numerical claims within 10 % of the nearest forecast value."""
    claims  = [(float(m.group(1)), m.group(2).lower()) for m in _NUM_RE.finditer(text)]
    sources = _forecast_numbers(forecast)
    if not claims:
        return 1.0  # no claims → no errors

    correct = 0
    for val, unit in claims:
        unit_norm = "kph" if unit in ("kph", "km/h") else unit
        candidates = [v for v, u in sources if u == unit_norm]
        if not candidates:
            correct += 1  # can't verify → benefit of the doubt
            continue
        nearest = min(candidates, key=lambda x: abs(x - val))
        if nearest == 0 or abs(val - nearest) / nearest <= 0.10:
            correct += 1
    return correct / len(claims)


def score_safety_enforcement(text: str, forecast: dict, skill_level: str = "intermediate") -> float:
    """Fraction of genuinely unsafe hours that are flagged in the output."""
    thresholds = {
        "beginner":     {"wave": 1.5, "wind": 15.0},
        "intermediate": {"wave": 2.5, "wind": 20.0},
        "advanced":     {"wave": 5.0, "wind": 30.0},
    }
    th = thresholds.get(skill_level, thresholds["intermediate"])
    unsafe_hours = [
        fc for fc in forecast.get("forecasts", [])
        if (fc.get("waves", {}).get("avg_m") or 0) > th["wave"] * 1.5
        or (fc.get("wind",  {}).get("speed_kph") or 0) > th["wind"] * 1.5
    ]
    if not unsafe_hours:
        return 1.0  # nothing to flag

    flagged = text.lower().count("unsafe")
    return min(float(flagged) / len(unsafe_hours), 1.0)


def score_temporal_optimisation(text: str) -> float:
    """1.0 if at least one explicit time window (start–end) is identified."""
    times = _TIME_RE.findall(text)
    return 1.0 if len(times) >= 2 else 0.0


def score_consistency(run_texts: list[str]) -> float:
    """Mean pairwise normalised similarity (1 − edit_distance / max_len) across runs."""
    if len(run_texts) < 2:
        return 1.0
    scores = []
    pairs = [(i, j) for i in range(len(run_texts)) for j in range(i + 1, len(run_texts))]
    for i, j in pairs:
        a, b = run_texts[i], run_texts[j]
        max_len = max(len(a), len(b), 1)
        dist    = Levenshtein.distance(a, b)
        scores.append(1.0 - dist / max_len)
    return sum(scores) / len(scores)


def score_explainability(text: str) -> float:
    """Fraction of rating statements that reference a specific number."""
    sentences = re.split(r"[.!?\n]", text)
    rating_sentences = [s for s in sentences if _RATING_RE.search(s)]
    if not rating_sentences:
        return 0.0
    with_number = [s for s in rating_sentences if _NUM_RE.search(s)]
    return len(with_number) / len(rating_sentences)


# ---------------------------------------------------------------------------
# Main scoring loop
# ---------------------------------------------------------------------------

def score_all() -> None:
    if not RUNS_DIR.exists():
        print("No run outputs found. Execute driver.py first.")
        return

    rows = []
    for scenario_dir in sorted(RUNS_DIR.iterdir()):
        if not scenario_dir.is_dir():
            continue
        scenario = scenario_dir.name
        forecast = _load_snapshot(scenario)

        for system_dir in sorted(scenario_dir.iterdir()):
            if not system_dir.is_dir():
                continue
            system = system_dir.name
            run_files = sorted(system_dir.glob("run_*.txt"))
            run_texts = [p.read_text() for p in run_files]
            if not run_texts:
                continue

            # Per-run scores (first 3)
            run_scores: dict[str, list[float]] = {dim: [] for dim in (
                "factual_consistency", "safety_enforcement",
                "temporal_optimisation", "explainability"
            )}
            for text in run_texts[:3]:
                run_scores["factual_consistency"].append(
                    score_factual_consistency(text, forecast)
                )
                run_scores["safety_enforcement"].append(
                    score_safety_enforcement(text, forecast)
                )
                run_scores["temporal_optimisation"].append(
                    score_temporal_optimisation(text)
                )
                run_scores["explainability"].append(
                    score_explainability(text)
                )

            consistency = score_consistency(run_texts[:3])

            for dim, run_vals in run_scores.items():
                mean_score = sum(run_vals) / len(run_vals) if run_vals else 0.0
                rows.append({
                    "scenario":  scenario,
                    "system":    system,
                    "dimension": dim,
                    "score":     round(mean_score, 4),
                    "run_1":     round(run_vals[0], 4) if len(run_vals) > 0 else "",
                    "run_2":     round(run_vals[1], 4) if len(run_vals) > 1 else "",
                    "run_3":     round(run_vals[2], 4) if len(run_vals) > 2 else "",
                })
            rows.append({
                "scenario":  scenario,
                "system":    system,
                "dimension": "consistency",
                "score":     round(consistency, 4),
                "run_1": "", "run_2": "", "run_3": "",
            })

    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["scenario","system","dimension","score","run_1","run_2","run_3"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows → {RESULTS_CSV}")


if __name__ == "__main__":
    score_all()
