"""
Per-agent scoring functions for SurfSense agent-level evaluation.

Each function returns a dict of metric_name -> float | None.
None means "not applicable" for the given snapshot (e.g. safety compliance
when no unsafe hours exist in that scenario).
"""

from __future__ import annotations

import json as _json

_REQUIRED_RESEARCH_FIELDS = [
    "name", "latitude", "longitude", "break_type", "wave_direction",
    "bottom", "skill_minimum", "skill_recommended", "beginner_friendly",
    "hazards", "best_swell_direction", "description",
]

_SKILL_ORDER = ["beginner", "intermediate", "advanced", "expert"]

_VALID_RATINGS = {"ideal", "suitable", "challenging", "unsafe"}

_SKILL_BASE_THRESHOLDS: dict[str, dict[str, float]] = {
    "beginner":     {"max_wave_height": 1.5, "max_wind_speed": 15.0},
    "intermediate": {"max_wave_height": 2.5, "max_wind_speed": 20.0},
    "advanced":     {"max_wave_height": 5.0, "max_wind_speed": 30.0},
}

_RATING_RANK_ORDER = ["ideal", "suitable", "challenging", "unsafe"]


def score_research_agent(output: dict) -> dict[str, float | None]:
    """Score a research_agent output dict.

    Metrics
    -------
    field_completeness    : fraction of 12 key fields that are non-null
    coordinate_validity   : 1.0 if lat in [-90,90] and lon in [-180,180]
    hazard_coverage       : 1.0 if at least one hazard is listed
    skill_coherence       : 1.0 if skill_minimum ordinal <= skill_recommended
    """
    if not output or "error" in output:
        return {m: 0.0 for m in ("field_completeness", "coordinate_validity",
                                  "hazard_coverage", "skill_coherence")}

    present = sum(1 for f in _REQUIRED_RESEARCH_FIELDS if output.get(f) is not None)
    field_completeness = present / len(_REQUIRED_RESEARCH_FIELDS)

    lat = output.get("latitude")
    lon = output.get("longitude")
    coordinate_validity = 1.0 if (
        lat is not None and lon is not None
        and -90 <= lat <= 90 and -180 <= lon <= 180
    ) else 0.0

    hazards = output.get("hazards")
    hazard_coverage = 1.0 if isinstance(hazards, list) and hazards else 0.0

    skill_min = output.get("skill_minimum")
    skill_rec = output.get("skill_recommended")
    if skill_min in _SKILL_ORDER and skill_rec in _SKILL_ORDER:
        skill_coherence = 1.0 if _SKILL_ORDER.index(skill_min) <= _SKILL_ORDER.index(skill_rec) else 0.0
    else:
        skill_coherence = None

    return {
        "field_completeness": field_completeness,
        "coordinate_validity": coordinate_validity,
        "hazard_coverage": hazard_coverage,
        "skill_coherence": skill_coherence,
    }


def score_forecast_agent(
    forecast: dict,
    expected_hours: int,
) -> dict[str, float | None]:
    """Score a forecast_agent output dict (or snapshot standing in for it).

    Metrics
    -------
    field_completeness       : fraction of records with all 8 required sub-fields
    temporal_coverage        : records_count / expected_hours (capped at 1.0)
    value_sanity             : fraction of records with plausible numeric ranges
    wind_direction_presence  : fraction of records with wind.direction_deg present
    """
    _REQUIRED = [
        ("waves", "avg_m"), ("waves", "min_m"), ("waves", "max_m"),
        ("swell", "height_m"), ("swell", "period_s"), ("swell", "direction_deg"),
        ("wind", "speed_kph"), ("wind", "direction_deg"),
    ]

    forecasts = forecast.get("forecasts", [])
    if not forecasts:
        return {m: 0.0 for m in ("field_completeness", "temporal_coverage",
                                  "value_sanity", "wind_direction_presence")}

    complete = sum(
        1 for fc in forecasts
        if all(fc.get(grp, {}).get(fld) is not None for grp, fld in _REQUIRED)
    )
    field_completeness = complete / len(forecasts)

    temporal_coverage = min(len(forecasts) / max(expected_hours, 1), 1.0)

    sane = 0
    for fc in forecasts:
        waves = fc.get("waves", {}) or {}
        swell = fc.get("swell", {}) or {}
        wind  = fc.get("wind",  {}) or {}
        wave_ok   = 0 <= (waves.get("avg_m")    or 0) <= 15
        period_ok = 0 <= (swell.get("period_s") or 0) <= 30
        wind_ok   = 0 <= (wind.get("speed_kph") or 0) <= 200
        if wave_ok and period_ok and wind_ok:
            sane += 1
    value_sanity = sane / len(forecasts)

    has_dir = sum(
        1 for fc in forecasts
        if fc.get("wind", {}).get("direction_deg") is not None
    )
    wind_direction_presence = has_dir / len(forecasts)

    return {
        "field_completeness": field_completeness,
        "temporal_coverage": temporal_coverage,
        "value_sanity": value_sanity,
        "wind_direction_presence": wind_direction_presence,
    }


def score_condition_agent(
    assessments: list[dict],
    skill_level: str = "intermediate",
) -> dict[str, float | None]:
    """Score a condition_agent assess_conditions() output.

    Metrics
    -------
    rating_validity              : fraction of records with a valid rating word
    score_range_validity         : fraction of records with score in [0, 100]
    reasoning_presence           : fraction of records with non-empty reasoning
    safety_threshold_compliance  : fraction of genuinely-unsafe hours rated 'unsafe'
                                   (None when no unsafe hours exist in the scenario)
    rating_score_monotonicity    : 1.0 if mean(ideal) >= mean(suitable) >=
                                   mean(challenging) >= mean(unsafe) across present
                                   categories; None when fewer than 2 categories present
    """
    if not assessments or (len(assessments) == 1 and "error" in assessments[0]):
        return {m: 0.0 for m in ("rating_validity", "score_range_validity",
                                  "reasoning_presence", "safety_threshold_compliance",
                                  "rating_score_monotonicity")}

    valid_ratings = sum(1 for a in assessments if a.get("rating") in _VALID_RATINGS)
    rating_validity = valid_ratings / len(assessments)

    in_range = sum(
        1 for a in assessments
        if a.get("score") is not None and 0 <= a["score"] <= 100
    )
    score_range_validity = in_range / len(assessments)

    has_reasoning = sum(1 for a in assessments if a.get("reasoning"))
    reasoning_presence = has_reasoning / len(assessments)

    thresholds = _SKILL_BASE_THRESHOLDS.get(skill_level, _SKILL_BASE_THRESHOLDS["intermediate"])
    max_wave = thresholds["max_wave_height"]
    max_wind = thresholds["max_wind_speed"]

    genuinely_unsafe = [
        a for a in assessments
        if (a.get("wave_height_m") or 0) > max_wave * 1.5
        or (a.get("wind_speed_kph") or 0) > max_wind * 1.5
    ]
    if genuinely_unsafe:
        flagged = sum(1 for a in genuinely_unsafe if a.get("rating") == "unsafe")
        safety_threshold_compliance: float | None = flagged / len(genuinely_unsafe)
    else:
        safety_threshold_compliance = None

    by_rating: dict[str, list[float]] = {}
    for a in assessments:
        r = a.get("rating")
        s = a.get("score")
        if r in _VALID_RATINGS and s is not None:
            by_rating.setdefault(r, []).append(float(s))

    means = {r: sum(v) / len(v) for r, v in by_rating.items()}
    present = [r for r in _RATING_RANK_ORDER if r in means]

    if len(present) < 2:
        rating_score_monotonicity: float | None = None
    else:
        violations = sum(
            1 for i in range(len(present) - 1)
            if means[present[i]] < means[present[i + 1]]
        )
        rating_score_monotonicity = 1.0 if violations == 0 else 0.0

    return {
        "rating_validity": rating_validity,
        "score_range_validity": score_range_validity,
        "reasoning_presence": reasoning_presence,
        "safety_threshold_compliance": safety_threshold_compliance,
        "rating_score_monotonicity": rating_score_monotonicity,
    }


def score_trip_planning_agent(
    windows: list[dict],
    assessments: list[dict],
    min_hours: int = 2,
) -> dict[str, float | None]:
    """Score a trip_planning_agent find_surf_windows() output.

    Metrics
    -------
    window_detection        : 1.0 if windows found when suitable hours exist;
                              0.0 if suitable hours exist but no windows returned;
                              None when no suitable hours exist in the scenario
    window_score_ranking    : 1.0 if windows are sorted by avg_score descending
    suitable_hour_coverage  : fraction of suitable assessment hours covered by a window
    min_hours_respected     : fraction of windows that meet the min_hours threshold
    """
    suitable = [a for a in assessments if a.get("rating") in ("ideal", "suitable")]

    if not suitable:
        return {
            "window_detection": None,
            "window_score_ranking": None,
            "suitable_hour_coverage": None,
            "min_hours_respected": None,
        }

    if not windows:
        return {
            "window_detection": 0.0,
            "window_score_ranking": None,
            "suitable_hour_coverage": 0.0,
            "min_hours_respected": None,
        }

    window_detection = 1.0

    scores = [w.get("avg_score", 0) for w in windows]
    window_score_ranking = 1.0 if all(
        scores[i] >= scores[i + 1] for i in range(len(scores) - 1)
    ) else 0.0

    suitable_ts = {a.get("timestamp", "") for a in suitable}
    covered_ts: set[str] = set()
    for w in windows:
        w_start = w.get("start", "")
        w_end   = w.get("end", "")
        for a in suitable:
            ts = a.get("timestamp", "")
            if w_start <= ts <= w_end:
                covered_ts.add(ts)
    suitable_hour_coverage = len(covered_ts) / len(suitable_ts)

    ok = sum(1 for w in windows if (w.get("hours") or 0) >= min_hours)
    min_hours_respected = ok / len(windows)

    return {
        "window_detection": window_detection,
        "window_score_ranking": window_score_ranking,
        "suitable_hour_coverage": suitable_hour_coverage,
        "min_hours_respected": min_hours_respected,
    }


_UNSAFE_KEYWORDS = frozenset({
    "unsafe", "caution", "dangerous", "warning", "not recommended",
    "avoid", "too dangerous", "extreme", "risk", "hazardous",
})


def score_orchestrator(
    messages: list[dict],
    session_data: dict,
    skill_level: str,
) -> dict[str, float | None]:
    """Score the orchestrator's single-turn coherence.

    Metrics
    -------
    tool_sequence_valid          : 1.0 if research_spot called before fetch_forecast;
                                   None if fetch_forecast never called
    skill_level_passed_correctly : fraction of assess_conditions calls that pass the
                                   correct skill_level; None if never called
    unsafe_warning_present       : 1.0 if final response contains a safety warning when
                                   at least one assessment is rated 'unsafe';
                                   None when no unsafe assessments exist
    top_window_mentioned         : 1.0 if the top-ranked window's start timestamp
                                   (date or time substring) appears in the response;
                                   None when no windows were found
    """
    tool_calls_ordered: list[tuple[str, dict]] = []
    final_response = ""

    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"]
                try:
                    args = _json.loads(tc["function"]["arguments"])
                except Exception:
                    args = {}
                tool_calls_ordered.append((name, args))
        elif msg.get("content"):
            final_response = msg["content"]

    tool_names = [n for n, _ in tool_calls_ordered]

    # tool_sequence_valid
    if "fetch_forecast" not in tool_names:
        tool_sequence_valid: float | None = None
    elif "research_spot" not in tool_names:
        tool_sequence_valid = 0.0
    else:
        ri = tool_names.index("research_spot")
        fi = tool_names.index("fetch_forecast")
        tool_sequence_valid = 1.0 if ri < fi else 0.0

    # skill_level_passed_correctly
    assess_calls = [(n, a) for n, a in tool_calls_ordered if n == "assess_conditions"]
    if assess_calls:
        correct = sum(1 for _, a in assess_calls if a.get("skill_level") == skill_level)
        skill_level_passed_correctly: float | None = correct / len(assess_calls)
    else:
        skill_level_passed_correctly = None

    # unsafe_warning_present
    all_assessments: list[dict] = []
    for spot_data in session_data.values():
        all_assessments.extend(spot_data.get("assessments", []))

    has_unsafe = any(a.get("rating") == "unsafe" for a in all_assessments)
    if has_unsafe:
        lower = final_response.lower()
        unsafe_warning_present: float | None = 1.0 if any(kw in lower for kw in _UNSAFE_KEYWORDS) else 0.0
    else:
        unsafe_warning_present = None

    # top_window_mentioned
    best_window: dict | None = None
    best_score = -1.0
    for spot_data in session_data.values():
        for w in spot_data.get("windows", []):
            s = w.get("avg_score") or 0.0
            if s > best_score:
                best_score = s
                best_window = w

    if best_window:
        start = best_window.get("start", "")
        date_part = start[:10]
        time_part = start[11:16]
        mentioned = (date_part and date_part in final_response) or (time_part and time_part in final_response)
        top_window_mentioned: float | None = 1.0 if mentioned else 0.0
    else:
        top_window_mentioned = None

    return {
        "tool_sequence_valid": tool_sequence_valid,
        "skill_level_passed_correctly": skill_level_passed_correctly,
        "unsafe_warning_present": unsafe_warning_present,
        "top_window_mentioned": top_window_mentioned,
    }
