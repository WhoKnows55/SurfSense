# SurfSense Refactoring Plan: Azure OpenAI Orchestrator with Deterministic Sub-Agents

## 1. Architectural Overview

The refactored SurfSense follows a single-orchestrator, multi-agent pattern. One LLM-powered orchestrator (GPT-4o via Azure OpenAI) manages dialogue and delegates tasks to four sub-agents through OpenAI function-calling. Three sub-agents are fully deterministic; the **Research Agent** uses the LLM for structured data extraction from web search results.

```
User (Terminal / Future GUI)
        │
        ▼
┌──────────────────────────────────────────────────┐
│          Orchestrator Agent (LLM-powered)         │
│  Azure OpenAI GPT-4o with function-calling        │
│  - Manages dialogue and user preference elicitation│
│  - Selects which sub-agent tool to call            │
│  - Synthesises sub-agent outputs into responses    │
│  - Maintains conversation history                  │
└──┬──────────┬──────────────┬──────────────┬──────┘
   │          │              │              │
   ▼          ▼              ▼              ▼
┌────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│Research│ │  Forecast &  │ │  Condition   │ │    Trip      │
│ Agent  │ │    Data      │ │  Assessment  │ │  Planning    │
│        │ │  Aggregation │ │    Agent     │ │    Agent     │
│ Tools: │ │    Agent     │ │              │ │              │
│-research│ │              │ │ Tools:       │ │ Tools:       │
│ _spot  │ │ Tools:       │ │ -assess_     │ │ -find_surf_  │
│        │ │ -fetch_      │ │  conditions  │ │  windows     │
│Tavily +│ │  forecast    │ │ -check_      │ │ -plan_       │
│LLM     │ │ -fetch_      │ │  safety      │ │  itinerary   │
│extract │ │  contextual  │ │ -get_skill_  │ │ -rank_spots  │
│        │ │  _info       │ │  thresholds  │ │              │
│        │ │ -get_spot_   │ │              │ │              │
│        │ │  metadata    │ │              │ │              │
└────────┘ └─────────────┘ └──────────────┘ └──────────────┘
   │              │                │                  │
   ▼              ▼                ▼                  ▼
 Tavily       External APIs    config/settings.py   Haversine +
 Web Search   (Open-Meteo,     (SkillLevel          greedy
              Stormglass,       Thresholds)         optimisation
              Contextual
              Providers)
```

### Design Rationale

- **Single LLM point**: Only the orchestrator calls Azure OpenAI (plus the ResearchAgent's extraction step). This keeps token costs predictable, avoids non-determinism in safety-critical scoring, and simplifies debugging.
- **Dynamic knowledge via web search**: Instead of a hardcoded spot database, the ResearchAgent uses Tavily web search + LLM extraction to gather structured information about any surf spot worldwide at conversation time.
- **Function-calling as delegation mechanism**: The orchestrator's system prompt describes the available tools. GPT-4o decides which tools to invoke and in what order. The tool results are fed back into the conversation, and the orchestrator synthesises a final natural-language response.
- **Sub-agents are Python classes, not LLM agents**: Each sub-agent is a class with methods registered as OpenAI function-calling tools. They contain deterministic logic (scoring formulas, API calls, optimisation algorithms).

---

## 2. File-by-File Change Plan

### Legend
- **NEW** = file does not exist, must be created
- **MODIFY** = file exists, specific changes listed
- **KEEP** = file unchanged
- **DEPRECATE** = file is superseded but not deleted (avoid breaking imports during transition)

---

### 2.1 Configuration

#### MODIFY: `config/settings.py`

Add an `AzureOpenAISettings` section. Keep the existing `LLMSettings` and `ForecastAPISettings` intact.

```python
class AzureOpenAISettings(BaseSettings):
    """Configuration for Azure OpenAI Service."""

    model_config = SettingsConfigDict(env_prefix="AZURE_OPENAI_")

    endpoint: str = Field(
        default="",
        description="Azure OpenAI endpoint URL (e.g. https://<resource>.openai.azure.com/)"
    )
    api_key: str = Field(
        default="",
        description="Azure OpenAI API key"
    )
    deployment_name: str = Field(
        default="gpt-4o",
        description="Azure deployment name for the model"
    )
    api_version: str = Field(
        default="2024-10-21",
        description="Azure OpenAI API version"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0,
        description="Sampling temperature for the orchestrator"
    )
    max_tokens: int = Field(
        default=2000, ge=100, le=8000,
        description="Maximum tokens in LLM response"
    )
```

Add this to the root `Settings` class:

```python
azure_openai: AzureOpenAISettings = Field(default_factory=AzureOpenAISettings)
```

Update `validate_required_keys()`:

```python
if not self.azure_openai.endpoint or not self.azure_openai.api_key:
    missing.append("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
```

#### MODIFY: `.env.example`

Add:

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_TEMPERATURE=0.7
AZURE_OPENAI_MAX_TOKENS=2000
```

---

### 2.2 LLM Service Layer

#### MODIFY: `app/core/llm_service.py`

Add a new `AzureOpenAIProvider` class. This provider wraps `openai.AzureOpenAI` and exposes two methods:

1. `chat(messages, tools=None)` -- sends a full message history with optional function-calling tool definitions. Returns the model's response (which may be a tool call or text).
2. `is_available()` -- checks credentials.

```python
from openai import AzureOpenAI

class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider with function-calling support."""

    def __init__(self, endpoint: str, api_key: str, deployment_name: str,
                 api_version: str, temperature: float = 0.7, max_tokens: int = 2000):
        self.deployment_name = deployment_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    def generate(self, prompt: str) -> str:
        """Simple single-turn generation (backward compat)."""
        response = self._client.chat.completions.create(
            model=self.deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content.strip()

    def chat_with_tools(self, messages: list[dict], tools: list[dict] | None = None) -> "ChatCompletion":
        """Full chat completion with optional function-calling tools.

        Args:
            messages: OpenAI-format message list [{"role": ..., "content": ...}].
            tools:    OpenAI function-calling tool definitions (optional).

        Returns:
            The raw ChatCompletion object for the orchestrator to inspect.
        """
        kwargs = {
            "model": self.deployment_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self._client.chat.completions.create(**kwargs)

    def is_available(self) -> bool:
        return bool(self._client)
```

Also update `LLMService.from_settings()` to handle `azure_openai`:

```python
@classmethod
def from_settings(cls, settings) -> "LLMService":
    if settings.azure_openai.endpoint and settings.azure_openai.api_key:
        provider = AzureOpenAIProvider(
            endpoint=settings.azure_openai.endpoint,
            api_key=settings.azure_openai.api_key,
            deployment_name=settings.azure_openai.deployment_name,
            api_version=settings.azure_openai.api_version,
            temperature=settings.azure_openai.temperature,
            max_tokens=settings.azure_openai.max_tokens,
        )
    elif settings.llm.provider == "openai":
        provider = OpenAILLMProvider(...)
    else:
        provider = LocalLLMProvider(...)
    return cls(provider)
```

**Key point**: The `AzureOpenAIProvider` has `chat_with_tools()` in addition to the base `generate()`. The orchestrator uses `chat_with_tools()`; legacy code can still call `generate()`.

---

### 2.3 Sub-Agent Definitions

Each sub-agent is a Python class with methods that serve as tools. Each class also provides a `get_tool_definitions()` method that returns OpenAI function-calling JSON schemas for its tools.

---

#### NEW: `app/agents/forecast_data_agent.py`

**Purpose**: Aggregates heterogeneous surf data (wave forecasts, tide, wind, contextual info) into a unified representation.

**Reuses**: `app/forecasting/models.py` (ForecastPoint, ForecastResponse, etc.), `app/contextual/` providers, existing `ForecastIntegrationAgent` logic (cache, mock data, API fetch).

**Tools exposed to the orchestrator**:

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `fetch_forecast` | `spot_name: str, days: int` | Unified forecast dict (waves, swell, wind, tide per hour) | Fetches from Open-Meteo (primary) / Stormglass (fallback), normalises to ForecastPoint schema, applies 1-hour cache |
| `fetch_contextual_info` | `spot_name: str` | Dict with parking, accessibility, reviews, safety | Aggregates all four contextual providers into one response |
| `get_spot_metadata` | `spot_name: str` | Coordinates, timezone, break type | Returns static spot information |

**Implementation approach**:

```python
class ForecastDataAgent:
    """Deterministic sub-agent for data aggregation."""

    def __init__(self, settings):
        self._forecast_cache = {}
        self._cache_ttl = timedelta(hours=1)
        # Initialise contextual providers (reuse existing)
        self._parking = ParkingProvider()
        self._accessibility = AccessibilityProvider()
        self._reviews = ReviewsProvider()
        self._safety = SafetyProvider()

    async def fetch_forecast(self, spot_name: str, days: int = 3) -> dict:
        """Fetch and unify forecast data."""
        # 1. Check cache
        # 2. Call Open-Meteo API (primary)
        # 3. Fallback to Stormglass if Open-Meteo fails
        # 4. Normalise to ForecastPoint list
        # 5. Cache and return
        ...

    async def fetch_contextual_info(self, spot_name: str) -> dict:
        """Aggregate contextual data from all providers."""
        parking = await self._parking.get_data(spot_name)
        access = await self._accessibility.get_data(spot_name)
        reviews = await self._reviews.get_data(spot_name)
        safety = await self._safety.get_data(spot_name)
        return {
            "spot_name": spot_name,
            "parking": parking.model_dump(),
            "accessibility": access.model_dump(),
            "reviews": reviews.model_dump(),
            "safety": safety.model_dump(),
        }

    async def get_spot_metadata(self, spot_name: str) -> dict:
        """Return static spot data."""
        ...

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        """Return OpenAI function-calling schemas for all tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "fetch_forecast",
                    "description": "Fetch surf forecast data (waves, swell, wind, tide) for a spot over N days. Returns hourly data normalised to a unified schema.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {"type": "string", "description": "Name of the surf spot"},
                            "days": {"type": "integer", "description": "Number of days to forecast (1-7)", "default": 3},
                        },
                        "required": ["spot_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_contextual_info",
                    "description": "Get parking, accessibility, reviews, and safety information for a surf spot.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {"type": "string", "description": "Name of the surf spot"},
                        },
                        "required": ["spot_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_spot_metadata",
                    "description": "Get static metadata for a surf spot: coordinates, timezone, break type.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {"type": "string", "description": "Name of the surf spot"},
                        },
                        "required": ["spot_name"],
                    },
                },
            },
        ]
```

**Relationship to existing code**: This class absorbs the data-fetching logic from `ForecastIntegrationAgent` and the aggregation logic that was planned but not yet built in `app/contextual/__init__.py`. The existing `ForecastIntegrationAgent` can be deprecated once this is stable.

---

#### NEW: `app/agents/condition_agent.py`

**Purpose**: Evaluates environmental conditions against user skill levels to produce safety-aware quality assessments.

**Reuses**: `config/settings.py` (`SkillLevelThresholds`), scoring logic from `ForecastIntegrationAgent._tool_analyze_conditions()`.

**Tools exposed to the orchestrator**:

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `assess_conditions` | `forecast_data: dict, skill_level: str` | List of hourly assessments with rating and reasoning | Scores each ForecastPoint against skill thresholds, returns "ideal" / "suitable" / "challenging" / "unsafe" per hour |
| `check_safety` | `spot_name: str, forecast_data: dict, skill_level: str` | Safety verdict with warnings | Combines hazard data from contextual layer with condition assessment |
| `get_skill_thresholds` | `skill_level: str` | Dict of max wave height, max wind speed | Returns the configured thresholds for a given skill level |

**Implementation approach**:

```python
class ConditionAssessmentAgent:
    """Deterministic sub-agent for condition evaluation."""

    def __init__(self, settings):
        self._thresholds = settings.skill_thresholds

    def assess_conditions(self, forecast_data: dict, skill_level: str = "intermediate") -> list[dict]:
        """Score each forecast point against skill-level thresholds.

        Returns a list of dicts, one per forecast point:
        {
            "timestamp": "...",
            "rating": "ideal" | "suitable" | "challenging" | "unsafe",
            "score": 0-100,
            "reasoning": "...",
            "wave_height_m": ...,
            "wind_speed_kph": ...,
            "swell_period_s": ...,
        }
        """
        thresholds = self._thresholds.get_thresholds(skill_level)
        results = []
        for fc in forecast_data.get("forecasts", []):
            waves = fc.get("waves", {})
            wind = fc.get("wind", {})
            swell = fc.get("swell", {})

            wave_avg = waves.get("avg_m", 0)
            wind_speed = wind.get("speed_kph", 0)
            swell_period = swell.get("period_s", 0)

            # Scoring formula (deterministic)
            wave_score = min(wave_avg / thresholds["max_wave_height"], 1.0) * 40
            period_score = min(swell_period / 14, 1.0) * 30
            wind_penalty = max(0, (wind_speed - thresholds["max_wind_speed"]) / 10) * 20
            offshore_bonus = 10 if wind.get("is_offshore") else 0

            score = wave_score + period_score - wind_penalty + offshore_bonus
            score = max(0, min(100, score))

            # Map score to rating
            if wind_speed > thresholds["max_wind_speed"] * 1.5 or wave_avg > thresholds["max_wave_height"] * 1.5:
                rating = "unsafe"
            elif score >= 70:
                rating = "ideal"
            elif score >= 45:
                rating = "suitable"
            else:
                rating = "challenging"

            results.append({
                "timestamp": fc["timestamp"],
                "rating": rating,
                "score": round(score, 1),
                "reasoning": self._build_reasoning(wave_avg, wind_speed, swell_period, thresholds, rating),
                "wave_height_m": wave_avg,
                "wind_speed_kph": wind_speed,
                "swell_period_s": swell_period,
            })
        return results

    def check_safety(self, spot_name: str, forecast_data: dict, skill_level: str,
                     safety_info: dict) -> dict:
        """Combine hazard data with condition assessment into a safety verdict."""
        assessments = self.assess_conditions(forecast_data, skill_level)
        unsafe_count = sum(1 for a in assessments if a["rating"] == "unsafe")
        warnings = list(safety_info.get("warnings", []))

        if safety_info.get("recommended_skill_level"):
            rec = safety_info["recommended_skill_level"]
            skill_order = ["beginner", "intermediate", "advanced", "expert"]
            if skill_order.index(skill_level) < skill_order.index(rec):
                warnings.append(
                    f"This spot is recommended for {rec} surfers. Your level ({skill_level}) may be insufficient."
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
        """Return configured thresholds."""
        return self._thresholds.get_thresholds(skill_level)

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "assess_conditions",
                    "description": "Evaluate surf conditions against a user's skill level. Returns per-hour ratings (ideal/suitable/challenging/unsafe) with scores and reasoning.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {"type": "string", "description": "Spot name (forecast must have been fetched first)"},
                            "skill_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"], "description": "User's surfing skill level"},
                        },
                        "required": ["spot_name", "skill_level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_safety",
                    "description": "Get a safety assessment for a spot, combining hazard data with current conditions and user skill level.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {"type": "string"},
                            "skill_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        },
                        "required": ["spot_name", "skill_level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_skill_thresholds",
                    "description": "Return the wave height and wind speed thresholds for a given skill level.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "skill_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        },
                        "required": ["skill_level"],
                    },
                },
            },
        ]
```

---

#### NEW: `app/agents/trip_planning_agent.py`

**Purpose**: Identifies optimal surf windows across multiple spots and generates itineraries that maximise surfing quality and time.

**Reuses**: `ForecastIntegrationAgent._tool_find_best_window()` logic, Haversine formula (already referenced in your thesis).

**Tools exposed to the orchestrator**:

| Tool Name | Parameters | Returns | Description |
|-----------|-----------|---------|-------------|
| `find_surf_windows` | `spot_name: str, assessments: list, min_hours: int` | List of contiguous windows with start/end times and average scores | Groups consecutive "ideal" or "suitable" hours into surf windows |
| `plan_itinerary` | `spots: list[str], days: int, skill_level: str, base_location: dict` | Ordered itinerary with day-by-day schedule | Greedy optimisation: for each day, pick the spot with the best window, accounting for travel time (Haversine) |
| `rank_spots` | `spot_assessments: dict` | Ranked list of spots with aggregate scores | Compares multiple spots by average condition score over the trip period |

**Implementation approach**:

```python
import math

class TripPlanningAgent:
    """Deterministic sub-agent for itinerary optimisation."""

    def find_surf_windows(self, assessments: list[dict], min_hours: int = 2) -> list[dict]:
        """Group consecutive good-condition hours into surf windows.

        Args:
            assessments: Output of ConditionAssessmentAgent.assess_conditions()
            min_hours:   Minimum window length to consider

        Returns:
            List of windows: {"start": ..., "end": ..., "avg_score": ..., "hours": ...}
        """
        suitable = [a for a in assessments if a["rating"] in ("ideal", "suitable")]
        # Group consecutive timestamps into windows
        # (timestamps assumed hourly and sorted)
        windows = []
        current_window = []
        for a in suitable:
            if not current_window:
                current_window.append(a)
            else:
                # Check if consecutive (within ~1.5 hours of previous)
                # Implementation detail: parse timestamps and compare
                current_window.append(a)
            # ... grouping logic ...
        # Filter by min_hours and compute avg_score per window
        return windows

    def plan_itinerary(self, spots_data: dict, days: int, skill_level: str,
                       base_coords: dict | None = None) -> dict:
        """Generate a multi-day itinerary using greedy optimisation.

        For each day:
        1. Compute best surf window per spot
        2. Penalise by travel time from previous day's spot (Haversine)
        3. Select spot with highest adjusted score
        4. Avoid repeating same spot on consecutive days (soft preference)

        Args:
            spots_data: Dict mapping spot_name -> {"assessments": [...], "coordinates": {...}, "windows": [...]}
            days:       Number of trip days
            skill_level: User skill level
            base_coords: Starting location {"lat": ..., "lon": ...}

        Returns:
            {"days": [{"day": 1, "spot": ..., "window": ..., "travel_km": ...}, ...],
             "total_score": ..., "total_travel_km": ...}
        """
        itinerary = []
        prev_coords = base_coords
        used_spots = set()

        for day in range(1, days + 1):
            best_spot = None
            best_adjusted_score = -1

            for spot_name, data in spots_data.items():
                windows = data.get("windows", [])
                if not windows:
                    continue

                # Best window for this day
                day_windows = [w for w in windows if self._is_day(w["start"], day)]
                if not day_windows:
                    continue

                top_window = max(day_windows, key=lambda w: w["avg_score"])
                score = top_window["avg_score"]

                # Travel penalty
                if prev_coords and data.get("coordinates"):
                    dist = self._haversine(prev_coords, data["coordinates"])
                    travel_penalty = min(dist / 100, 20)  # cap penalty
                    score -= travel_penalty
                else:
                    dist = 0

                # Diversity bonus (avoid same spot)
                if spot_name in used_spots:
                    score -= 5

                if score > best_adjusted_score:
                    best_adjusted_score = score
                    best_spot = {
                        "day": day,
                        "spot": spot_name,
                        "window": top_window,
                        "travel_km": round(dist, 1) if dist else 0,
                    }

            if best_spot:
                itinerary.append(best_spot)
                prev_coords = spots_data[best_spot["spot"]].get("coordinates")
                used_spots.add(best_spot["spot"])

        total_score = sum(d["window"]["avg_score"] for d in itinerary)
        total_travel = sum(d["travel_km"] for d in itinerary)

        return {
            "days": itinerary,
            "total_score": round(total_score, 1),
            "total_travel_km": round(total_travel, 1),
        }

    def rank_spots(self, spot_assessments: dict[str, list[dict]]) -> list[dict]:
        """Rank spots by aggregate condition score.

        Args:
            spot_assessments: Dict mapping spot_name -> list of assessment dicts

        Returns:
            Sorted list: [{"spot": ..., "avg_score": ..., "ideal_hours": ..., "suitable_hours": ...}]
        """
        rankings = []
        for spot, assessments in spot_assessments.items():
            scores = [a["score"] for a in assessments]
            rankings.append({
                "spot": spot,
                "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
                "ideal_hours": sum(1 for a in assessments if a["rating"] == "ideal"),
                "suitable_hours": sum(1 for a in assessments if a["rating"] == "suitable"),
                "unsafe_hours": sum(1 for a in assessments if a["rating"] == "unsafe"),
            })
        return sorted(rankings, key=lambda r: r["avg_score"], reverse=True)

    @staticmethod
    def _haversine(coord1: dict, coord2: dict) -> float:
        """Compute distance in km between two coordinate dicts."""
        R = 6371
        lat1, lon1 = math.radians(coord1["lat"]), math.radians(coord1["lon"])
        lat2, lon2 = math.radians(coord2["lat"]), math.radians(coord2["lon"])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "find_surf_windows",
                    "description": "Find contiguous time windows with good surf conditions at a spot. Requires that assess_conditions has been called first.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {"type": "string"},
                            "min_hours": {"type": "integer", "default": 2, "description": "Minimum window duration in hours"},
                        },
                        "required": ["spot_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "plan_itinerary",
                    "description": "Generate a multi-day surf trip itinerary across multiple spots, optimising for surf quality and minimising travel. Requires forecasts and assessments for all candidate spots.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of candidate spot names"
                            },
                            "days": {"type": "integer", "description": "Number of trip days"},
                            "skill_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                        },
                        "required": ["spot_names", "days", "skill_level"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "rank_spots",
                    "description": "Rank multiple surf spots by overall condition quality for a given period. Requires that assess_conditions has been called for each spot.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Spot names to rank"
                            },
                        },
                        "required": ["spot_names"],
                    },
                },
            },
        ]
```

---

### 2.4 Orchestrator

#### NEW: `app/agents/orchestrator.py`

The orchestrator is the only LLM-powered component. It:
1. Maintains conversation history as an OpenAI message list.
2. Collects all tool definitions from the three sub-agents.
3. Calls Azure OpenAI with function-calling enabled.
4. When the model returns a tool call, dispatches it to the appropriate sub-agent.
5. Feeds tool results back into the conversation and re-calls the model.
6. Repeats until the model returns a text response (no more tool calls).

```python
import json
from app.core.llm_service import AzureOpenAIProvider
from app.agents.forecast_data_agent import ForecastDataAgent
from app.agents.condition_agent import ConditionAssessmentAgent
from app.agents.trip_planning_agent import TripPlanningAgent

class Orchestrator:
    """LLM-powered orchestrator that delegates to deterministic sub-agents."""

    SYSTEM_PROMPT = """You are SurfSense, an AI surf trip planning assistant.

You help surfers plan trips by having a natural conversation to understand their needs,
then using your tools to fetch data, evaluate conditions, and build itineraries.

WORKFLOW:
1. Greet the user and ask about their trip: dates, location preferences, skill level, group size.
2. Once you have enough info, call fetch_forecast for candidate spots.
3. Call assess_conditions to evaluate each spot for the user's skill level.
4. Call check_safety if any spots have concerning conditions.
5. Call find_surf_windows to identify the best times.
6. For multi-day trips, call plan_itinerary to optimise the schedule.
7. Present results in a clear, enthusiastic but safety-conscious manner.

RULES:
- Always ask for skill level before making recommendations.
- Never recommend spots rated "unsafe" for the user's level without explicit warnings.
- Be concise. Present key info first, details on request.
- If a tool call fails, explain the issue and suggest alternatives.
"""

    MAX_TOOL_ROUNDS = 10  # Safety limit on tool-call loops

    def __init__(self, llm_provider: AzureOpenAIProvider, settings):
        self._llm = llm_provider
        self._forecast_agent = ForecastDataAgent(settings)
        self._condition_agent = ConditionAssessmentAgent(settings)
        self._trip_agent = TripPlanningAgent()

        # Conversation history (OpenAI message format)
        self._messages: list[dict] = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        # Tool dispatch table: tool_name -> (agent, method_name)
        self._tool_dispatch = {
            "fetch_forecast": (self._forecast_agent, "fetch_forecast"),
            "fetch_contextual_info": (self._forecast_agent, "fetch_contextual_info"),
            "get_spot_metadata": (self._forecast_agent, "get_spot_metadata"),
            "assess_conditions": (self._condition_agent, "assess_conditions"),
            "check_safety": (self._condition_agent, "check_safety"),
            "get_skill_thresholds": (self._condition_agent, "get_skill_thresholds"),
            "find_surf_windows": (self._trip_agent, "find_surf_windows"),
            "plan_itinerary": (self._trip_agent, "plan_itinerary"),
            "rank_spots": (self._trip_agent, "rank_spots"),
        }

        # Collect all tool definitions
        self._tools = (
            ForecastDataAgent.get_tool_definitions()
            + ConditionAssessmentAgent.get_tool_definitions()
            + TripPlanningAgent.get_tool_definitions()
        )

        # Intermediate data store (forecast/assessment results cached here
        # so later tools can reference them by spot_name)
        self._session_data: dict[str, dict] = {}

    async def process(self, user_input: str) -> str:
        """Process user input through the orchestrator loop.

        1. Append user message to history.
        2. Call Azure OpenAI with tools.
        3. If model returns tool_calls, execute them and feed results back.
        4. Repeat until model returns a text response.
        5. Return the text response.
        """
        self._messages.append({"role": "user", "content": user_input})

        for _ in range(self.MAX_TOOL_ROUNDS):
            response = self._llm.chat_with_tools(self._messages, self._tools)
            message = response.choices[0].message

            # If no tool calls, we have a final text response
            if not message.tool_calls:
                self._messages.append({"role": "assistant", "content": message.content})
                return message.content

            # Process tool calls
            # Append the assistant message (with tool_calls) to history
            self._messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Execute the tool
                result = await self._execute_tool(tool_name, tool_args)

                # Append tool result to history
                self._messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })

        # Safety: if we hit MAX_TOOL_ROUNDS, return what we have
        return "I've gathered the data but need to simplify my analysis. Let me summarise what I found..."

    async def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """Dispatch a tool call to the appropriate sub-agent."""
        if tool_name not in self._tool_dispatch:
            return {"error": f"Unknown tool: {tool_name}"}

        agent, method_name = self._tool_dispatch[tool_name]
        method = getattr(agent, method_name)

        try:
            # Some tools need session data (e.g., assess_conditions needs forecast_data)
            # The orchestrator manages this by injecting cached data
            enriched_args = self._enrich_args(tool_name, args)

            result = method(**enriched_args)
            if hasattr(result, "__await__"):
                result = await result

            # Cache results for cross-tool dependencies
            self._cache_result(tool_name, args, result)

            return result

        except Exception as e:
            return {"error": str(e)}

    def _enrich_args(self, tool_name: str, args: dict) -> dict:
        """Inject cached session data into tool arguments where needed.

        For example, assess_conditions needs the forecast_data dict,
        which was returned by a prior fetch_forecast call.
        """
        if tool_name == "assess_conditions":
            spot = args.get("spot_name", "")
            if spot in self._session_data and "forecast" in self._session_data[spot]:
                args["forecast_data"] = self._session_data[spot]["forecast"]
        elif tool_name == "check_safety":
            spot = args.get("spot_name", "")
            if spot in self._session_data:
                if "forecast" in self._session_data[spot]:
                    args["forecast_data"] = self._session_data[spot]["forecast"]
                if "contextual" in self._session_data[spot]:
                    args["safety_info"] = self._session_data[spot]["contextual"].get("safety", {})
        elif tool_name in ("find_surf_windows",):
            spot = args.get("spot_name", "")
            if spot in self._session_data and "assessments" in self._session_data[spot]:
                args["assessments"] = self._session_data[spot]["assessments"]
        elif tool_name == "plan_itinerary":
            # Build spots_data from session cache
            spots_data = {}
            for spot_name in args.get("spot_names", []):
                if spot_name in self._session_data:
                    spots_data[spot_name] = self._session_data[spot_name]
            args["spots_data"] = spots_data
        elif tool_name == "rank_spots":
            spot_assessments = {}
            for spot_name in args.get("spot_names", []):
                if spot_name in self._session_data and "assessments" in self._session_data[spot_name]:
                    spot_assessments[spot_name] = self._session_data[spot_name]["assessments"]
            args["spot_assessments"] = spot_assessments
        return args

    def _cache_result(self, tool_name: str, args: dict, result: dict) -> None:
        """Store tool results in session cache for cross-tool dependencies."""
        spot = args.get("spot_name", "")
        if not spot:
            return

        if spot not in self._session_data:
            self._session_data[spot] = {}

        if tool_name == "fetch_forecast":
            self._session_data[spot]["forecast"] = result
            if "coordinates" in result:
                self._session_data[spot]["coordinates"] = result["coordinates"]
        elif tool_name == "fetch_contextual_info":
            self._session_data[spot]["contextual"] = result
        elif tool_name == "assess_conditions":
            self._session_data[spot]["assessments"] = result
        elif tool_name == "find_surf_windows":
            self._session_data[spot]["windows"] = result

    def reset(self) -> None:
        """Reset conversation and session data."""
        self._messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        self._session_data = {}
```

---

### 2.5 Entry Point

#### MODIFY: `app/__main__.py`

Replace the current agent initialisation with the orchestrator. Minimal changes to the chat loop itself.

```python
async def chat_loop(settings) -> None:
    from app.core.llm_service import AzureOpenAIProvider
    from app.agents.orchestrator import Orchestrator

    print("\n🏄 Initialising SurfSense...")

    # Initialise Azure OpenAI provider
    try:
        llm_provider = AzureOpenAIProvider(
            endpoint=settings.azure_openai.endpoint,
            api_key=settings.azure_openai.api_key,
            deployment_name=settings.azure_openai.deployment_name,
            api_version=settings.azure_openai.api_version,
            temperature=settings.azure_openai.temperature,
            max_tokens=settings.azure_openai.max_tokens,
        )
    except Exception as e:
        print(f"\n❌ Failed to initialise Azure OpenAI: {e}")
        return

    # Initialise orchestrator
    orchestrator = Orchestrator(llm_provider, settings)

    print("\n✅ Ready! Type 'quit' or 'exit' to leave.")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("\n👋 Goodbye!")
            break
        if user_input.lower() == "/reset":
            orchestrator.reset()
            print("\n🔄 Conversation reset.")
            continue

        try:
            print("\n🤖 SurfSense: ", end="", flush=True)
            response = await orchestrator.process(user_input)
            print(response)
        except Exception as e:
            print(f"\n❌ Error: {e}")
```

The `/forecast`, `/skill`, and `/help` slash commands can be removed. The orchestrator now handles all of this through natural conversation and tool-calling. Alternatively, keep `/reset` as a convenience.

---

### 2.6 Existing Files: Keep or Deprecate

| File | Action | Reason |
|------|--------|--------|
| `app/agents/base.py` | **KEEP** | Still useful as a base class if you want sub-agents to inherit logging. Not strictly required by the new design but harmless. |
| `app/agents/conversational.py` | **DEPRECATE** | Superseded by `orchestrator.py`. Keep the file but remove from `__init__.py` imports. |
| `app/agents/forecast_integration.py` | **DEPRECATE** | Logic absorbed by `forecast_data_agent.py`. Keep as reference during transition. |
| `app/agents/contextual_agent.py` | **KEEP** | Wrapped by `ForecastDataAgent.fetch_contextual_info()`. |
| `app/agents/trip_planning_state.py` | **KEEP** | Available for future state management needs. |
| `app/forecasting/models.py` | **KEEP** | Core Pydantic models (ForecastPoint etc.) are still used by ForecastDataAgent. |
| `app/forecasting/openmeteo_client.py` | **KEEP** | Reused by ForecastDataAgent for real API calls. |
| `app/forecasting/stormglass_client.py` | **KEEP** | Available as fallback when API key is configured. |
| `app/contextual/*.py` | **KEEP** | All four providers are reused by ForecastDataAgent.fetch_contextual_info(). |
| `app/planning/condition_assessor.py` | **KEEP** | Wrapped by `ConditionAssessmentAgent`. |
| `app/planning/window_finder.py` | **KEEP** | Wrapped by `TripPlanningAgent`. |
| `app/planning/trip_planner.py` | **KEEP** | Wrapped by `TripPlanningAgent`. |
| `app/planning/forecast_preview.py` | **KEEP** | May be used for formatting. |
| `app/planning/travel_utils.py` | **KEEP** | Haversine and travel time calculations reused. |
| `app/knowledge/spot_database.py` | **KEEP** | Used by `ForecastDataAgent.get_spot_metadata()`. |
| `app/core/llm_service.py` | **MODIFY** | Add AzureOpenAIProvider. Keep existing providers for backward compatibility. |
| `app/core/logger.py` | **KEEP** | Unchanged. |
| `config/settings.py` | **MODIFY** | Add AzureOpenAISettings. |
| `requirements.txt` | **MODIFY** | Ensure `openai>=1.6.1` is present (already is). Azure uses the same `openai` package. |

---

### 2.7 Updated `app/agents/__init__.py`

```python
"""SurfSense Agent Layer."""

from app.agents.orchestrator import Orchestrator
from app.agents.forecast_data_agent import ForecastDataAgent
from app.agents.condition_agent import ConditionAssessmentAgent
from app.agents.trip_planning_agent import TripPlanningAgent

# Deprecated but kept for reference
from app.agents.base import BaseAgent

__all__ = [
    "Orchestrator",
    "ForecastDataAgent",
    "ConditionAssessmentAgent",
    "TripPlanningAgent",
    "BaseAgent",
]
```

---

## 3. Data Flow Example

Here is a concrete walkthrough of a user planning a 2-day trip:

```
User: "I'm an intermediate surfer planning a 2-day trip near Lisbon next weekend."

ORCHESTRATOR (LLM reasoning):
  → User wants: 2-day trip, intermediate, Lisbon area
  → I need to research surf spots near Lisbon first.
  → Tool call: research_spot(query="best surf spots near Lisbon Portugal")

SUB-AGENT (ResearchAgent):
  → Tavily search: "best surf spots near Lisbon Portugal surf spot conditions..."
  → Gets results about Costa da Caparica, Ericeira, Carcavelos
  → LLM extracts structured data: coordinates, break type, hazards, skill levels
  → Returns: { name: "Costa da Caparica", lat: 38.6446, lon: -9.2363, break_type: "beach", ... }

ORCHESTRATOR (receives research data, caches it, injects into ForecastDataAgent):
  → Now I have coordinates. Let me get forecasts.
  → Tool call: research_spot(query="Ericeira surf spot Portugal")
  → Tool call: fetch_forecast(spot_name="Costa da Caparica", days=3)

SUB-AGENT (ForecastDataAgent):
  → Resolves coordinates from injected research data
  → Calls Open-Meteo for Costa da Caparica → returns hourly data
  → Normalises to ForecastPoint schema → returns dict
  → Caches result

ORCHESTRATOR (receives forecast data):
  → Now I need to assess conditions.
  → Tool call: assess_conditions(spot_name="Costa da Caparica", skill_level="intermediate")
  → Tool call: assess_conditions(spot_name="Ericeira", skill_level="intermediate")

SUB-AGENT (ConditionAssessmentAgent):
  → Scores each hour against intermediate thresholds
  → Caparica: mostly "ideal" or "suitable" (gentle beach break)
  → Ericeira: some "challenging" hours (powerful reef/point breaks)

ORCHESTRATOR (receives assessments):
  → Ericeira has some challenging conditions. Let me check safety.
  → Tool call: check_safety(spot_name="Ericeira", skill_level="intermediate")
  → Tool call: find_surf_windows(spot_name="Costa da Caparica")
  → Tool call: plan_itinerary(spot_names=["Costa da Caparica", "Ericeira"], days=2)

SUB-AGENT (TripPlanningAgent):
  → Caparica has 5-hour morning windows both days.
  → Ericeira has a suitable window on day 2 afternoon.
  → Itinerary: Day 1 Caparica AM, Day 2 Caparica AM + Ericeira PM.

ORCHESTRATOR (synthesises final response):
  "Great news for your Lisbon surf trip! Here's what I'd recommend:

   Day 1 (Saturday): Costa da Caparica, 7am-12pm
   - Conditions: 3-4ft waves, light E wind (offshore), ideal for intermediate
   - Beach break with sand bottom — very forgiving

   Day 2 (Sunday): Costa da Caparica 7-10am, then Ericeira 2-5pm
   - Ericeira has a suitable window with clean conditions at Ribeira d'Ilhas.

   ⚠️ Safety note: Some Ericeira spots (like Coxos) are advanced-only.
   Stick to Ribeira d'Ilhas or Foz do Lizandro for intermediate surfing.

   Want me to look into other spots along the coast?"
```

---

## 4. Implementation Order

Execute in this sequence to maintain a working system at each step:

| Step | Task | Files | Status |
|------|------|-------|--------|
| 1 | Add Azure OpenAI config | `config/settings.py`, `.env.example`, `.env` | ✅ Done |
| 2 | Add AzureOpenAIProvider | `app/core/llm_service.py` | ✅ Done |
| 3 | Create ForecastDataAgent (wraps existing forecasting clients + contextual providers) | `app/agents/forecast_data_agent.py` | ✅ Done |
| 4 | Create ConditionAssessmentAgent (wraps existing ConditionAssessor) | `app/agents/condition_agent.py` | ✅ Done |
| 5 | Create TripPlanningAgent (wraps existing SurfWindowFinder + TripPlanner) | `app/agents/trip_planning_agent.py` | ✅ Done |
| 6 | Create Orchestrator | `app/agents/orchestrator.py` | ✅ Done |
| 7 | Update entry point (keep /reset and /help only) | `app/__main__.py` | ✅ Done |
| 8 | Update package init files | `app/agents/__init__.py` | ✅ Done |
| 9 | Create unit tests for sub-agent tools | `tests/test_forecast_data_agent.py`, `tests/test_condition_agent.py`, `tests/test_trip_planning_agent.py` | ✅ Done |
| 10 | Deprecate old agents | `conversational.py`, `forecast_integration.py` | ✅ Done |
| 11 | Add Tavily config + dependency | `config/settings.py`, `.env.example`, `requirements.txt` | ✅ Done |
| 12 | Create ResearchAgent (Tavily web search + LLM extraction) | `app/agents/research_agent.py` | ✅ Done |
| 13 | Register ResearchAgent in Orchestrator + update system prompt | `app/agents/orchestrator.py` | ✅ Done |
| 14 | Remove static spot database from ForecastDataAgent | `app/agents/forecast_data_agent.py` | ✅ Done |
| 15 | Add ResearchAgent unit tests | `tests/test_research_agent.py` | ✅ Done |
| 16 | Clean up unused env vars | `.env.example` | ✅ Done |

---

## 5. Dependencies

The `openai>=1.6.1` package already in `requirements.txt` includes `AzureOpenAI`. The `tavily-python>=0.5.0` package was added for the ResearchAgent's web search capability.

```bash
pip install -r requirements.txt
python -c "from openai import AzureOpenAI; print('OK')"
python -c "from tavily import TavilyClient; print('OK')"
```

---

## 6. Resolved Design Decisions

The following questions were resolved during planning review:

### 6.1 Reuse of Existing Planning Module

**Decision**: New sub-agents **wrap and delegate to** the existing `app/planning/` module classes rather than rewriting the logic.

- `ConditionAssessmentAgent` wraps `app/planning/condition_assessor.ConditionAssessor`
- `TripPlanningAgent` wraps `app/planning/window_finder.SurfWindowFinder` and `app/planning/trip_planner.TripPlanner`
- `ForecastDataAgent` wraps existing `app/forecasting/` clients and `app/contextual/` providers

This means sub-agent methods act as **adapters** that translate between the OpenAI function-calling tool schema (JSON dicts with spot_name-based keys) and the existing module interfaces (which use `ForecastPoint`, `ConditionAssessment`, `SurfWindow` dataclasses). The orchestrator's `_enrich_args()` still bridges cross-tool data dependencies (e.g., injecting cached forecast data into `assess_conditions`).

### 6.2 Existing Module Fate

**Decision**: **KEEP ALL** existing modules — new agents import and wrap them.

| Module | Action | Notes |
|--------|--------|-------|
| `app/planning/condition_assessor.py` | **KEEP** | Wrapped by `ConditionAssessmentAgent` |
| `app/planning/window_finder.py` | **KEEP** | Wrapped by `TripPlanningAgent` |
| `app/planning/trip_planner.py` | **KEEP** | Wrapped by `TripPlanningAgent` |
| `app/planning/forecast_preview.py` | **KEEP** | May be used for formatting |
| `app/planning/travel_utils.py` | **KEEP** | Haversine and travel time calculations |
| `app/knowledge/spot_database.py` | **DEPRECATED** | Replaced by `ResearchAgent` — dynamic web search instead of static DB |
| `app/agents/research_agent.py` | **NEW** | Tavily web search + LLM extraction for any surf spot worldwide |
| `app/agents/contextual_agent.py` | **KEEP** | Wrapped by `ForecastDataAgent.fetch_contextual_info()` |
| `app/agents/trip_planning_state.py` | **KEEP** | Available for future state management needs |
| `app/agents/conversational.py` | **DEPRECATE** | Superseded by `orchestrator.py` |
| `app/agents/forecast_integration.py` | **DEPRECATE** | Logic absorbed by new agents |

### 6.3 Spot Database

**Decision**: ~~Keep hardcoded spots for now.~~ **Replaced with dynamic ResearchAgent.** The static `spot_database.py` and `KNOWN_SPOTS` dict have been removed from the active data flow. The `ForecastDataAgent` now receives spot coordinates and metadata from the orchestrator's session data, which is populated by the `ResearchAgent` via Tavily web search + LLM extraction. Any surf spot worldwide can be looked up at conversation time.

The `app/knowledge/` module and `data/spots.json` are retained as legacy/reference files but are no longer imported or used by any active agent.

### 6.4 Forecast API

**Decision**: Include **real Open-Meteo API calls** in `ForecastDataAgent`. Open-Meteo is free and requires no API key. The existing `app/forecasting/openmeteo_client.py` will be reused.

### 6.5 Streaming

**Decision**: **Batch response** (full response at once). Simpler to implement; streaming can be added later.

### 6.6 Slash Commands

**Decision**: Keep only `/reset` and `/help`. Remove all other slash commands (`/forecast`, `/assess`, `/windows`, `/trip`, `/context`, `/skill`). The orchestrator handles everything through natural conversation and function-calling.

### 6.7 Tests

**Decision**: Remove old tests. Create **unit tests** for the new sub-agent tools to verify they work correctly. No end-to-end tests for now.
