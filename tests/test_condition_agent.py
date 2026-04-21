"""
Unit tests for ConditionAssessmentAgent.

Tests the deterministic scoring, safety evaluation, and threshold retrieval
without any LLM or external API calls.
"""

import pytest

from config.settings import Settings
from app.agents.condition_agent import ConditionAssessmentAgent


@pytest.fixture
def settings():
    """Create a Settings instance with defaults (no .env loaded)."""
    return Settings(
        _env_file=None,
        azure_openai={"endpoint": "", "api_key": ""},
    )


@pytest.fixture
def agent(settings):
    """Create a ConditionAssessmentAgent with default settings."""
    return ConditionAssessmentAgent(settings)


# -- Sample forecast data fixtures --

@pytest.fixture
def ideal_intermediate_forecast():
    """Forecast data that should be 'ideal' for intermediate surfers."""
    return {
        "spot": "Waikiki",
        "forecasts": [
            {
                "timestamp": "2026-03-15T08:00:00",
                "waves": {"min_m": 1.0, "max_m": 1.8, "avg_m": 1.5},
                "swell": {"height_m": 1.5, "period_s": 13, "direction": "SW"},
                "wind": {"speed_kph": 8, "direction": "N", "is_offshore": True, "is_light": True},
            },
        ],
    }


@pytest.fixture
def unsafe_beginner_forecast():
    """Forecast data that should be 'unsafe' for beginners."""
    return {
        "spot": "Pipeline",
        "forecasts": [
            {
                "timestamp": "2026-03-15T10:00:00",
                "waves": {"min_m": 3.0, "max_m": 4.5, "avg_m": 3.5},
                "swell": {"height_m": 3.5, "period_s": 14, "direction": "NW"},
                "wind": {"speed_kph": 25, "direction": "S", "is_offshore": False, "is_light": False},
            },
        ],
    }


@pytest.fixture
def multi_hour_forecast():
    """Multi-hour forecast with mixed conditions."""
    return {
        "spot": "Huntington Beach",
        "forecasts": [
            {
                "timestamp": "2026-03-15T06:00:00",
                "waves": {"avg_m": 1.2},
                "swell": {"period_s": 12},
                "wind": {"speed_kph": 5, "is_offshore": True},
            },
            {
                "timestamp": "2026-03-15T07:00:00",
                "waves": {"avg_m": 1.5},
                "swell": {"period_s": 12},
                "wind": {"speed_kph": 8, "is_offshore": True},
            },
            {
                "timestamp": "2026-03-15T12:00:00",
                "waves": {"avg_m": 1.8},
                "swell": {"period_s": 10},
                "wind": {"speed_kph": 35, "is_offshore": False},
            },
        ],
    }


# -- assess_conditions tests --

class TestAssessConditions:
    """Tests for ConditionAssessmentAgent.assess_conditions()."""

    def test_ideal_conditions_intermediate(self, agent, ideal_intermediate_forecast):
        """Ideal conditions should produce high scores and 'ideal' or 'suitable' rating."""
        results = agent.assess_conditions(ideal_intermediate_forecast, "intermediate")
        assert len(results) == 1
        r = results[0]
        assert r["rating"] in ("ideal", "suitable")
        assert r["score"] >= 45
        assert "timestamp" in r
        assert "reasoning" in r

    def test_unsafe_conditions_beginner(self, agent, unsafe_beginner_forecast):
        """Big waves + strong onshore wind should be unsafe for beginners."""
        results = agent.assess_conditions(unsafe_beginner_forecast, "beginner")
        assert len(results) == 1
        r = results[0]
        assert r["rating"] == "unsafe"

    def test_same_conditions_different_skill_levels(self, agent, unsafe_beginner_forecast):
        """Advanced surfers should rate the same conditions more favorably than beginners."""
        beginner = agent.assess_conditions(unsafe_beginner_forecast, "beginner")
        advanced = agent.assess_conditions(unsafe_beginner_forecast, "advanced")
        assert advanced[0]["score"] > beginner[0]["score"]

    def test_multi_hour_returns_all_hours(self, agent, multi_hour_forecast):
        """Should return one assessment per forecast point."""
        results = agent.assess_conditions(multi_hour_forecast, "intermediate")
        assert len(results) == 3

    def test_error_in_forecast_data(self, agent):
        """Error in forecast data should be propagated."""
        results = agent.assess_conditions({"error": "API failed"}, "intermediate")
        assert len(results) == 1
        assert "error" in results[0]

    def test_empty_forecasts(self, agent):
        """Empty forecast list should return error."""
        results = agent.assess_conditions({"forecasts": []}, "intermediate")
        assert len(results) == 1
        assert "error" in results[0]

    def test_offshore_wind_bonus(self, agent):
        """Offshore wind should boost score compared to onshore."""
        offshore = {
            "forecasts": [{
                "timestamp": "2026-03-15T08:00:00",
                "waves": {"avg_m": 1.5},
                "swell": {"period_s": 10},
                "wind": {"speed_kph": 10, "is_offshore": True},
            }]
        }
        onshore = {
            "forecasts": [{
                "timestamp": "2026-03-15T08:00:00",
                "waves": {"avg_m": 1.5},
                "swell": {"period_s": 10},
                "wind": {"speed_kph": 10, "is_offshore": False},
            }]
        }
        off_result = agent.assess_conditions(offshore, "intermediate")
        on_result = agent.assess_conditions(onshore, "intermediate")
        assert off_result[0]["score"] > on_result[0]["score"]

    def test_score_clamped_0_to_100(self, agent):
        """Score should always be between 0 and 100."""
        extreme = {
            "forecasts": [{
                "timestamp": "2026-03-15T08:00:00",
                "waves": {"avg_m": 10.0},
                "swell": {"period_s": 20},
                "wind": {"speed_kph": 60, "is_offshore": False},
            }]
        }
        results = agent.assess_conditions(extreme, "beginner")
        assert 0 <= results[0]["score"] <= 100


# -- check_safety tests --

class TestCheckSafety:
    """Tests for ConditionAssessmentAgent.check_safety()."""

    def test_safe_conditions(self, agent, ideal_intermediate_forecast):
        """Safe conditions should return safe_overall=True."""
        result = agent.check_safety(
            "Waikiki", ideal_intermediate_forecast, "intermediate"
        )
        assert result["spot_name"] == "Waikiki"
        assert result["safe_overall"] is True
        assert result["unsafe_hours"] == 0

    def test_unsafe_conditions(self, agent, unsafe_beginner_forecast):
        """Unsafe conditions should return safe_overall=False."""
        result = agent.check_safety(
            "Pipeline", unsafe_beginner_forecast, "beginner"
        )
        assert result["safe_overall"] is False
        assert result["unsafe_hours"] > 0

    def test_skill_level_warning_from_safety_info(self, agent, ideal_intermediate_forecast):
        """Should warn if spot recommends higher skill than user has."""
        safety_info = {
            "recommended_skill_level": "advanced",
            "hazards": ["reef", "currents"],
            "warnings": [],
        }
        result = agent.check_safety(
            "Pipeline", ideal_intermediate_forecast, "beginner", safety_info
        )
        assert len(result["warnings"]) > 0
        assert any("insufficient" in w.lower() for w in result["warnings"])

    def test_no_safety_info(self, agent, ideal_intermediate_forecast):
        """Should work without safety_info."""
        result = agent.check_safety(
            "Waikiki", ideal_intermediate_forecast, "intermediate"
        )
        assert "safe_overall" in result

    def test_hazards_passed_through(self, agent, ideal_intermediate_forecast):
        """Hazards from safety_info should appear in result."""
        safety_info = {"hazards": ["reef", "currents"], "warnings": []}
        result = agent.check_safety(
            "Waikiki", ideal_intermediate_forecast, "intermediate", safety_info
        )
        assert result["hazards"] == ["reef", "currents"]


# -- get_skill_thresholds tests --

class TestGetSkillThresholds:
    """Tests for ConditionAssessmentAgent.get_skill_thresholds()."""

    def test_beginner_thresholds(self, agent):
        t = agent.get_skill_thresholds("beginner")
        assert t["max_wave_height"] == 1.5
        assert t["max_wind_speed"] == 15.0

    def test_intermediate_thresholds(self, agent):
        t = agent.get_skill_thresholds("intermediate")
        assert t["max_wave_height"] == 2.5
        assert t["max_wind_speed"] == 20.0

    def test_advanced_thresholds(self, agent):
        t = agent.get_skill_thresholds("advanced")
        assert t["max_wave_height"] == 5.0
        assert t["max_wind_speed"] == 30.0

    def test_unknown_level_defaults_to_intermediate(self, agent):
        t = agent.get_skill_thresholds("pro")
        assert t == agent.get_skill_thresholds("intermediate")

    def test_thresholds_increase_with_skill(self, agent):
        b = agent.get_skill_thresholds("beginner")
        i = agent.get_skill_thresholds("intermediate")
        a = agent.get_skill_thresholds("advanced")
        assert b["max_wave_height"] < i["max_wave_height"] < a["max_wave_height"]
        assert b["max_wind_speed"] < i["max_wind_speed"] < a["max_wind_speed"]


# -- get_tool_definitions tests --

class TestToolDefinitions:
    """Tests for tool schema definitions."""

    def test_returns_three_tools(self):
        defs = ConditionAssessmentAgent.get_tool_definitions()
        assert len(defs) == 3

    def test_tool_names(self):
        defs = ConditionAssessmentAgent.get_tool_definitions()
        names = {d["function"]["name"] for d in defs}
        assert names == {"assess_conditions", "check_safety", "get_skill_thresholds"}

    def test_tool_schema_structure(self):
        defs = ConditionAssessmentAgent.get_tool_definitions()
        for d in defs:
            assert d["type"] == "function"
            assert "name" in d["function"]
            assert "description" in d["function"]
            assert "parameters" in d["function"]
            assert d["function"]["parameters"]["type"] == "object"
