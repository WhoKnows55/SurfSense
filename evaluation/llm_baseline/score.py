"""
LLM baseline scoring rubric (Section 3.5.2).

Scores each system's output on five dimensions:
  1. factual_consistency   numerical claims match the forecast within 10 %
  2. safety_enforcement    unsafe hours are explicitly flagged
                           (returns None when the snapshot has no unsafe
                           hours, since the metric is undefined in that
                           case; the previous early-exit returned 1.0,
                           which trivially passed any output)
  3. temporal_optimisation at least one explicit window with start AND end
                           (previous version returned 1.0 for any output
                           with two timestamps anywhere, so a copied
                           forecast table passed automatically)
  4. consistency           normalised edit distance across 3 runs
  5. explainability        fraction of ratings that cite a specific number

Patch notes (vs. the previous revision)
---------------------------------------
* `score_factual_consistency` now also extracts numeric claims from
  markdown tables whose column headers carry the unit (`Wave Height (m)`,
  `Wind Speed (kph)`). Without this, GPT-4o style outputs were scored
  almost entirely on the prose paragraph at the end of the response,
  which often echoed the prompt's injected safety thresholds.
* It also filters out claims that match those injected safety thresholds
  for the run's skill level, because echoing the prompt's own thresholds
  is not a factual claim about the forecast.
* `score_safety_enforcement` returns `None` (rendered as "N/A" in the
  CSV) when the snapshot contains no unsafe hours, instead of
  returning 1.0.
* `score_temporal_optimisation` now requires an explicit window
  (a labelled `Start:`/`End:` pair within a few lines, or an inline
  `X to Y` / `X - Y` range), rather than counting any two timestamps.

Usage:
    python -m evaluation.llm_baseline.score
    # Writes evaluation/llm_baseline/results.csv
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import Levenshtein  # python-Levenshtein

RUNS_DIR    = Path("evaluation/llm_baseline/runs")
RESULTS_CSV = Path("evaluation/llm_baseline/results.csv")
SNAPSHOTS   = Path("scenarios/snapshots")


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# Numbers with a unit suffix in prose ("1.5 m", "12 kph").
_NUM_RE   = re.compile(r"(\d+(?:\.\d+)?)\s*(m|ft|kph|km/h|s)\b", re.IGNORECASE)
_RATING_RE = re.compile(r"\b(ideal|suitable|challenging|unsafe)\b", re.IGNORECASE)
_TIME_RE   = re.compile(r"\b(\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}T\d{2}:\d{2})\b")

# Markdown-table column-header units: "Wave Height (m)" or "Wind Speed (kph)".
_HEADER_UNIT_RE = re.compile(
    r"\(\s*(m|ft|kph|km/h|s|meters?|metres?|seconds?|feet)\s*\)",
    re.IGNORECASE,
)
# Numeric cell content (no unit, optional whitespace, optional sign).
_NUMERIC_CELL_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*$")

# Window patterns: explicit start AND end.
# Time tokens we recognise: "12:00", "12:00:00", ISO timestamps, "6am" / "6 pm".
_TIME_TOKEN = (
    r"\d{1,2}:\d{2}(?::\d{2})?"
    r"|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?"
    r"|\d{1,2}\s*(?:am|pm)"
)
_WINDOW_RANGE_RE = re.compile(
    r"(" + _TIME_TOKEN + r")"
    r"\s*(?:to|until|through|\-|\u2013|\u2014)\s*"
    r"(" + _TIME_TOKEN + r")",
    re.IGNORECASE,
)
_START_RE = re.compile(r"\bstart\b\s*[:\-\*]", re.IGNORECASE)
_END_RE   = re.compile(r"\bend\b\s*[:\-\*]",   re.IGNORECASE)


# ---------------------------------------------------------------------------
# Skill-level thresholds
# These mirror driver.py exactly so we can detect prompt-injected echoes.
# ---------------------------------------------------------------------------

def _skill_unsafe_thresholds(skill_level: str) -> tuple[float, float]:
    """Return (unsafe_wave_m, unsafe_wind_kph) injected by the driver into
    the prompt's safety instruction. Must match driver._build_prompt().
    """
    base = {
        "beginner":     (1.5 * 1.5, 15.0 * 1.5),
        "intermediate": (2.5 * 1.5, 20.0 * 1.5),
        "advanced":     (5.0 * 1.5, 30.0 * 1.5),
    }
    return base.get(skill_level, base["intermediate"])


def _skill_base_thresholds(skill_level: str) -> tuple[float, float]:
    """Return (max_wave_m, max_wind_kph), the underlying classifier
    thresholds. Filtered out as well in case a model echoes them."""
    base = {
        "beginner":     (1.5, 15.0),
        "intermediate": (2.5, 20.0),
        "advanced":     (5.0, 30.0),
    }
    return base.get(skill_level, base["intermediate"])


def _is_threshold_echo(val: float, unit: str, skill_level: str) -> bool:
    """True if `(val, unit)` matches an injected threshold value
    (allowing for `.1f` / `.0f` rounding tolerance)."""
    unsafe_w, unsafe_k = _skill_unsafe_thresholds(skill_level)
    base_w,   base_k   = _skill_base_thresholds(skill_level)
    if unit == "m":
        if abs(val - unsafe_w) <= 0.15: return True
        if abs(val - base_w)   <= 0.05: return True
    if unit == "kph":
        if abs(val - unsafe_k) <= 1.5:  return True
        if abs(val - base_k)   <= 0.5:  return True
    return False


# ---------------------------------------------------------------------------
# Snapshot helpers
# ---------------------------------------------------------------------------

def _load_snapshot(scenario_name: str) -> dict:
    for path in SNAPSHOTS.glob("*.json"):
        if path.stem.startswith(scenario_name.split("_")[0]) or path.stem == scenario_name:
            with open(path) as f:
                return json.load(f)
    return {}


def _forecast_numbers(forecast: dict) -> list[tuple[float, str]]:
    """Extract `(value, unit)` pairs that appear in the forecast data."""
    nums: list[tuple[float, str]] = []
    for fc in forecast.get("forecasts", []):
        waves = fc.get("waves", {}) or {}
        swell = fc.get("swell", {}) or {}
        wind  = fc.get("wind",  {}) or {}
        if waves.get("avg_m"):     nums.append((float(waves["avg_m"]),     "m"))
        if swell.get("height_m"):  nums.append((float(swell["height_m"]),  "m"))
        if swell.get("period_s"):  nums.append((float(swell["period_s"]), "s"))
        if wind.get("speed_kph"):  nums.append((float(wind["speed_kph"]), "kph"))
    return nums


# ---------------------------------------------------------------------------
# Markdown-table claim extraction
# ---------------------------------------------------------------------------

def _normalise_unit(raw: str) -> str | None:
    raw = raw.strip().lower()
    if raw in ("m", "meter", "meters", "metre", "metres"): return "m"
    if raw in ("ft", "feet", "foot"):                      return "ft"
    if raw in ("kph", "km/h", "kmh"):                      return "kph"
    if raw in ("s", "sec", "secs", "second", "seconds"):   return "s"
    return None


def _extract_table_claims(text: str) -> list[tuple[float, str]]:
    """Extract numeric claims from any markdown tables in `text`.

    A table is detected as a header row starting with `|`, followed by a
    separator row containing `---`, followed by data rows. Units come from
    parenthesised qualifiers in the header cells.
    """
    claims: list[tuple[float, str]] = []
    lines = text.splitlines()

    i = 0
    while i < len(lines) - 1:
        header = lines[i].strip()
        sep    = lines[i + 1].strip() if i + 1 < len(lines) else ""

        is_table_start = (
            header.startswith("|")
            and sep.startswith("|")
            and "---" in sep
        )
        if not is_table_start:
            i += 1
            continue

        header_cells = [c.strip() for c in header.strip("|").split("|")]
        col_units: list[str | None] = []
        for cell in header_cells:
            m = _HEADER_UNIT_RE.search(cell)
            col_units.append(_normalise_unit(m.group(1)) if m else None)

        j = i + 2
        while j < len(lines):
            row = lines[j].strip()
            if not row.startswith("|") or "---" in row:
                break
            cells = [c.strip() for c in row.strip("|").split("|")]
            for col_idx, cell in enumerate(cells):
                if col_idx >= len(col_units) or col_units[col_idx] is None:
                    continue
                m = _NUMERIC_CELL_RE.match(cell)
                if m:
                    try:
                        claims.append((float(m.group(1)), col_units[col_idx]))
                    except ValueError:
                        pass
            j += 1
        i = j

    return claims


# ---------------------------------------------------------------------------
# Per-dimension scorers
# ---------------------------------------------------------------------------

def score_factual_consistency(
    text: str,
    forecast: dict,
    skill_level: str = "intermediate",
) -> float:
    """Proportion of numerical claims within 10 % of the nearest forecast
    value of the same unit.

    Claims are gathered from:
      * unit-suffixed prose (`1.5 m`, `12 kph`) via `_NUM_RE`
      * markdown-table cells whose column header carries a unit
        (`Wave Height (m)`, `Wind Speed (kph)`)

    Claims that match the prompt's injected safety thresholds for the
    given skill level are excluded, because echoing the prompt's own
    threshold values is not a factual claim about the forecast.
    """
    def _norm(u: str) -> str:
        u = u.lower()
        return "kph" if u in ("kph", "km/h", "kmh") else u

    prose_claims = [
        (float(m.group(1)), _norm(m.group(2)))
        for m in _NUM_RE.finditer(text)
    ]
    table_claims = [(v, _norm(u)) for v, u in _extract_table_claims(text)]

    combined = prose_claims + table_claims
    filtered = [
        (v, u) for v, u in combined
        if not _is_threshold_echo(v, u, skill_level)
    ]
    if not filtered:
        return 1.0  # no verifiable claims  no errors

    sources = _forecast_numbers(forecast)
    correct = 0
    for val, unit in filtered:
        candidates = [v for v, u in sources if u == unit]
        if not candidates:
            correct += 1  # can't verify  benefit of the doubt
            continue
        nearest = min(candidates, key=lambda x: abs(x - val))
        if nearest == 0 or abs(val - nearest) / nearest <= 0.10:
            correct += 1
    return correct / len(filtered)


def score_safety_enforcement(
    text: str,
    forecast: dict,
    skill_level: str = "intermediate",
) -> float | None:
    """Fraction of genuinely unsafe hours that are flagged in the output.

    Returns `None` when the snapshot contains no unsafe hours, since the
    metric is trivially undefined in that case (any output, including
    silence, would otherwise score 1.0). Callers should treat `None` as
    "not applicable" and exclude it from cross-scenario means.
    """
    base_w, base_k = _skill_base_thresholds(skill_level)
    unsafe_hours = [
        fc for fc in forecast.get("forecasts", [])
        if (fc.get("waves", {}).get("avg_m")    or 0) > base_w * 1.5
        or (fc.get("wind",  {}).get("speed_kph") or 0) > base_k * 1.5
    ]
    if not unsafe_hours:
        return None  # not applicable  no unsafe hours in this snapshot

    flagged = text.lower().count("unsafe")
    return min(float(flagged) / len(unsafe_hours), 1.0)


def score_temporal_optimisation(text: str) -> float:
    """1.0 if at least one explicit time window (start AND end) is identified.

    Two detection patterns:
      1. Inline range: "12:00 to 16:00", "6am - 10am", "X  Y", "X  Y".
      2. Labelled pair: a "Start: X" line followed by an "End: Y" line
         within the next 5 lines.

    A bare list of timestamps (such as the input forecast table copied
    into the response) does NOT score 1.0 unless it contains a clear
    range or a labelled start/end pair.
    """
    if _WINDOW_RANGE_RE.search(text):
        return 1.0

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _START_RE.search(line) and _TIME_RE.search(line):
            for j in range(i, min(i + 6, len(lines))):
                if _END_RE.search(lines[j]) and _TIME_RE.search(lines[j]):
                    return 1.0
    return 0.0


def score_consistency(run_texts: list[str]) -> float:
    """Mean pairwise normalised similarity (1  edit_distance / max_len)
    across runs."""
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


def _is_valid_output(text: str) -> bool:
    """Return False for outputs that contain no rating word and no time
    reference. Catches clarification requests and error messages that
    would otherwise inherit benefit-of-the-doubt scores."""
    return bool(_RATING_RE.search(text)) or bool(_TIME_RE.search(text))


def score_explainability(text: str) -> float:
    """Fraction of rating statements that reference a specific number.

    Looks at the rating line plus the two following lines for prose
    numbers, and additionally accepts a numeric cell appearing in the
    same markdown-table row as the rating.
    """
    lines = text.splitlines()
    rating_indices = [i for i, l in enumerate(lines) if _RATING_RE.search(l)]
    if not rating_indices:
        return 0.0

    with_number = 0
    for i in rating_indices:
        block = "\n".join(lines[i: i + 3])
        if _NUM_RE.search(block):
            with_number += 1
            continue
        # Fallback: rating in a markdown-table row with a numeric cell
        same_row = lines[i]
        if "|" in same_row:
            cells = [c.strip() for c in same_row.strip("|").split("|")]
            if any(_NUMERIC_CELL_RE.match(c) for c in cells):
                with_number += 1
                continue
    return with_number / len(rating_indices)


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _format_score(v: float | None) -> str:
    """Render a score for CSV output. None  'N/A'."""
    if v is None:
        return "N/A"
    return f"{round(v, 4)}"


def _safe_mean(vals: list) -> float | None:
    """Mean over non-None entries; None if all are None or list empty."""
    valid = [v for v in vals if v is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


# ---------------------------------------------------------------------------
# Main scoring loop
# ---------------------------------------------------------------------------

def score_all(skill_level: str = "intermediate") -> None:
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

            run_scores: dict[str, list] = {dim: [] for dim in (
                "factual_consistency", "safety_enforcement",
                "temporal_optimisation", "explainability"
            )}

            for text in run_texts[:3]:
                if not _is_valid_output(text):
                    # Clarification requests, error messages, or empty outputs
                    # must not receive benefit-of-the-doubt scores.
                    for dim in run_scores:
                        run_scores[dim].append(0.0)
                    continue
                run_scores["factual_consistency"].append(
                    score_factual_consistency(text, forecast, skill_level)
                )
                run_scores["safety_enforcement"].append(
                    score_safety_enforcement(text, forecast, skill_level)
                )
                run_scores["temporal_optimisation"].append(
                    score_temporal_optimisation(text)
                )
                run_scores["explainability"].append(
                    score_explainability(text)
                )

            consistency = score_consistency(run_texts[:3])

            for dim, run_vals in run_scores.items():
                mean_score = _safe_mean(run_vals)
                rows.append({
                    "scenario":  scenario,
                    "system":    system,
                    "dimension": dim,
                    "score":     _format_score(mean_score),
                    "run_1":     _format_score(run_vals[0]) if len(run_vals) > 0 else "",
                    "run_2":     _format_score(run_vals[1]) if len(run_vals) > 1 else "",
                    "run_3":     _format_score(run_vals[2]) if len(run_vals) > 2 else "",
                })
            rows.append({
                "scenario":  scenario,
                "system":    system,
                "dimension": "consistency",
                "score":     _format_score(consistency),
                "run_1": "", "run_2": "", "run_3": "",
            })

    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["scenario","system","dimension","score","run_1","run_2","run_3"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows  {RESULTS_CSV}")


if __name__ == "__main__":
    score_all()