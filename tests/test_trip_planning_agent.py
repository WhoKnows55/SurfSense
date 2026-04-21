"""
Unit tests for TripPlanningAgent.

Tests the deterministic window-finding, itinerary planning, and spot ranking
without any LLM or external API calls.
"""

import pytest

from app.agents.trip_planning_agent import TripPlanningAgent


@pytest.fixture
def agent():
    return TripPlanningAgent()


# -- Sample assessment fixtures --

@pytest.fixture
def good_assessments():
    """Consecutive hours of ideal/suitable conditions."""
    return [
        {"timestamp": "2026-03-15T06:00:00", "rating": "ideal", "score": 85.0},
        {"timestamp": "2026-03-15T07:00:00", "rating": "ideal", "score": 80.0},
        {"timestamp": "2026-03-15T08:00:00", "rating": "suitable", "score": 60.0},
        {"timestamp": "2026-03-15T09:00:00", "rating": "suitable", "score": 55.0},
        {"timestamp": "2026-03-15T10:00:00", "rating": "challenging", "score": 30.0},
        {"timestamp": "2026-03-15T11:00:00", "rating": "unsafe", "score": 10.0},
        {"timestamp": "2026-03-15T14:00:00", "rating": "suitable", "score": 50.0},
        {"timestamp": "2026-03-15T15:00:00", "rating": "ideal", "score": 75.0},
        {"timestamp": "2026-03-15T16:00:00", "rating": "suitable", "score": 55.0},
    ]


@pytest.fixture
def all_unsuitable():
    """All hours are challenging or unsafe."""
    return [
        {"timestamp": "2026-03-15T06:00:00", "rating": "challenging", "score": 30.0},
        {"timestamp": "2026-03-15T07:00:00", "rating": "unsafe", "score": 10.0},
        {"timestamp": "2026-03-15T08:00:00", "rating": "challenging", "score": 25.0},
    ]


# -- find_surf_windows tests --

class TestFindSurfWindows:
    """Tests for TripPlanningAgent.find_surf_windows()."""

    def test_finds_consecutive_windows(self, agent, good_assessments):
        """Should group consecutive ideal/suitable hours into windows."""
        windows = agent.find_surf_windows(good_assessments)
        assert len(windows) >= 1
        # First window should be the 4 morning hours (06-09)
        morning = [w for w in windows if w["hours"] >= 3]
        assert len(morning) >= 1

    def test_window_has_required_fields(self, agent, good_assessments):
        """Each window should have start, end, avg_score, hours."""
        windows = agent.find_surf_windows(good_assessments)
        assert len(windows) > 0
        for w in windows:
            assert "start" in w
            assert "end" in w
            assert "avg_score" in w
            assert "hours" in w

    def test_min_hours_filter(self, agent, good_assessments):
        """Windows shorter than min_hours should be excluded."""
        # With min_hours=5, no window should be long enough
        windows = agent.find_surf_windows(good_assessments, min_hours=5)
        for w in windows:
            assert w["hours"] >= 5

    def test_empty_assessments(self, agent):
        """Empty input should return empty list."""
        assert agent.find_surf_windows([]) == []

    def test_error_assessments(self, agent):
        """Error assessments should return empty list."""
        assert agent.find_surf_windows([{"error": "no data"}]) == []

    def test_no_suitable_hours(self, agent, all_unsuitable):
        """All challenging/unsafe should return no windows."""
        windows = agent.find_surf_windows(all_unsuitable)
        assert windows == []

    def test_sorted_by_score(self, agent, good_assessments):
        """Windows should be sorted by avg_score descending."""
        windows = agent.find_surf_windows(good_assessments, min_hours=2)
        if len(windows) > 1:
            assert windows[0]["avg_score"] >= windows[1]["avg_score"]

    def test_peak_score_present(self, agent, good_assessments):
        """Each window should include peak_score."""
        windows = agent.find_surf_windows(good_assessments)
        for w in windows:
            assert "peak_score" in w
            assert w["peak_score"] >= w["avg_score"]


# -- plan_itinerary tests --

class TestPlanItinerary:
    """Tests for TripPlanningAgent.plan_itinerary()."""

    def test_basic_itinerary(self, agent):
        """Should produce a day-by-day schedule."""
        spots_data = {
            "Waikiki": {
                "windows": [
                    {"start": "2026-03-15T07:00:00", "end": "2026-03-15T10:00:00", "avg_score": 75.0, "hours": 3},
                ],
                "coordinates": {"lat": 21.2766, "lon": -157.8278},
            },
        }
        result = agent.plan_itinerary(spots_data, days=1, skill_level="intermediate")
        assert len(result["days"]) == 1
        assert result["days"][0]["spot"] == "Waikiki"

    def test_multi_spot_itinerary(self, agent):
        """Should pick best spot per day."""
        spots_data = {
            "Waikiki": {
                "windows": [
                    {"start": "2026-03-15T07:00:00", "end": "2026-03-15T10:00:00", "avg_score": 60.0, "hours": 3},
                ],
                "coordinates": {"lat": 21.2766, "lon": -157.8278},
            },
            "Pipeline": {
                "windows": [
                    {"start": "2026-03-15T08:00:00", "end": "2026-03-15T11:00:00", "avg_score": 85.0, "hours": 3},
                ],
                "coordinates": {"lat": 21.6650, "lon": -158.0539},
            },
        }
        result = agent.plan_itinerary(spots_data, days=1, skill_level="advanced")
        assert result["days"][0]["spot"] == "Pipeline"

    def test_empty_spots_data(self, agent):
        """No spots should produce empty itinerary."""
        result = agent.plan_itinerary({}, days=2, skill_level="intermediate")
        assert result["days"] == []
        assert result["total_score"] == 0

    def test_travel_distance_computed(self, agent):
        """Travel distance should be computed between spots."""
        spots_data = {
            "Waikiki": {
                "windows": [
                    {"start": "2026-03-15T07:00:00", "avg_score": 70.0, "hours": 3},
                ],
                "coordinates": {"lat": 21.2766, "lon": -157.8278},
            },
        }
        base = {"lat": 21.3, "lon": -157.8}
        result = agent.plan_itinerary(
            spots_data, days=1, skill_level="intermediate", base_coords=base
        )
        assert result["days"][0]["travel_km"] >= 0

    def test_total_score_and_travel(self, agent):
        """total_score and total_travel_km should be aggregates."""
        spots_data = {
            "Spot A": {
                "windows": [{"start": "2026-03-15T07:00:00", "avg_score": 60.0, "hours": 3}],
                "coordinates": {"lat": 0.0, "lon": 0.0},
            },
        }
        result = agent.plan_itinerary(spots_data, days=1, skill_level="intermediate")
        assert result["total_score"] == 60.0
        assert "total_travel_km" in result


# -- rank_spots tests --

class TestRankSpots:
    """Tests for TripPlanningAgent.rank_spots()."""

    def test_basic_ranking(self, agent):
        """Spots should be ranked by avg_score descending."""
        spot_assessments = {
            "Spot A": [
                {"score": 50, "rating": "suitable"},
                {"score": 40, "rating": "challenging"},
            ],
            "Spot B": [
                {"score": 80, "rating": "ideal"},
                {"score": 70, "rating": "ideal"},
            ],
        }
        ranked = agent.rank_spots(spot_assessments)
        assert len(ranked) == 2
        assert ranked[0]["spot"] == "Spot B"
        assert ranked[1]["spot"] == "Spot A"

    def test_counts_rating_categories(self, agent):
        """Should count ideal, suitable, unsafe hours."""
        spot_assessments = {
            "Spot A": [
                {"score": 80, "rating": "ideal"},
                {"score": 60, "rating": "suitable"},
                {"score": 10, "rating": "unsafe"},
            ],
        }
        ranked = agent.rank_spots(spot_assessments)
        assert ranked[0]["ideal_hours"] == 1
        assert ranked[0]["suitable_hours"] == 1
        assert ranked[0]["unsafe_hours"] == 1

    def test_skips_error_assessments(self, agent):
        """Should skip spots with error assessments."""
        spot_assessments = {
            "Good Spot": [{"score": 70, "rating": "ideal"}],
            "Bad Spot": [{"error": "no data"}],
        }
        ranked = agent.rank_spots(spot_assessments)
        assert len(ranked) == 1
        assert ranked[0]["spot"] == "Good Spot"

    def test_empty_input(self, agent):
        """Empty input should return empty list."""
        assert agent.rank_spots({}) == []


# -- haversine tests --

class TestHaversine:
    """Tests for TripPlanningAgent._haversine()."""

    def test_same_point_zero_distance(self, agent):
        """Same coordinates should return 0."""
        coord = {"lat": 21.3, "lon": -157.8}
        assert agent._haversine(coord, coord) == pytest.approx(0.0, abs=0.1)

    def test_known_distance(self, agent):
        """Waikiki to Pipeline should be roughly 45-55 km."""
        waikiki = {"lat": 21.2766, "lon": -157.8278}
        pipeline = {"lat": 21.6650, "lon": -158.0539}
        dist = agent._haversine(waikiki, pipeline)
        assert 40 < dist < 60

    def test_long_distance(self, agent):
        """Hawaii to Sydney should be roughly 8000-9000 km."""
        hawaii = {"lat": 21.3, "lon": -157.8}
        sydney = {"lat": -33.9, "lon": 151.2}
        dist = agent._haversine(hawaii, sydney)
        assert 8000 < dist < 9000


# -- tool definitions tests --

class TestToolDefinitions:
    """Tests for tool schema definitions."""

    def test_returns_three_tools(self):
        defs = TripPlanningAgent.get_tool_definitions()
        assert len(defs) == 3

    def test_tool_names(self):
        defs = TripPlanningAgent.get_tool_definitions()
        names = {d["function"]["name"] for d in defs}
        assert names == {"find_surf_windows", "plan_itinerary", "rank_spots"}

    def test_tool_schema_structure(self):
        defs = TripPlanningAgent.get_tool_definitions()
        for d in defs:
            assert d["type"] == "function"
            assert "name" in d["function"]
            assert "description" in d["function"]
            assert "parameters" in d["function"]
