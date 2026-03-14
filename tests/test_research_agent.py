"""
Unit tests for ResearchAgent.

Tests web search + LLM extraction workflow with mocked Tavily and LLM responses.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from config.settings import Settings
from app.agents.research_agent import ResearchAgent


# -- Fixtures --

@pytest.fixture
def settings():
    """Create a Settings instance with Tavily configured."""
    return Settings(
        _env_file=None,
        azure_openai={"endpoint": "", "api_key": ""},
        tavily={"api_key": "test-key"},
    )


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = MagicMock()
    return llm


@pytest.fixture
def agent(mock_llm, settings):
    """Create a ResearchAgent with mocked dependencies."""
    return ResearchAgent(mock_llm, settings)


# -- Sample data --

SAMPLE_TAVILY_RESPONSE = {
    "results": [
        {
            "title": "Costa da Caparica Surf Guide",
            "content": (
                "Costa da Caparica is a long beach break south of Lisbon, Portugal. "
                "Coordinates: 38.6446°N, 9.2363°W. It offers consistent waves year-round "
                "with sandy bottom. Best with NW swell and E wind. Great for beginners "
                "and intermediates. Hazards include rip currents and occasional rocks."
            ),
            "url": "https://example.com/caparica-surf",
        },
        {
            "title": "Surfing in Caparica",
            "content": (
                "Caparica has multiple peaks along its 30km stretch. The northern end "
                "near CDS is more protected. Break type is beach break with left and right "
                "waves. Crowd level is medium to high in summer."
            ),
            "url": "https://example.com/caparica-surfing",
        },
    ],
}

SAMPLE_LLM_EXTRACTION = {
    "name": "Costa da Caparica",
    "latitude": 38.6446,
    "longitude": -9.2363,
    "region": "Lisbon Coast",
    "country": "Portugal",
    "timezone": "Europe/Lisbon",
    "break_type": "beach",
    "wave_direction": "right_and_left",
    "bottom": "sand",
    "crowd_level": "high",
    "skill_minimum": "beginner",
    "skill_recommended": "intermediate",
    "beginner_friendly": True,
    "hazards": ["rip currents", "occasional rocks"],
    "facilities": ["parking", "showers", "surf schools"],
    "best_swell_direction": ["NW", "W"],
    "best_swell_size_min_m": 0.5,
    "best_swell_size_max_m": 2.5,
    "best_swell_period_min": 8.0,
    "best_wind_direction": ["E", "NE"],
    "best_tide": ["low", "mid"],
    "best_season": ["fall", "winter", "spring"],
    "description": "Long beach break south of Lisbon with consistent waves.",
    "local_tips": "Head to the southern end for fewer crowds.",
}


def _make_llm_response(content: str):
    """Create a mock LLM response object."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# -- Tests --

class TestResearchSpot:
    """Tests for ResearchAgent.research_spot()."""

    @pytest.mark.asyncio
    async def test_successful_research(self, agent, mock_llm):
        """Should return structured spot data from search + extraction."""
        # Mock Tavily
        mock_tavily = MagicMock()
        mock_tavily.search.return_value = SAMPLE_TAVILY_RESPONSE
        agent._tavily_client = mock_tavily

        # Mock LLM extraction
        mock_llm.chat_with_tools.return_value = _make_llm_response(
            json.dumps(SAMPLE_LLM_EXTRACTION)
        )

        result = await agent.research_spot("Caparica")

        assert result["name"] == "Costa da Caparica"
        assert result["latitude"] == pytest.approx(38.6446)
        assert result["longitude"] == pytest.approx(-9.2363)
        assert result["break_type"] == "beach"
        assert result["country"] == "Portugal"
        assert result["_source"] == "research"

    @pytest.mark.asyncio
    async def test_tavily_failure_returns_error(self, agent):
        """Should return error dict when Tavily search fails."""
        mock_tavily = MagicMock()
        mock_tavily.search.side_effect = Exception("API quota exceeded")
        agent._tavily_client = mock_tavily

        result = await agent.research_spot("Caparica")

        assert "error" in result
        assert "Web search failed" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_search_results(self, agent):
        """Should return error when no search results found."""
        mock_tavily = MagicMock()
        mock_tavily.search.return_value = {"results": []}
        agent._tavily_client = mock_tavily

        result = await agent.research_spot("xyznonexistent")

        assert "error" in result
        assert "No useful search results" in result["error"]

    @pytest.mark.asyncio
    async def test_llm_returns_invalid_json(self, agent, mock_llm):
        """Should return error when LLM returns unparseable response."""
        mock_tavily = MagicMock()
        mock_tavily.search.return_value = SAMPLE_TAVILY_RESPONSE
        agent._tavily_client = mock_tavily

        mock_llm.chat_with_tools.return_value = _make_llm_response(
            "This is not valid JSON"
        )

        result = await agent.research_spot("Caparica")

        assert "error" in result
        assert "Failed to parse" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_coordinates_returns_error(self, agent, mock_llm):
        """Should return error when extracted data lacks coordinates."""
        mock_tavily = MagicMock()
        mock_tavily.search.return_value = SAMPLE_TAVILY_RESPONSE
        agent._tavily_client = mock_tavily

        incomplete = {"name": "Caparica", "latitude": None, "longitude": None}
        mock_llm.chat_with_tools.return_value = _make_llm_response(
            json.dumps(incomplete)
        )

        result = await agent.research_spot("Caparica")

        assert "error" in result
        assert "coordinates" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_strips_markdown_fences(self, agent, mock_llm):
        """Should handle LLM responses wrapped in markdown code fences."""
        mock_tavily = MagicMock()
        mock_tavily.search.return_value = SAMPLE_TAVILY_RESPONSE
        agent._tavily_client = mock_tavily

        fenced = f"```json\n{json.dumps(SAMPLE_LLM_EXTRACTION)}\n```"
        mock_llm.chat_with_tools.return_value = _make_llm_response(fenced)

        result = await agent.research_spot("Caparica")

        assert result["name"] == "Costa da Caparica"
        assert result["_source"] == "research"


class TestResearchAgentConfig:
    """Tests for ResearchAgent configuration."""

    def test_missing_api_key_raises(self):
        """Should raise when TAVILY_API_KEY is not set."""
        settings = Settings(
            _env_file=None,
            azure_openai={"endpoint": "", "api_key": ""},
            tavily={"api_key": ""},
        )
        agent = ResearchAgent(MagicMock(), settings)

        with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
            agent._get_tavily_client()


class TestToolDefinitions:
    """Tests for research tool schema."""

    def test_returns_one_tool(self):
        defs = ResearchAgent.get_tool_definitions()
        assert len(defs) == 1

    def test_tool_name(self):
        defs = ResearchAgent.get_tool_definitions()
        assert defs[0]["function"]["name"] == "research_spot"

    def test_tool_schema_structure(self):
        defs = ResearchAgent.get_tool_definitions()
        d = defs[0]
        assert d["type"] == "function"
        assert "description" in d["function"]
        assert "parameters" in d["function"]
        assert "query" in d["function"]["parameters"]["properties"]
