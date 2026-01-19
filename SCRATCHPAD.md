# SurfSense AI Agent Scratchpad

> **Purpose:** This document provides context for AI agents working on the SurfSense project.
> **Last Updated:** 2026-01-19
> **Project Status:** Active Development

---

## 🎯 Project Overview

**SurfSense** is a terminal-based conversational AI assistant for surf trip planning, built as part of a Master's Thesis project. It helps surfers find optimal surfing conditions by integrating weather forecasts, spot information, and contextual data.

### Key Features
- **Terminal chat interface** - No web server needed
- **Local LLM** - Uses Phi-3 mini via Hugging Face (free, runs locally)
- **Real forecast data** - Open-Meteo (free) + Stormglass (premium)
- **15 world-class surf spots** in database
- **3-layer agent architecture** matching thesis design

---

## 🏗️ Architecture

The system follows a **3-layer agent architecture** from the thesis:

```
┌─────────────────────────────────────────────────────────────┐
│                    Terminal Interface                        │
│                     (app/__main__.py)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│          LAYER 1: Conversational Agent Core                  │
│              (app/agents/conversational.py)                  │
│  • User-facing dialogue management                          │
│  • Personalization & preference tracking                    │
│  • Intent extraction                                        │
│  • Coordinates with other layers                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         │                                 │
┌────────▼────────┐               ┌────────▼────────┐
│    LAYER 2:     │               │    LAYER 3:     │
│   Contextual    │               │    Forecast     │
│     Layer       │               │  Integration    │
│ (app/contextual)│               │     Agent       │
│                 │               │(app/agents/     │
│ • Parking       │               │forecast_        │
│ • Accessibility │               │integration.py)  │
│ • Reviews       │               │                 │
│ • Safety        │               │ • Stormglass    │
└─────────────────┘               │ • Open-Meteo    │
                                  │ • Spot database │
                                  └─────────────────┘
```

---

## 📁 Project Structure

```
SurfSense/
├── app/
│   ├── __init__.py
│   ├── __main__.py              # Terminal chat entry point
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseAgent, AgentRole, AgentState
│   │   ├── conversational.py    # Layer 1: User-facing agent
│   │   └── forecast_integration.py  # Layer 3: Forecast APIs
│   ├── contextual/
│   │   ├── __init__.py
│   │   ├── base.py              # SpotContext, data models
│   │   ├── parking.py           # ParkingProvider
│   │   ├── accessibility.py     # AccessibilityProvider
│   │   ├── reviews.py           # ReviewsProvider
│   │   └── safety.py            # SafetyProvider
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm_service.py       # LLM providers (Local, OpenAI)
│   │   └── logger.py            # Structured logging, LoggerMixin
│   ├── forecasting/
│   │   ├── __init__.py
│   │   ├── models.py            # ForecastPoint, ForecastResponse, etc.
│   │   ├── stormglass_client.py # Stormglass API (requires key)
│   │   ├── openmeteo_client.py  # Open-Meteo API (FREE!)
│   │   ├── base_client.py       # ForecastAPIClient interface
│   │   └── noaa_client.py       # NOAA client (US only, not primary)
│   └── knowledge/
│       ├── __init__.py
│       └── spot_database.py     # SpotDatabase, search/filter
├── config/
│   ├── __init__.py
│   └── settings.py              # Pydantic settings, env vars
├── data/
│   └── spots.json               # 15 surf spots with full data
├── tests/
│   └── __init__.py
├── .env.example                 # Environment variable template
├── .gitignore
├── github_issues.md             # Project roadmap/issues
├── Makefile                     # Common commands
├── README.md                    # User documentation
├── requirements.txt             # Python dependencies
└── SCRATCHPAD.md               # This file (AI context)
```

---

## 🔧 Technical Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Language | Python 3.10+ | Virtual env at `.venv` |
| LLM | Phi-3 mini | Via Hugging Face transformers |
| Config | Pydantic + pydantic-settings | Type-safe, env vars |
| HTTP | httpx | Async HTTP client |
| Logging | structlog | Structured JSON logging |
| Forecasts | Open-Meteo (free), Stormglass | Real marine weather data |

### Key Dependencies
```
pydantic>=2.5.0
pydantic-settings>=2.1.0
transformers>=4.36.0
torch>=2.1.0
httpx>=0.25.2
structlog>=23.2.0
python-dotenv>=1.0.0
```

---

## 🌊 Forecast API Integration

### Priority Order
1. **Stormglass** (if `FORECAST_API_KEY` set) - Premium wave data
2. **Open-Meteo** (always available) - FREE, global coverage

### Open-Meteo (Primary - FREE)
- **No API key required**
- Global coverage at 5km resolution
- Up to 16 days forecast
- Marine + Weather data combined
- Endpoint: `https://marine-api.open-meteo.com/v1/marine`

### Stormglass (Premium)
- Requires API key (`FORECAST_API_KEY` in .env)
- Free tier: 10 requests/day
- Better wave detail
- Endpoint: `https://api.stormglass.io/v2`

### Data Models
```python
ForecastPoint:
  - timestamp: datetime
  - source: DataSource (stormglass, open_meteo, etc.)
  - waves: WaveData (height_min, height_max)
  - swell: SwellData (height, period, direction_degrees)
  - wind: WindData (speed, gust, direction_degrees)
  - tide: TideData (height)
  - weather: WeatherData (temperature, water_temperature, description)
```

---

## 🏄 Surf Spot Database

**Location:** `data/spots.json`
**Access:** `app/knowledge/spot_database.py`

### 15 Spots Included
| Region | Spots |
|--------|-------|
| Hawaii | Pipeline, Sunset Beach, Waikiki |
| California | Mavericks, Huntington Beach, San Onofre, Trestles, Rincon |
| Pacific | Teahupo'o (Tahiti) |
| Europe | Nazaré (Portugal), Hossegor (France) |
| Africa | Jeffreys Bay (South Africa) |
| Asia | Uluwatu (Bali) |
| Australia | Bells Beach, Gold Coast |

### Spot Data Structure
```python
SpotInfo:
  - id, name
  - location: region, country, lat/lon, timezone
  - characteristics: break_type, wave_direction, bottom, crowd_level
  - skill_levels: minimum, recommended, beginner_friendly
  - best_conditions: swell_direction, size, wind, tide, season
  - hazards, facilities, description, local_tips
```

### Search Methods
```python
db = get_spot_database()
db.search_by_name("pipe")              # Fuzzy name search
db.search_by_region("North Shore")     # Region filter
db.filter_by_skill(SkillLevel.BEGINNER)  # Skill filter
db.filter_by_break_type(BreakType.POINT) # Break type
db.find_nearby(lat, lon, radius_km=50)   # Distance search
db.get_spots_for_conditions(swell="NW")  # Condition match
```

---

## ✅ Completed Issues (1-19)

### Phase 1: Foundation ✅
- Issue #1: Project structure
- Issue #2: Skipped (code quality tools)
- Issue #3: Configuration management (Pydantic)
- Issue #4: Logging system (structlog)

### Phase 2: LLM Core ✅
- Issue #5: Local LLM service (Phi-3 mini)
- Issue #6: Terminal chat interface

### Phase 3: Agent Architecture ✅
- Issue #7: Forecast data schema
- Issue #8: Base agent framework
- Issue #9: Layer 1 - Conversational Agent
- Issue #10: Layer 3 - Forecast Integration Agent
- Issue #11: Layer 2 - Contextual Data Layer
- Issue #12: Terminal interface with agents

### Phase 4: Forecast API ✅
- Issue #13: Stormglass API client
- Issue #14: Open-Meteo integration (enrichment)

### Phase 5: Knowledge ✅
- Issue #15: Surf spot database
- Issue #16: Contextual Layer Integration

### Phase 6: Planning Engine ✅
- Issue #17: Condition Assessment
- Issue #18: Surf Window Finder
- Issue #19: Trip Planner

---

## 🚧 Remaining Issues (20-21)

### Issue #20: Unit Tests
- Test forecast clients
- Test spot database
- Test condition assessment
- Test window finder
- Test trip planner

### Issue #21: Documentation
- API documentation
- User guide
- Developer guide

---

## 🔑 Key Code Patterns

### LoggerMixin Usage
```python
from app.core.logger import LoggerMixin

class MyClass(LoggerMixin):
    def my_method(self):
        self.log_info("Message", key="value")
        self.log_warning("Warning message")
        self.log_error("Error message")
```

### Async Forecast Fetching
```python
from app.agents import ForecastIntegrationAgent

agent = ForecastIntegrationAgent()
result = await agent.get_forecast("Pipeline", days=3)
# Returns dict with: spot, source, coordinates, forecast_count, forecasts
```

### Spot Database Access
```python
from app.knowledge import get_spot_database, SkillLevel

db = get_spot_database()
spot = db.get_spot("pipeline")
coords = db.get_coordinates("waikiki")  # Returns (lat, lon)
```

### Settings Access
```python
from config.settings import get_settings

settings = get_settings()
api_key = settings.forecast.api_key
log_level = settings.logging.level
```

---

## 🏃 Running the Project

### Setup
```bash
cd /Users/jwehr/Desktop/Master\ Thesis\ Project/SurfSense
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run Chat
```bash
python -m app
```

### Slash Commands (in chat)
- `/forecast <spot>` - Get forecast for a spot
- `/skill <level>` - Set skill level (beginner/intermediate/advanced/expert)
- `/reset` - Reset conversation
- `/help` - Show help

---

## ⚠️ Known Issues / TODOs

1. **LLM Integration Incomplete**: ConversationalAgent has basic LLM setup but full integration with tools is pending
2. ~~**Contextual Layer Not Wired**: Providers exist but aren't connected to agent tools yet~~ ✅ Fixed
3. ~~**Planning Engine Missing**~~ Condition Assessment complete, Trip Planner (Issues #18-19) pending
4. **No Tests**: Test suite is empty

---

## 📝 Recent Changes (2026-01-19)

1. **Issue #17 Completed**: Condition Assessment
   - Created `app/planning/` module with `ConditionAssessor`
   - Skill-based thresholds from config (beginner/intermediate/advanced)
   - Ratings: ideal, suitable, challenging, unsafe
   - Safety warnings for conditions exceeding skill limits
   - Integrated with `ForecastIntegrationAgent.assess_conditions()`
   - Added `/assess <spot> [skill]` terminal command
2. **Issue #16 Completed**: Contextual Layer Integration
   - Created `ContextualAgent` class that aggregates all contextual providers
   - Added `get_spot_context` tool to ConversationalAgent
   - Updated `_tool_get_spot_info` to include contextual data
   - Added `/context <spot>` command for terminal interface
   - Wired ContextualAgent into the chat loop
3. Added Open-Meteo Marine Weather API client (FREE, no API key)
4. Updated ForecastIntegrationAgent to use Open-Meteo as fallback
5. Removed mock data - now uses real APIs only
6. Added `OPEN_METEO` to DataSource enum
7. Created comprehensive spot database with 15 spots
8. Integrated spot database with forecast agent

---

## 🎓 Thesis Context

This project is part of a Master's Thesis on conversational AI for surf trip planning. The 3-layer architecture is a key design decision from the thesis:

1. **Layer 1 (Conversational)**: Handles user interaction, preference learning, dialogue management
2. **Layer 2 (Contextual)**: Provides auxiliary info (parking, safety, reviews, accessibility)
3. **Layer 3 (Forecast)**: Integrates weather/surf forecast APIs

The goal is to demonstrate how a conversational agent can help surfers plan trips by combining multiple data sources with personalized recommendations based on skill level.

---

## 🔗 Quick References

- **Main entry**: `app/__main__.py`
- **Settings**: `config/settings.py`
- **Forecast agent**: `app/agents/forecast_integration.py`
- **Spot database**: `app/knowledge/spot_database.py`
- **Open-Meteo client**: `app/forecasting/openmeteo_client.py`
- **Project roadmap**: `github_issues.md`
