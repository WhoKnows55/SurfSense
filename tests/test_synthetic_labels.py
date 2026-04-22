"""
Tests for ml/labels.py – the physics-based synthetic label generator.

Verifies: purity (determinism), bounded output, non-degenerate distribution,
and structural independence from the rule-based scorer.
"""

import math
import random

import pandas as pd
import pytest

from ml.labels import (
    SPOT_REGISTRY,
    compute_synthetic_score,
    _wave_energy_subscore,
    _wind_alignment_subscore,
    _tidal_subscore,
    _period_quality_subscore,
)
from app.planning.scoring import rule_based_score


def _row(
    swell_h=1.5, swell_t=12.0, wind_s=15.0, wind_d=90.0,
    tide_h=0.5, spot_id="hossegor"
) -> dict:
    return {
        "swell_height_m":    swell_h,
        "swell_period_s":    swell_t,
        "wind_speed_kph":    wind_s,
        "wind_direction_deg":wind_d,
        "tide_height_m":     tide_h,
        "spot_id":           spot_id,
    }


class TestPureFunction:
    def test_same_input_same_output(self):
        r = _row()
        assert compute_synthetic_score(r) == compute_synthetic_score(r)

    def test_deterministic_across_many_calls(self):
        r = _row(swell_h=2.0, swell_t=14.0, wind_s=10.0, wind_d=270.0)
        first = compute_synthetic_score(r)
        for _ in range(10):
            assert compute_synthetic_score(r) == first


class TestBounds:
    def test_output_in_range(self):
        for _ in range(50):
            r = _row(
                swell_h=random.uniform(0, 4),
                swell_t=random.uniform(0, 20),
                wind_s=random.uniform(0, 60),
                wind_d=random.uniform(0, 359),
                tide_h=random.uniform(-1, 2),
            )
            score = compute_synthetic_score(r)
            assert 0.0 <= score <= 100.0, f"Out of bounds: {score}"

    def test_zero_swell_onshore_wind_gives_low_score(self):
        # hossegor: swell_facing=270, offshore_source=90 → wind from 270° is onshore
        score = compute_synthetic_score(_row(
            swell_h=0, swell_t=0,
            wind_s=30.0, wind_d=270.0,  # onshore for hossegor
            tide_h=2.0,                  # far from preferred 0.2m
            spot_id="hossegor",
        ))
        assert score < 5.0

    def test_excellent_conditions_give_high_score(self):
        # Big swell, long period, offshore wind, preferred tide
        spot = SPOT_REGISTRY["hossegor"]
        offshore_source = (spot["swell_facing_deg"] + 180) % 360  # wind FROM this direction
        r = _row(swell_h=2.5, swell_t=14.0, wind_s=10.0, wind_d=offshore_source,
                 tide_h=spot["preferred_tide_m"])
        assert compute_synthetic_score(r) >= 60.0


class TestNonDegenerateDistribution:
    """Score distribution should span a reasonable range (not stuck at 0 or 100)."""

    def _sample_scores(self, n: int = 200) -> list[float]:
        rng = random.Random(42)
        scores = []
        for _ in range(n):
            scores.append(compute_synthetic_score(_row(
                swell_h=rng.uniform(0.3, 3.5),
                swell_t=rng.uniform(5.0, 18.0),
                wind_s=rng.uniform(0, 40),
                wind_d=rng.uniform(0, 359),
                tide_h=rng.uniform(0, 1.5),
            )))
        return scores

    def test_mean_in_reasonable_range(self):
        scores = self._sample_scores()
        mean = sum(scores) / len(scores)
        assert 20.0 < mean < 80.0, f"Mean {mean:.1f} looks degenerate"

    def test_std_above_threshold(self):
        import statistics
        scores = self._sample_scores()
        std = statistics.stdev(scores)
        assert std > 5.0, f"Std {std:.1f} too low — label may be degenerate"


class TestSubScores:
    def test_wave_energy_increases_with_height(self):
        assert _wave_energy_subscore(2.0, 10.0) > _wave_energy_subscore(1.0, 10.0)

    def test_wave_energy_increases_with_period(self):
        assert _wave_energy_subscore(1.5, 14.0) > _wave_energy_subscore(1.5, 8.0)

    def test_wave_energy_capped_at_40(self):
        assert _wave_energy_subscore(100.0, 100.0) <= 40.0

    def test_wind_alignment_offshore_higher_than_onshore(self):
        swell_facing = 270.0
        offshore_source = 90.0   # wind blowing from 90° is offshore for W-facing beach
        onshore_source  = 270.0  # wind from 270° is onshore
        assert (
            _wind_alignment_subscore(10.0, offshore_source, swell_facing)
            > _wind_alignment_subscore(10.0, onshore_source, swell_facing)
        )

    def test_tidal_peaks_at_preferred(self):
        preferred = 0.5
        sigma = 0.4
        at_pref  = _tidal_subscore(preferred, preferred, sigma)
        off_pref = _tidal_subscore(preferred + sigma * 2, preferred, sigma)
        assert at_pref > off_pref

    def test_period_quality_monotone_up_to_14s(self):
        periods = [5.0, 8.0, 10.0, 12.0, 14.0]
        scores  = [_period_quality_subscore(p) for p in periods]
        for a, b in zip(scores, scores[1:]):
            assert a <= b, f"Non-monotone: {a} > {b}"

    def test_period_quality_flat_above_14s(self):
        assert _period_quality_subscore(14.0) == _period_quality_subscore(18.0)


class TestStructuralIndependenceFromRuleBased:
    """The synthetic label must have a different structure from rule_based_score.

    A simple consistency check: there must exist inputs where the two formulas
    produce substantially different relative rankings.  This is a necessary
    (not sufficient) condition for independence.
    """

    def test_rankings_differ_on_contrasting_inputs(self):
        # Case A: high wave energy, poor wind alignment
        a = _row(swell_h=2.5, swell_t=14.0, wind_s=5.0, wind_d=270.0, spot_id="hossegor")
        # Case B: moderate wave, offshore wind, long period
        b = _row(swell_h=1.0, swell_t=12.0, wind_s=8.0, wind_d=90.0,  spot_id="hossegor")

        synthetic_a = compute_synthetic_score(a)
        synthetic_b = compute_synthetic_score(b)

        thresholds = {"max_wave_height": 2.5, "max_wind_speed": 20.0}
        rule_a = rule_based_score(a["swell_height_m"], a["wind_speed_kph"],
                                  a["swell_period_s"], False, thresholds)
        rule_b = rule_based_score(b["swell_height_m"], b["wind_speed_kph"],
                                  b["swell_period_s"], True,  thresholds)

        synthetic_wins_a = synthetic_a > synthetic_b
        rule_wins_a      = rule_a      > rule_b
        # At least one of these orderings should differ
        assert synthetic_wins_a != rule_wins_a, (
            "Synthetic and rule-based produce identical relative rankings on these inputs — "
            "they may not be structurally independent enough."
        )
