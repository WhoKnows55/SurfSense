"""
Train/serve consistency contract for ForecastPointFeatureExtractor.

Verifies that transform_point and transform_row produce vectors of the same
length and identical values when given logically equivalent inputs.
"""

import math
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from app.forecasting.models import ForecastPoint, WaveData, SwellData, WindData
from app.ml.feature_extractor import FEATURE_NAMES, ForecastPointFeatureExtractor


EXTRACTOR = ForecastPointFeatureExtractor()

# Shared logical input values
_TS          = datetime(2026, 6, 15, 10, 0, 0)
_WAVE_H      = 1.5       # avg (point path uses min=0.85×, max=1.15×)
_SWELL_H     = 1.2
_SWELL_T     = 12.0
_SWELL_DIR   = 225.0     # SW
_WIND_S      = 18.0
_WIND_DIR    = 45.0      # NE
_SKILL       = "intermediate"


def _make_forecast_point() -> ForecastPoint:
    return ForecastPoint(
        timestamp=_TS,
        waves=WaveData(
            height_min=_WAVE_H * 0.85,
            height_max=_WAVE_H * 1.15,
        ),
        swell=SwellData(
            height=_SWELL_H,
            period=_SWELL_T,
            direction_degrees=_SWELL_DIR,
        ),
        wind=WindData(
            speed=_WIND_S,
            direction_degrees=_WIND_DIR,
        ),
    )


def _make_row() -> pd.Series:
    return pd.Series({
        "timestamp":         _TS,
        "wave_height_m":     _WAVE_H,
        "swell_height_m":    _SWELL_H,
        "swell_period_s":    _SWELL_T,
        "swell_direction_deg": _SWELL_DIR,
        "wind_speed_kph":    _WIND_S,
        "wind_gust_kph":     _WIND_S,
        "wind_direction_deg":_WIND_DIR,
        "tide_height_m":     0.0,
        "water_temp_c":      0.0,
        "air_temp_c":        0.0,
    })


class TestFeatureListContract:
    def test_feature_count_matches_constant(self):
        vec = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        assert len(vec) == len(FEATURE_NAMES)

    def test_row_feature_count_matches_constant(self):
        vec = EXTRACTOR.transform_row(_make_row(), _SKILL)
        assert len(vec) == len(FEATURE_NAMES)

    def test_no_duplicates_in_feature_names(self):
        assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES))


class TestTrainServeConsistency:
    """Both paths should produce the same vector for equivalent logical input."""

    def test_wave_height_avg_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        idx = FEATURE_NAMES.index("wave_height_avg")
        assert abs(vp[idx] - vr[idx]) < 1e-4

    def test_swell_height_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        idx = FEATURE_NAMES.index("swell_height")
        assert abs(vp[idx] - vr[idx]) < 1e-4

    def test_swell_period_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        idx = FEATURE_NAMES.index("swell_period")
        assert abs(vp[idx] - vr[idx]) < 1e-4

    def test_swell_dir_sin_cos_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        for feat in ("swell_dir_sin", "swell_dir_cos"):
            idx = FEATURE_NAMES.index(feat)
            assert abs(vp[idx] - vr[idx]) < 1e-4, f"{feat} mismatch"

    def test_wind_speed_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        idx = FEATURE_NAMES.index("wind_speed")
        assert abs(vp[idx] - vr[idx]) < 1e-4

    def test_wave_energy_proxy_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        idx = FEATURE_NAMES.index("wave_energy_proxy")
        expected = _SWELL_H ** 2 * _SWELL_T
        assert abs(vp[idx] - expected) < 1e-3
        assert abs(vr[idx] - expected) < 1e-3

    def test_skill_encoding_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        idx = FEATURE_NAMES.index("skill_level_encoded")
        assert vp[idx] == vr[idx] == 1.0  # intermediate = 1

    def test_temporal_features_consistent(self):
        vp = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        vr = EXTRACTOR.transform_row(_make_row(), _SKILL)
        for feat in ("hour_sin", "hour_cos", "month_sin", "month_cos", "day_of_week"):
            idx = FEATURE_NAMES.index(feat)
            assert abs(vp[idx] - vr[idx]) < 1e-4, f"{feat} mismatch"


class TestDtype:
    def test_point_returns_float32(self):
        vec = EXTRACTOR.transform_point(_make_forecast_point(), _SKILL)
        assert vec.dtype == np.float32

    def test_row_returns_float32(self):
        vec = EXTRACTOR.transform_row(_make_row(), _SKILL)
        assert vec.dtype == np.float32


class TestMissingValueHandling:
    def test_nan_in_row_defaults_to_zero(self):
        row = _make_row()
        row["tide_height_m"] = float("nan")
        vec = EXTRACTOR.transform_row(row, _SKILL)
        idx = FEATURE_NAMES.index("tide_height")
        assert vec[idx] == 0.0

    def test_none_in_row_defaults_to_zero(self):
        row = _make_row().to_dict()
        row["air_temp_c"] = None
        vec = EXTRACTOR.transform_row(pd.Series(row), _SKILL)
        idx = FEATURE_NAMES.index("air_temp")
        assert vec[idx] == 0.0
