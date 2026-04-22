"""
Tests for the snapshot / replay mechanism in ForecastDataAgent.

Verifies that fetch_forecast with snapshot_path:
  1. Writes JSON to disk on first call (live fetch).
  2. Reads from disk on subsequent calls without hitting the API.
  3. Produces identical dicts in both cases.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config.settings import Settings
from app.agents.forecast_data_agent import ForecastDataAgent

SAMPLE_RESEARCH = {
    "name": "Pipeline",
    "latitude": 21.6650,
    "longitude": -158.0539,
    "timezone": "Pacific/Honolulu",
    "break_type": "reef",
}


@pytest.fixture
def settings():
    return Settings(
        _env_file=None,
        azure_openai={"endpoint": "", "api_key": ""},
    )


@pytest.fixture
def agent(settings):
    return ForecastDataAgent(settings)


def _mock_om_response():
    mock = MagicMock()
    mock.spot.name = "Pipeline"
    mock.spot.coordinates.latitude = 21.665
    mock.spot.coordinates.longitude = -158.054
    mock.source.value = "open_meteo"
    mock.fetched_at.isoformat.return_value = "2026-01-01T00:00:00"
    mock.forecasts = []
    return mock


class TestSnapshotWrite:
    @pytest.mark.asyncio
    async def test_snapshot_written_on_first_call(self, agent):
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            snap = f.name
        Path(snap).unlink()  # ensure it doesn't pre-exist

        with patch.object(
            agent._openmeteo_client, "get_forecast",
            new_callable=AsyncMock, return_value=_mock_om_response()
        ):
            await agent.fetch_forecast("Pipeline", snapshot_path=snap)

        assert Path(snap).exists(), "Snapshot file was not created"
        with open(snap) as f:
            data = json.load(f)
        assert data["spot"] == "Pipeline"
        Path(snap).unlink()


class TestSnapshotReplay:
    @pytest.mark.asyncio
    async def test_existing_snapshot_bypasses_api(self, agent):
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        snap_data = {"spot": "Pipeline", "forecasts": [], "source": "snapshot", "forecast_count": 0}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(snap_data, f)
            snap = f.name

        with patch.object(
            agent._openmeteo_client, "get_forecast", new_callable=AsyncMock
        ) as om_mock:
            result = await agent.fetch_forecast("Pipeline", snapshot_path=snap)
            om_mock.assert_not_called()

        assert result["spot"] == "Pipeline"
        assert result["source"] == "snapshot"
        Path(snap).unlink()

    @pytest.mark.asyncio
    async def test_replay_produces_identical_dict(self, agent):
        """Snapshot round-trip: write then read → same dict."""
        agent.set_research_data("Pipeline", SAMPLE_RESEARCH)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            snap = f.name
        Path(snap).unlink()

        with patch.object(
            agent._openmeteo_client, "get_forecast",
            new_callable=AsyncMock, return_value=_mock_om_response()
        ):
            first = await agent.fetch_forecast("Pipeline", snapshot_path=snap)

        # Clear cache so second call would hit API if snapshot not used
        agent._forecast_cache.clear()

        with patch.object(
            agent._openmeteo_client, "get_forecast", new_callable=AsyncMock
        ) as om_mock:
            second = await agent.fetch_forecast("Pipeline", snapshot_path=snap)
            om_mock.assert_not_called()

        # Compare all keys except _cached_at (added at cache time, not in snapshot)
        first_clean  = {k: v for k, v in first.items()  if k != "_cached_at"}
        second_clean = {k: v for k, v in second.items() if k != "_cached_at"}
        assert first_clean == second_clean
        Path(snap).unlink()
