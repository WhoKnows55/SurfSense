"""
SurfSense Condition Assessment Agent

Deterministic sub-agent that evaluates environmental conditions against
user skill levels to produce safety-aware quality assessments.

Wraps the existing ConditionAssessor from app/planning/condition_assessor.py.
"""

from typing import Any

from app.core.logger import LoggerMixin, get_logger
from app.forecasting.models import ForecastPoint
from app.planning.condition_assessor import ConditionAssessor, ConditionRating

logger = get_logger(__name__)


class ConditionAssessmentAgent(LoggerMixin):
    """Deterministic sub-agent for condition evaluation.

    Exposes tools for the orchestrator to:
    - assess_conditions: Score forecast points against skill thresholds
    - check_safety: Combine hazard data with condition assessment
    - get_skill_thresholds: Return configured thresholds
    """

    def __init__(self, settings):
        self._settings = settings
        self._thresholds = settings.skill_thresholds
        self._assessor = ConditionAssessor()

    def assess_conditions(
        self, forecast_data: dict, skill_level: str = "intermediate"
    ) -> list[dict]:
        """Score each forecast point against skill-level thresholds.

        Args:
            forecast_data: Unified forecast dict (from ForecastDataAgent).
            skill_level: User's surfing skill level.

        Returns:
            List of per-hour assessment dicts with rating, score, reasoning.
        """
        if "error" in forecast_data:
            return [{"error": forecast_data["error"]}]

        forecasts = forecast_data.get("forecasts", [])
        if not forecasts:
            return [{"error": "No forecast data available"}]

        thresholds = self._thresholds.get_thresholds(skill_level)
        results = []

        for fc in forecasts:
            waves = fc.get("waves", {})
            wind = fc.get("wind", {})
            swell = fc.get("swell", {})

            wave_avg = waves.get("avg_m") or waves.get("max_m") or 0
            wind_speed = wind.get("speed_kph", 0)
            swell_period = swell.get("period_s") or 0
            is_offshore = wind.get("is_offshore", False)

            # Deterministic scoring formula
            max_wave = thresholds["max_wave_height"]
            max_wind = thresholds["max_wind_speed"]

            # Wave score: ratio of wave height to max (capped at 1.0), weighted 40
            wave_score = min(wave_avg / max_wave, 1.0) * 40 if max_wave > 0 else 0

            # Swell period score: ratio to ideal (14s), weighted 30
            period_score = min(swell_period / 14, 1.0) * 30

            # Wind penalty: excess wind over threshold, weighted 20
            wind_penalty = max(0, (wind_speed - max_wind) / 10) * 20

            # Offshore bonus
            offshore_bonus = 10 if is_offshore else 0

            score = wave_score + period_score - wind_penalty + offshore_bonus
            score = max(0, min(100, score))

            # Map score to rating
            if (
                wind_speed > max_wind * 1.5
                or wave_avg > max_wave * 1.5
            ):
                rating = "unsafe"
            elif score >= 70:
                rating = "ideal"
            elif score >= 45:
                rating = "suitable"
            else:
                rating = "challenging"

            results.append(
                {
                    "timestamp": fc.get("timestamp", ""),
                    "rating": rating,
                    "score": round(score, 1),
                    "reasoning": self._build_reasoning(
                        wave_avg, wind_speed, swell_period, thresholds, rating
                    ),
                    "wave_height_m": wave_avg,
                    "wind_speed_kph": wind_speed,
                    "swell_period_s": swell_period,
                }
            )

        return results

    def check_safety(
        self,
        spot_name: str,
        forecast_data: dict,
        skill_level: str,
        safety_info: dict | None = None,
    ) -> dict:
        """Combine hazard data with condition assessment into a safety verdict.

        Args:
            spot_name: Name of the surf spot.
            forecast_data: Unified forecast dict.
            skill_level: User's surfing skill level.
            safety_info: Safety info from contextual layer (optional).

        Returns:
            Safety verdict with warnings.
        """
        if safety_info is None:
            safety_info = {}

        assessments = self.assess_conditions(forecast_data, skill_level)
        if assessments and "error" in assessments[0]:
            return {
                "spot_name": spot_name,
                "safe_overall": False,
                "error": assessments[0]["error"],
            }

        unsafe_count = sum(1 for a in assessments if a.get("rating") == "unsafe")
        warnings = list(safety_info.get("warnings", []))

        recommended = safety_info.get("recommended_skill_level")
        if recommended:
            skill_order = ["beginner", "intermediate", "advanced", "expert"]
            user_idx = (
                skill_order.index(skill_level)
                if skill_level in skill_order
                else 1
            )
            rec_idx = (
                skill_order.index(recommended)
                if recommended in skill_order
                else 1
            )
            if user_idx < rec_idx:
                warnings.append(
                    f"This spot is recommended for {recommended} surfers. "
                    f"Your level ({skill_level}) may be insufficient."
                )

        return {
            "spot_name": spot_name,
            "safe_overall": unsafe_count == 0 and len(warnings) == 0,
            "unsafe_hours": unsafe_count,
            "total_hours": len(assessments),
            "warnings": warnings,
            "hazards": safety_info.get("hazards", []),
        }

    def get_skill_thresholds(self, skill_level: str) -> dict:
        """Return configured thresholds for a skill level.

        Args:
            skill_level: beginner, intermediate, or advanced.

        Returns:
            Dict with max_wave_height and max_wind_speed.
        """
        return self._thresholds.get_thresholds(skill_level)

    @staticmethod
    def _build_reasoning(
        wave_avg: float,
        wind_speed: float,
        swell_period: float,
        thresholds: dict,
        rating: str,
    ) -> str:
        """Build human-readable reasoning for a condition rating."""
        parts = []

        max_wave = thresholds["max_wave_height"]
        max_wind = thresholds["max_wind_speed"]

        if wave_avg > max_wave:
            parts.append(
                f"Waves ({wave_avg:.1f}m) exceed limit ({max_wave}m)"
            )
        elif wave_avg > 0:
            parts.append(f"Waves {wave_avg:.1f}m within range")
        else:
            parts.append("No wave data")

        if wind_speed > max_wind:
            parts.append(
                f"Wind ({wind_speed:.0f}kph) too strong (max {max_wind}kph)"
            )
        elif wind_speed > 0:
            parts.append(f"Wind {wind_speed:.0f}kph acceptable")

        if swell_period >= 12:
            parts.append(f"Good swell period ({swell_period:.0f}s)")
        elif swell_period >= 8:
            parts.append(f"Decent swell period ({swell_period:.0f}s)")
        elif swell_period > 0:
            parts.append(f"Short swell period ({swell_period:.0f}s)")

        return "; ".join(parts) + f" → {rating}"

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        """Return OpenAI function-calling schemas for all tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "assess_conditions",
                    "description": (
                        "Evaluate surf conditions against a user's skill level. "
                        "Returns per-hour ratings (ideal/suitable/challenging/unsafe) "
                        "with scores and reasoning."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {
                                "type": "string",
                                "description": "Spot name (forecast must have been fetched first)",
                            },
                            "skill_level": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                                "description": "User's surfing skill level",
                            },
                        },
                        "required": ["spot_name", "skill_level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_safety",
                    "description": (
                        "Get a safety assessment for a spot, combining hazard data "
                        "with current conditions and user skill level."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {"type": "string"},
                            "skill_level": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                            },
                        },
                        "required": ["spot_name", "skill_level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_skill_thresholds",
                    "description": (
                        "Return the wave height and wind speed thresholds "
                        "for a given skill level."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skill_level": {
                                "type": "string",
                                "enum": ["beginner", "intermediate", "advanced"],
                            },
                        },
                        "required": ["skill_level"],
                    },
                },
            },
        ]
