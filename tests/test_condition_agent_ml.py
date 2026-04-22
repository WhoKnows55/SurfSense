"""
Tests for ConditionAssessmentAgent in ML mode.

Verifies:
  1. Rule mode still works and passes existing behaviour.
  2. ML mode attaches feature_contributions to each record.
  3. Rating logic (70/45/1.5× thresholds) is unchanged in both modes.
  4. Model loading failure raises FileNotFoundError, not a silent error.
"""

import math
from unittest.mock import MagicMock, patch

import pytest

from config.settings import Settings
from app.agents.condition_agent import ConditionAssessmentAgent
from app.planning.scoring import derive_rating, rule_based_score


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _settings(mode: str = "rule", model_path: str = "ml/models/surf_condition_model.joblib"):
    s = Settings(
        _env_file=None,
        azure_openai={"endpoint": "", "api_key": ""},
    )
    s.scoring.scoring_mode  = mode
    s.scoring.ml_model_path = model_path
    return s


def _forecast(wave_avg=1.5, wind=12.0, swell_t=10.0, is_offshore=True):
    """Minimal forecast dict matching ForecastDataAgent output format."""
    return {
        "forecasts": [
            {
                "timestamp": "2026-06-15T10:00:00",
                "waves": {"min_m": wave_avg * 0.85, "max_m": wave_avg * 1.15, "avg_m": wave_avg},
                "swell": {
                    "height_m":    wave_avg * 0.8,
                    "period_s":    swell_t,
                    "direction":   "SW",
                    "direction_deg": 225.0,
                },
                "wind": {
                    "speed_kph":   wind,
                    "direction":   "NE",
                    "direction_deg": 45.0,
                    "is_offshore": is_offshore,
                    "is_light":    wind < 15,
                },
            }
        ]
    }


# ---------------------------------------------------------------------------
# Rule mode tests (regression — must not change existing behaviour)
# ---------------------------------------------------------------------------

class TestRuleMode:
    def test_rule_mode_produces_rating(self):
        agent = ConditionAssessmentAgent(_settings("rule"))
        result = agent.assess_conditions(_forecast(), skill_level="intermediate")
        assert len(result) == 1
        assert result[0]["rating"] in ("ideal", "suitable", "challenging", "unsafe")

    def test_rule_mode_no_feature_contributions(self):
        agent = ConditionAssessmentAgent(_settings("rule"))
        result = agent.assess_conditions(_forecast(), skill_level="intermediate")
        assert "feature_contributions" not in result[0]

    def test_rule_mode_unsafe_gate(self):
        # wave > max_wave * 1.5 → unsafe regardless of score
        agent = ConditionAssessmentAgent(_settings("rule"))
        result = agent.assess_conditions(
            _forecast(wave_avg=10.0),  # well above intermediate 2.5m limit
            skill_level="intermediate",
        )
        assert result[0]["rating"] == "unsafe"

    def test_rule_score_matches_scoring_module(self):
        agent = ConditionAssessmentAgent(_settings("rule"))
        fc = _forecast(wave_avg=1.5, wind=10.0, swell_t=12.0, is_offshore=True)
        result = agent.assess_conditions(fc, skill_level="intermediate")
        thresholds = agent._thresholds.get_thresholds("intermediate")
        expected = rule_based_score(1.5, 10.0, 12.0, True, thresholds)
        assert abs(result[0]["score"] - round(expected, 1)) < 0.1


# ---------------------------------------------------------------------------
# ML mode tests
# ---------------------------------------------------------------------------

class TestMLMode:
    def _make_mock_model(self, score: float = 72.0):
        mock = MagicMock()
        mock.predict.return_value = score
        mock.get_feature_contributions.return_value = {
            "swell_period": 8.5,
            "wind_speed": -3.2,
            "wave_height_avg": 4.1,
        }
        return mock

    def test_ml_mode_attaches_feature_contributions(self):
        agent = ConditionAssessmentAgent(_settings("ml"))
        with patch.object(agent, "_get_ml_model", return_value=self._make_mock_model()):
            result = agent.assess_conditions(_forecast(), skill_level="intermediate")
        assert "feature_contributions" in result[0]
        assert isinstance(result[0]["feature_contributions"], dict)
        assert len(result[0]["feature_contributions"]) > 0

    def test_ml_mode_rating_uses_deterministic_gate(self):
        """Rating must still be derived by derive_rating, not from ML score directly."""
        agent = ConditionAssessmentAgent(_settings("ml"))
        with patch.object(agent, "_get_ml_model", return_value=self._make_mock_model(72.0)):
            result = agent.assess_conditions(_forecast(), skill_level="intermediate")
        # score 72 + no unsafe trigger → rating should be 'ideal'
        assert result[0]["rating"] == "ideal"

    def test_ml_unsafe_gate_still_fires(self):
        """Even with a high ML score, 1.5× threshold triggers unsafe."""
        agent = ConditionAssessmentAgent(_settings("ml"))
        with patch.object(agent, "_get_ml_model", return_value=self._make_mock_model(95.0)):
            result = agent.assess_conditions(
                _forecast(wave_avg=10.0),  # 10m >> 2.5 * 1.5
                skill_level="intermediate",
            )
        assert result[0]["rating"] == "unsafe"

    def test_ml_model_not_found_raises(self):
        agent = ConditionAssessmentAgent(_settings("ml", "/nonexistent/model.joblib"))
        with pytest.raises(FileNotFoundError):
            agent.assess_conditions(_forecast(), skill_level="intermediate")

    def test_ml_falls_back_to_rule_if_fp_reconstruction_fails(self):
        """If ForecastPoint reconstruction fails, rule-based score is used (no crash)."""
        agent = ConditionAssessmentAgent(_settings("ml"))
        mock_model = self._make_mock_model()
        bad_forecast = {"forecasts": [{"timestamp": "", "waves": {}, "swell": {}, "wind": {}}]}
        with patch.object(agent, "_get_ml_model", return_value=mock_model):
            result = agent.assess_conditions(bad_forecast, skill_level="intermediate")
        # Should not raise; rating is one of the four categories
        assert result[0]["rating"] in ("ideal", "suitable", "challenging", "unsafe")


# ---------------------------------------------------------------------------
# derive_rating unit tests (shared between modes)
# ---------------------------------------------------------------------------

class TestDeriveRating:
    def _th(self):
        return {"max_wave_height": 2.5, "max_wind_speed": 20.0}

    def test_unsafe_wave_gate(self):
        assert derive_rating(95.0, 4.0, 10.0, self._th()) == "unsafe"

    def test_unsafe_wind_gate(self):
        assert derive_rating(95.0, 1.0, 35.0, self._th()) == "unsafe"

    def test_ideal(self):
        assert derive_rating(75.0, 1.5, 10.0, self._th()) == "ideal"

    def test_suitable(self):
        assert derive_rating(55.0, 1.5, 10.0, self._th()) == "suitable"

    def test_challenging(self):
        assert derive_rating(30.0, 1.5, 10.0, self._th()) == "challenging"
