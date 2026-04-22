"""
Unit tests for ForecastDataAgent.

Tests spot lookup, caching, forecast-to-dict conversion, and tool definitions.
Async methods are tested with pytest-asyncio.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from config.settings import Settings
from app.agents.forecast_data_agent import ForecastDataAgent
from app.forecasting.models import (
    Coordinates,
    ForecastResponse,
    ForecastPoint,
    SpotMetadata,
    WaveData,
    SwellData,
    WindData,
    DataSource,
)


@pytest.fixture
def settings():
    """Create a Settings instance with defaults (no .env loaded)."""
    return Settings(
        _env_file=None,
        azure_openai={"endpoint": "", "api_key": ""},
    )


@pytest.fixture
def agent(settings):
    """Create a ForecastDataAgent with default settings."""
    return ForecastDataAgent(settings)


# Sample research data to inject
SAMPLE_RESEARCH = {
    "name": "Pipeline",
    "latitude": 21.6650,
    "longitude": -158.0539,
    "region": "North Shore",
    "country": "USA",
    "timezone": "Pacific/Honolulu",
    "break_type": "reef",
    "hazards": ["shallow reef", "strong currents"],
    "skill_minimum": "advanced",
    "skill_recommended": "expert",
    "description": "Famous Hawaiian reef break",
}


# -- Spot coordinate lookup tests --

class TestSpotCoordinateLookup:
    """Tests for ForecastDataAgent._get_spot_coordinates()."""

    def test_researched_spot_lookup(self, agent):
        """Spots with injected research data should return coordinates."""
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        coords = agent._get_spot_coordinates("Pipeline")
        assert coords is not None
        assert abs(coords.latitude - 21.665) < 0.1

    def test_case_insensitive_lookup(self, agent):
        """Research data lookup should be case-insensitive."""
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        coords = agent._get_spot_coordinates("pipeline")
        assert coords is not None

    def test_unknown_spot_returns_none(self, agent):
        """Unknown spots (not researched) should return None."""
        coords = agent._get_spot_coordinates("Nonexistent Beach XYZ")
        assert coords is None


# -- Caching tests --

class TestForecastCaching:
    """Tests for forecast caching behavior."""

    def test_cache_stores_and_retrieves(self, agent):
        """Cached forecast should be retrievable."""
        data = {"spot": "Pipeline", "forecasts": []}
        agent._cache_forecast("Pipeline", data)
        cached = agent._get_cached_forecast("Pipeline")
        assert cached is not None
        assert cached["spot"] == "Pipeline"

    def test_cache_miss_returns_none(self, agent):
        """Non-cached spot should return None."""
        assert agent._get_cached_forecast("Unknown Spot") is None

    def test_cache_expiry(self, agent):
        """Expired cache entries should be evicted."""
        data = {"spot": "Pipeline", "forecasts": []}
        agent._cache_forecast("Pipeline", data)
        # Manually backdate the cache entry
        agent._forecast_cache["pipeline"]["_cached_at"] = (
            datetime.utcnow() - timedelta(hours=2)
        )
        assert agent._get_cached_forecast("Pipeline") is None

    def test_cache_key_normalized(self, agent):
        """Cache keys should be case-insensitive."""
        data = {"spot": "Pipeline", "forecasts": []}
        agent._cache_forecast("Pipeline", data)
        assert agent._get_cached_forecast("pipeline") is not None
        assert agent._get_cached_forecast("PIPELINE") is not None


# -- forecast_to_dict tests --

class TestForecastToDict:
    """Tests for ForecastDataAgent._forecast_to_dict()."""

    def _make_forecast_response(self):
        """Create a minimal ForecastResponse for testing."""
        spot = SpotMetadata(
            name="Waikiki",
            coordinates=Coordinates(latitude=21.2766, longitude=-157.8278),
        )
        point = ForecastPoint(
            timestamp=datetime(2026, 3, 15, 8, 0, 0),
            waves=WaveData(height_min=1.0, height_max=1.8),
            swell=SwellData(height=1.5, period=12.0, direction_degrees=225.0),
            wind=WindData(speed=10.0, direction_degrees=45.0),
        )
        return ForecastResponse(
            spot=spot,
            source=DataSource.OPEN_METEO,
            forecasts=[point],
        )

    def test_converts_to_dict(self, agent):
        """Should produce a dict with expected top-level keys."""
        fr = self._make_forecast_response()
        d = agent._forecast_to_dict(fr)
        assert d["spot"] == "Waikiki"
        assert "coordinates" in d
        assert d["coordinates"]["lat"] == pytest.approx(21.2766)
        assert "forecasts" in d
        assert len(d["forecasts"]) == 1

    def test_forecast_point_fields(self, agent):
        """Each forecast point should have waves, swell, wind dicts."""
        fr = self._make_forecast_response()
        d = agent._forecast_to_dict(fr)
        fc = d["forecasts"][0]
        assert "waves" in fc
        assert "swell" in fc
        assert "wind" in fc
        assert "timestamp" in fc


# -- fetch_forecast tests (mocked) --

class TestFetchForecast:
    """Tests for ForecastDataAgent.fetch_forecast() with mocked API."""

    @pytest.mark.asyncio
    async def test_unknown_spot_returns_error(self, agent):
        """Unknown (unresearched) spot should return error dict."""
        result = await agent.fetch_forecast("Nonexistent Beach XYZ")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_returns_cached_if_available(self, agent):
        """Should return cached data without calling APIs."""
        cached = {"spot": "Pipeline", "forecasts": [{"timestamp": "..."}]}
        agent._cache_forecast("Pipeline", cached)
        result = await agent.fetch_forecast("Pipeline")
        assert result["spot"] == "Pipeline"

    @pytest.mark.asyncio
    async def test_openmeteo_called_first(self, agent):
        """Open-Meteo should be the primary source (thesis Section 3.3.3)."""
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        mock_response = MagicMock()
        mock_response.spot.name = "Pipeline"
        mock_response.spot.coordinates.latitude = 21.665
        mock_response.spot.coordinates.longitude = -158.054
        mock_response.source.value = "open-meteo"
        mock_response.fetched_at.isoformat.return_value = "2026-01-01T00:00:00"
        mock_response.forecasts = []
        with patch.object(agent._openmeteo_client, "get_forecast", new_callable=AsyncMock, return_value=mock_response) as om_mock, \
             patch.object(agent._stormglass_client, "get_forecast", new_callable=AsyncMock) as sg_mock:
            result = await agent.fetch_forecast("Pipeline")
            om_mock.assert_called_once()
            sg_mock.assert_not_called()
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_stormglass_fallback_on_openmeteo_failure(self, agent):
        """Stormglass should be tried when Open-Meteo raises."""
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        mock_response = MagicMock()
        mock_response.spot.name = "Pipeline"
        mock_response.spot.coordinates.latitude = 21.665
        mock_response.spot.coordinates.longitude = -158.054
        mock_response.source.value = "stormglass"
        mock_response.fetched_at.isoformat.return_value = "2026-01-01T00:00:00"
        mock_response.forecasts = []
        with patch.object(agent._openmeteo_client, "get_forecast", side_effect=Exception("Open-Meteo down")), \
             patch.object(type(agent._stormglass_client), "is_configured", new_callable=PropertyMock, return_value=True), \
             patch.object(agent._stormglass_client, "get_forecast", new_callable=AsyncMock, return_value=mock_response) as sg_mock:
            result = await agent.fetch_forecast("Pipeline")
            sg_mock.assert_called_once()
            assert "error" not in result

    @pytest.mark.asyncio
    async def test_api_failure_returns_error(self, agent):
        """Both providers failing (or unavailable) should return error dict, not raise."""
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        with patch.object(agent._openmeteo_client, "get_forecast", side_effect=Exception("API down")), \
             patch.object(type(agent._stormglass_client), "is_configured", new_callable=PropertyMock, return_value=False):
            result = await agent.fetch_forecast("Pipeline")
            assert "error" in result


# -- get_spot_metadata tests --

class TestGetSpotMetadata:
    """Tests for ForecastDataAgent.get_spot_metadata()."""

    @pytest.mark.asyncio
    async def test_researched_spot_metadata(self, agent):
        """Spot with research data should return metadata dict."""
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        result = await agent.get_spot_metadata("Pipeline")
        assert "name" in result
        assert "coordinates" in result
        assert result["break_type"] == "reef"

    @pytest.mark.asyncio
    async def test_unknown_spot_metadata(self, agent):
        """Unknown (unresearched) spot should return error."""
        result = await agent.get_spot_metadata("Nonexistent Beach XYZ")
        assert "error" in result


# -- fetch_contextual_info tests --

class TestFetchContextualInfo:
    """Tests for ForecastDataAgent.fetch_contextual_info()."""

    @pytest.mark.asyncio
    async def test_returns_all_context_sections(self, agent):
        """Should return parking, accessibility, reviews, safety."""
        result = await agent.fetch_contextual_info("Pipeline")
        assert result["spot_name"] == "Pipeline"
        assert "parking" in result
        assert "accessibility" in result
        assert "reviews" in result
        assert "safety" in result


# -- Tool definitions tests --

class TestToolDefinitions:
    """Tests for tool schema definitions."""

    def test_returns_three_tools(self):
        defs = ForecastDataAgent.get_tool_definitions()
        assert len(defs) == 3

    def test_tool_names(self):
        defs = ForecastDataAgent.get_tool_definitions()
        names = {d["function"]["name"] for d in defs}
        assert names == {"fetch_forecast", "fetch_contextual_info", "get_spot_metadata"}

    def test_tool_schema_structure(self):
        defs = ForecastDataAgent.get_tool_definitions()
        for d in defs:
            assert d["type"] == "function"
            assert "name" in d["function"]
            assert "description" in d["function"]
            assert "parameters" in d["function"]
            assert d["function"]["parameters"]["type"] == "object"
