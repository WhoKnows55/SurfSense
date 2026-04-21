"""
API Connection Smoke Tests

Pings every external service used by SurfSense to verify that
environment variables are set correctly and endpoints are reachable.

Run with:
    make check-api
    # or
    pytest tests/test_api_connections.py -v
"""

import pytest

from config.settings import Settings


@pytest.fixture(scope="module")
def settings():
    """Load settings (bypasses lru_cache so .env changes are picked up)."""
    return Settings()


# ── Azure OpenAI / OpenAI ────────────────────────────────────────────────────


class TestLLMConnection:
    """Verify that the configured LLM provider responds."""

    def test_llm_key_configured(self, settings):
        """At least one LLM API key must be set."""
        has_azure = bool(settings.azure_openai.endpoint and settings.azure_openai.api_key)
        has_openai = bool(settings.openai_api_key)
        assert has_azure or has_openai, (
            "No LLM API key configured. "
            "Set AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY or OPENAI_API_KEY in .env"
        )

    def test_llm_ping(self, settings):
        """Send a minimal request to the LLM endpoint."""
        if settings.azure_openai.endpoint and settings.azure_openai.api_key and not settings.azure_openai.api_key.startswith("sk-"):
            from openai import AzureOpenAI

            client = AzureOpenAI(
                azure_endpoint=settings.azure_openai.endpoint,
                api_key=settings.azure_openai.api_key,
                api_version=settings.azure_openai.api_version,
            )
            response = client.chat.completions.create(
                model=settings.azure_openai.deployment_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
        elif settings.openai_api_key:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.azure_openai.deployment_name or "gpt-4o",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
        else:
            pytest.skip("No LLM key configured")

        assert response.choices, "LLM returned no choices"


# ── Tavily Search ────────────────────────────────────────────────────────────


class TestTavilyConnection:
    """Verify that the Tavily web-search API is reachable."""

    def test_tavily_key_configured(self, settings):
        """TAVILY_API_KEY must be set."""
        assert settings.tavily.api_key, (
            "TAVILY_API_KEY is not set. Get a free key at https://tavily.com"
        )

    def test_tavily_ping(self, settings):
        """Run a minimal Tavily search."""
        if not settings.tavily.api_key:
            pytest.skip("TAVILY_API_KEY not set")

        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily.api_key)
        results = client.search(query="ping", max_results=1)
        assert "results" in results, "Tavily returned unexpected response"


# ── Stormglass ───────────────────────────────────────────────────────────────


class TestStormglassConnection:
    """Verify that the Stormglass forecast API is reachable."""

    def test_stormglass_key_configured(self, settings):
        """FORECAST_API_KEY should be set (optional but recommended)."""
        if not settings.forecast.api_key:
            pytest.skip("FORECAST_API_KEY not set (optional — Open-Meteo is used as fallback)")

    @pytest.mark.asyncio
    async def test_stormglass_ping(self, settings):
        """Send a minimal Stormglass API request."""
        if not settings.forecast.api_key:
            pytest.skip("FORECAST_API_KEY not set")

        import httpx

        params = {
            "lat": 0,
            "lng": 0,
            "params": "waveHeight",
        }
        headers = {"Authorization": settings.forecast.api_key}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.stormglass.io/v2/weather/point",
                params=params,
                headers=headers,
            )
        assert resp.status_code == 200, (
            f"Stormglass returned {resp.status_code}: {resp.text[:200]}"
        )


# ── Open-Meteo (free, no key) ───────────────────────────────────────────────


class TestOpenMeteoConnection:
    """Verify that the Open-Meteo marine API is reachable."""

    @pytest.mark.asyncio
    async def test_openmeteo_ping(self):
        """Ping the Open-Meteo marine endpoint."""
        from app.forecasting.openmeteo_client import OpenMeteoClient

        client = OpenMeteoClient()
        is_up = await client.health_check()
        assert is_up, "Open-Meteo API is not reachable"


# ── NOAA (free, no key) ─────────────────────────────────────────────────────


class TestNOAAConnection:
    """Verify that the NOAA weather API is reachable."""

    @pytest.mark.asyncio
    async def test_noaa_ping(self):
        """Ping the NOAA weather endpoint."""
        from app.forecasting.noaa_client import NOAAClient

        client = NOAAClient()
        is_up = await client.health_check()
        assert is_up, "NOAA API is not reachable"
