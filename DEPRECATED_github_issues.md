# SurfSense - GitHub Issues

## Project Overview

SurfSense is a **terminal-based conversational AI** for surf trip planning, powered by a **free local LLM** (Phi-3 mini). No API keys required for basic usage!

### Architecture

The system follows a **3-layer agent architecture** with an **ML-enhanced condition scoring** pipeline:

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
│ • Safety        │               │ • Forecast APIs │
│                 │               │ • Data analysis │
└─────────────────┘               │ • Caching       │
                                  └────────┬────────┘
                                           │
                                  ┌────────▼────────┐
                                  │   ML Condition  │
                                  │     Model       │
                                  │ (app/ml/)       │
                                  │                 │
                                  │ • XGBoost model │
                                  │ • Feature eng.  │
                                  │ • Scoring 0-100 │
                                  └─────────────────┘
```

### ML Model Integration (Mini Project)

The condition scoring in `ConditionAssessor` is replaced by a fine-tuned
XGBoost/LightGBM model trained on historical surf condition data. The model
predicts a surf quality score (0–100) from the same `ForecastPoint` features
the rule-based system used (wave height, swell period, wind speed, etc.).

```
Forecast APIs ──► ForecastPoint ──► Feature Extractor ──► XGBoost ──► score 0-100
                                                                         │
                                                          ConditionAssessor
                                                                         │
                                                     SurfWindow / TripPlanner
```

---

## Phase 1: Foundation ✅ COMPLETED

### Issue #1: Initialize Python Project Structure
**Labels:** setup, infrastructure  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Set up the foundational Python project structure for SurfSense terminal chat app.

**Completed Tasks:**
- [x] Create project directory structure following clean architecture
- [x] Initialize Python virtual environment (Python 3.10+)
- [x] Create `requirements.txt` with core dependencies
- [x] Set up `.env.example` for configuration templates
- [x] Create `.gitignore` for Python projects
- [x] Add `README.md` with setup instructions
- [x] Create basic project structure

**Acceptance Criteria:** ✅
- Project runs with `python -m app`
- All dependencies install without errors
- Clean, documented folder structure

---

### Issue #2: Code Quality Tools (SKIPPED)
**Labels:** setup, code-quality  
**Priority:** Low  
**Status:** ⏭️ Skipped (solo developer)

**Note:** Skipped for solo development. Clean code maintained through careful coding practices.

---

### Issue #3: Implement Configuration Management System
**Labels:** infrastructure, core  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Create a centralized, type-safe configuration system using Pydantic.

**Completed Tasks:**
- [x] Create `config/settings.py` with Pydantic models
- [x] Support environment variables via `.env` file
- [x] Define configuration sections:
  - LLM settings (provider, model, temperature, max tokens)
  - Forecast API settings
  - Skill level thresholds
  - Logging configuration
- [x] Implement configuration validation on startup
- [x] Add clear error messages for missing settings
- [x] Document all configuration options in README

**Acceptance Criteria:** ✅
- Configuration loads from environment variables
- Invalid configuration raises clear errors
- All settings are type-safe and validated

---

### Issue #4: Set Up Logging System
**Labels:** infrastructure, observability  
**Priority:** Medium  
**Status:** ✅ Complete

**Description:**
Implement consistent logging across all components.

**Completed Tasks:**
- [x] Create `app/core/logger.py` with structured logging
- [x] Configure log levels (DEBUG, INFO, WARNING, ERROR)
- [x] Include timestamps, module names, and log levels
- [x] Support file and console output
- [x] Filter sensitive data (API keys) from logs
- [x] Add API request/response logging helpers
- [x] Add `LoggerMixin` with convenience methods (log_info, log_debug, etc.)

**Acceptance Criteria:** ✅
- Logs are readable and consistently formatted
- Easy to filter by component or severity
- No sensitive data in logs

---

## Phase 2: LLM Core ✅ COMPLETED

### Issue #5: Implement Local LLM Service
**Labels:** llm, core  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Build the conversational AI using a free local LLM (Phi-3 mini) via Hugging Face Transformers.

**Completed Tasks:**
- [x] Create `app/core/llm_service.py` with clean interface
- [x] Implement `LocalLLMProvider` using Hugging Face Transformers
- [x] Support Phi-3 mini model (free, runs locally)
- [x] Auto-detect GPU (CUDA/MPS) or fallback to CPU
- [x] Define system prompt for SurfSense persona
- [x] Add error handling for model loading failures
- [x] Implement `OpenAILLMProvider` as alternative option
- [x] Create unified `LLMService` interface

**Acceptance Criteria:** ✅
- LLM responds to basic surf queries
- Works offline (after initial model download)
- Handles errors gracefully
- Code is clear and well-documented

---

### Issue #6: Create Terminal Chat Interface
**Labels:** interface, core  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Build interactive terminal chat for conversation with the AI.

**Completed Tasks:**
- [x] Update `app/__main__.py` with chat loop
- [x] Display welcome banner and configuration summary
- [x] Handle user input with graceful exit (quit/exit/Ctrl+C)
- [x] Show loading indicator while model initializes
- [x] Display formatted responses

**Acceptance Criteria:** ✅
- Chat works smoothly in terminal
- Graceful handling of exit commands
- Clear visual feedback

---

## Phase 3: Agent Architecture ✅ COMPLETED

### Issue #7: Design Unified Forecast Data Schema
**Labels:** forecasting, data-model  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Create a consistent internal data model for surf forecasts.

**Completed Tasks:**
- [x] Create `app/forecasting/models.py` with Pydantic models
- [x] Define `ForecastPoint` model with all required fields
- [x] Define `ForecastResponse` with list of forecast points
- [x] Add validation rules (wave height > 0, direction ranges, etc.)
- [x] Include spot metadata (name, coordinates, timezone)
- [x] Add helper methods (summary, best_conditions, unit conversions)
- [x] Auto-compute cardinal directions from degrees

**Models Created:**
- `ForecastPoint` - Single forecast data point
- `ForecastResponse` - Complete forecast with metadata
- `WaveData`, `SwellData`, `WindData`, `TideData`, `WeatherData`
- `SpotMetadata`, `Coordinates`
- Enums: `WindDirection`, `SwellDirection`, `TideState`, `DataSource`

**Acceptance Criteria:** ✅
- Schema validates all required fields
- Clear field names and types
- Works with multiple forecast sources

---

### Issue #8: Implement Base Agent Framework
**Labels:** agents, architecture  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Create the foundational agent framework for the 3-layer architecture.

**Completed Tasks:**
- [x] Create `app/agents/base.py` with `BaseAgent` abstract class
- [x] Define `AgentRole` enum (conversational, forecast_integration, contextual)
- [x] Implement `AgentState` for tracking conversation/context
- [x] Implement `AgentMessage` for conversation history
- [x] Add tool registration system (`register_tool`, `call_tool`)
- [x] Add user preference management (`update_user_preference`, `get_user_preference`)
- [x] Add context management (`set_context`, `get_context`)

**Components Created:**
- `BaseAgent` - Abstract base class with state, tools, preferences
- `AgentRole` - Enum defining agent types
- `AgentState` - Tracks conversation history, preferences, context
- `AgentMessage` - Single message in conversation

**Acceptance Criteria:** ✅
- Clean abstract interface for all agents
- State management works correctly
- Tool system is extensible

---

### Issue #9: Implement Layer 1 - Conversational Agent
**Labels:** agents, layer-1  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Build the user-facing conversational agent (Layer 1 of the architecture).

**Completed Tasks:**
- [x] Create `app/agents/conversational.py`
- [x] Implement dialogue management with LLM
- [x] Track user preferences (skill level, preferred spots)
- [x] Extract preferences from natural language
- [x] Build prompts with context and history
- [x] Coordinate with ForecastIntegrationAgent
- [x] Register tools for forecast queries and skill setting

**Tools Registered:**
- `get_forecast` - Get surf forecast via Layer 3
- `set_user_skill` - Set user's skill level
- `get_spot_info` - Get spot information (contextual layer)

**Acceptance Criteria:** ✅
- Natural dialogue flow
- Remembers user preferences across turns
- Coordinates with other agents

---

### Issue #10: Implement Layer 3 - Forecast Integration Agent
**Labels:** agents, layer-3  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Build the forecast integration agent (Layer 3 of the architecture).

**Completed Tasks:**
- [x] Create `app/agents/forecast_integration.py`
- [x] Implement forecast fetching with caching
- [x] Generate mock forecast data for development
- [x] Analyze conditions for surf quality
- [x] Find best surfing windows in forecast
- [x] Convert forecast to dictionary for API use

**Tools Registered:**
- `fetch_forecast` - Fetch raw forecast data
- `analyze_conditions` - Rate conditions for skill level
- `find_best_window` - Find optimal surf times

**Acceptance Criteria:** ✅
- Returns forecast data in unified format
- Caching reduces redundant calls
- Analysis provides useful insights

---

### Issue #11: Implement Layer 2 - Contextual Data Layer
**Labels:** contextual, layer-2  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Build the contextual data layer for auxiliary information (Layer 2).

**Completed Tasks:**
- [x] Create `app/contextual/base.py` with data models
- [x] Define `SpotContext` unified model
- [x] Create `ParkingProvider` with sample data
- [x] Create `AccessibilityProvider` with sample data
- [x] Create `ReviewsProvider` with sample data
- [x] Create `SafetyProvider` with sample data

**Data Models Created:**
- `SpotContext` - Complete contextual info for a spot
- `ParkingInfo` - Parking type, cost, capacity, distance
- `AccessibilityInfo` - Wheelchair access, paths, facilities
- `ReviewSummary` - Ratings, highlights, concerns
- `SafetyInfo` - Hazards, lifeguards, warnings

**Providers:**
| Provider | Data |
|----------|------|
| `ParkingProvider` | Parking info (Pipeline, Waikiki, Sunset Beach) |
| `AccessibilityProvider` | Access info (Waikiki, Pipeline, San Onofre) |
| `ReviewsProvider` | Reviews (Pipeline, Waikiki, Mavericks) |
| `SafetyProvider` | Safety (Pipeline, Waikiki, Mavericks, Huntington) |

**Acceptance Criteria:** ✅
- Unified data models for all contextual data
- Sample data for development
- Easy to extend with real data sources

---

### Issue #12: Update Terminal Interface for Agent Architecture
**Labels:** interface, agents  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Update the terminal chat to use the new agent architecture.

**Completed Tasks:**
- [x] Update `app/__main__.py` to use `ConversationalAgent`
- [x] Initialize `ForecastIntegrationAgent` on startup
- [x] Add slash commands for direct actions
- [x] Use async for agent processing

**Commands Added:**
- `/forecast <spot>` - Get forecast via ForecastIntegrationAgent
- `/skill <level>` - Set skill level preference
- `/reset` - Reset conversation state
- `/help` - Show available commands

**Acceptance Criteria:** ✅
- Chat uses full agent architecture
- Commands provide direct access to features
- Async processing works correctly

---

## Phase 4: Forecast API Integration ✅ COMPLETED

### Issue #13: Implement Stormglass API Client
**Labels:** forecasting, api-integration  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Build API client for fetching real-time surf forecasts from Stormglass.

**Completed Tasks:**
- [x] Create `app/forecasting/stormglass_client.py`
- [x] Implement async HTTP client for Stormglass API
- [x] Transform API responses to unified schema
- [x] Add request timeout handling (10 seconds)
- [x] Integrate with `ForecastIntegrationAgent` cache
- [x] Log API calls and response times
- [x] Handle rate limiting gracefully
- [x] Add clear error messages for failures
- [x] Add known surf spots database (15 spots with coordinates)
- [x] Implement fallback to mock data when no API key

**Components Created:**
- `StormglassClient` - Async HTTP client for Stormglass API
- `StormglassAPIError` - Custom exception for API errors
- `fetch_stormglass_forecast()` - Convenience function

**Known Surf Spots (15):**
Pipeline, Sunset Beach, Waikiki, Mavericks, Huntington Beach, San Onofre, Trestles, Rincon, Teahupoo, Nazare, Hossegor, Jeffreys Bay, Uluwatu, Bells Beach, Gold Coast

**Acceptance Criteria:** ✅
- Successfully fetches forecast data (or falls back to mock)
- Transforms to internal schema correctly
- Handles network errors without crashing

---

### Issue #14: Add Alternative Forecast Sources
**Labels:** forecasting, api-integration  
**Priority:** Low  
**Status:** ✅ Complete

**Description:**
Add support for additional forecast data sources.

**Completed Tasks:**
- [x] Create abstract interface for forecast API clients (`ForecastAPIClient`)
- [x] Implement NOAA data source (free, no API key required!)
- [x] Add source selection logic to ForecastIntegrationAgent
- [x] Fall back to mock data if APIs unavailable
- [x] Support location-based client selection (NOAA = US waters only)

**Components Created:**
- `ForecastAPIClient` - Abstract base class for all forecast clients
- `ForecastClientRegistry` - Registry for managing multiple clients
- `NOAAClient` - NOAA marine weather API client (FREE!)
- `fetch_noaa_forecast()` - Convenience function

**Source Priority Order:**
1. **Stormglass** (if API key configured) - Global coverage, detailed wave data
2. **NOAA** (always available) - US coastal waters only, wind/weather focus
3. **Mock Data** (fallback) - Always works, simulated data

**NOAA Coverage:**
- US Continental Coasts (24.5°N - 49°N, 125°W - 66°W)
- Hawaiian Islands (18°N - 23°N, 161°W - 154°W)

**Acceptance Criteria:** ✅
- Multiple data sources supported
- Graceful fallback behavior
- NOAA works without any API key

---

## Phase 5: Knowledge Integration ✅ COMPLETED

### Issue #15: Create Surf Spot Database
**Labels:** knowledge, data  
**Priority:** Medium  
**Status:** ✅ Complete

**Description:**
Build comprehensive surf spot database.

**Completed Tasks:**
- [x] Create `data/spots.json` with 15 world-class surf spots
- [x] Define comprehensive `SpotInfo` model with:
  - Name, coordinates, timezone
  - Break type, wave direction, bottom type
  - Skill levels (minimum, recommended, beginner-friendly)
  - Best conditions (swell, wind, tide, season)
  - Hazards, facilities, description, local tips
- [x] Create `app/knowledge/spot_database.py` with `SpotDatabase` class
- [x] Implement search functionality:
  - Search by name (fuzzy matching)
  - Filter by region/country
  - Filter by skill level
  - Filter by break type
  - Find nearby spots (Haversine distance)
  - Match spots to conditions
- [x] Integrate with ForecastIntegrationAgent

**Spots Included (15):**
| Region | Spots |
|--------|-------|
| Hawaii | Pipeline, Sunset Beach, Waikiki |
| California | Mavericks, Huntington Beach, San Onofre, Trestles, Rincon |
| Pacific Islands | Teahupo'o (Tahiti) |
| Europe | Nazaré (Portugal), Hossegor (France) |
| South Africa | Jeffreys Bay |
| Asia | Uluwatu (Bali) |
| Australia | Bells Beach, Gold Coast |

**Search Features:**
- `search_by_name("pipe")` → Pipeline
- `search_by_region("North Shore")` → Pipeline, Sunset Beach
- `filter_by_skill(SkillLevel.BEGINNER)` → Beginner-friendly spots
- `filter_by_break_type(BreakType.POINT)` → Point breaks
- `find_nearby(lat, lon, radius_km)` → Distance-sorted results
- `get_spots_for_conditions(swell="NW", size=6)` → Matching spots

**Acceptance Criteria:** ✅
- Comprehensive spot data with 15 world-class spots
- Fast search functionality with multiple filters
- JSON is human-editable

---

### Issue #16: Integrate Contextual Layer with Agents
**Labels:** contextual, agents  
**Priority:** Medium  
**Status:** ✅ Complete

**Description:**
Connect contextual data providers to the agent system.

**Completed Tasks:**
- [x] Create `ContextualAgent` class in `app/agents/contextual_agent.py`
- [x] Aggregate data from all providers (Parking, Accessibility, Reviews, Safety)
- [x] Add `get_spot_context` tool to ConversationalAgent
- [x] Add `/context <spot>` command to terminal interface
- [x] Include contextual info in `get_spot_info` tool
- [x] Add `format_context_for_display()` for terminal output

**Components Created:**
- `ContextualAgent` - Aggregates all contextual providers
- Tools: `get_spot_context`, `get_parking_info`, `get_safety_info`, `get_accessibility_info`, `get_reviews`
- Serialization helpers for dict conversion

**Terminal Command:**
- `/context <spot>` - Display parking, safety, reviews, accessibility info

**Acceptance Criteria:** ✅
- Agents can access all contextual data
- Recommendations include parking/safety info
- Terminal displays formatted contextual information

---

## Phase 6: Planning Engine ✅ COMPLETED

### Issue #17: Implement Condition Assessment
**Labels:** planning, business-logic  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Build rules for matching conditions to skill levels.

**Completed Tasks:**
- [x] Create `app/planning/` module with `__init__.py`
- [x] Create `app/planning/condition_assessor.py` with:
  - `ConditionAssessor` class for skill-based evaluation
  - `ConditionRating` enum (ideal, suitable, challenging, unsafe)
  - `ConditionAssessment` dataclass with full analysis
- [x] Use thresholds from configuration:
  - Beginner: max 1.5m waves, 15 km/h wind
  - Intermediate: max 2.5m waves, 20 km/h wind  
  - Advanced: max 5.0m waves, 30 km/h wind
- [x] Score based on wave height, swell period, and wind conditions
- [x] Include reasoning and safety warnings
- [x] Integrate with `ForecastIntegrationAgent`
- [x] Add `/assess <spot> [skill]` terminal command

**Components Created:**
- `ConditionAssessor` - Main assessment logic
- `ConditionRating` - Rating enum (ideal/suitable/challenging/unsafe)
- `ConditionAssessment` - Full assessment with factors and warnings
- `SkillLevel` - Skill level enum
- `WindCondition` - Wind condition categories

**Key Methods:**
- `assess(forecast, skill_level)` - Assess single forecast point
- `assess_forecast_range(forecasts, skill_level)` - Assess multiple points
- `find_best_conditions(forecasts, skill_level)` - Find best windows
- `get_daily_summary(forecasts, skill_level)` - Daily overview

**Terminal Command:**
- `/assess <spot> [skill]` - Assess conditions for skill level

**Acceptance Criteria:** ✅
- Assessments match expected outcomes based on thresholds
- Clear safety warnings for conditions exceeding skill limits
- Integrated with forecast agent and terminal interface

---

### Issue #18: Surf Window Finder
**Labels:** planning, core  
**Priority:** High  
**Status:** ✅ Complete

**Description:**
Find optimal surfing windows within a forecast by identifying contiguous 
periods of favorable conditions.

**Completed Tasks:**
- [x] Create `app/planning/window_finder.py`
- [x] Implement `SurfWindowFinder` class with:
  - Window grouping algorithm for consecutive good hours
  - Quality ratings (epic, excellent, good, fair, poor)
  - Duration, score, and factor tracking
- [x] Weight factors: wave quality, swell period, wind conditions
- [x] Integrate with `ForecastIntegrationAgent`:
  - `find_surf_windows()` method
  - `find_windows_by_day()` method
- [x] Add `/windows <spot> [skill] [days]` terminal command

**Components Created:**
- `SurfWindowFinder` - Main window finding logic
- `SurfWindow` - Dataclass for a contiguous surf window
- `WindowQuality` - Quality rating enum
- `WindowFinderResult` - Complete result with recommendations

**Key Methods:**
- `find_windows(forecasts, skill_level)` - Find all windows
- `find_best_window(forecasts, skill_level)` - Find single best
- `find_windows_by_day(forecasts, skill_level)` - Group by day

**Terminal Command:**
- `/windows <spot> [skill] [days]` - Find optimal surf windows

**Acceptance Criteria:** ✅
- Identifies contiguous periods of favorable conditions
- Groups windows with quality ratings and recommendations
- Integrated with terminal interface

---

### Issue #19: Trip Planner
**Labels:** planning, core  
**Priority:** Medium  
**Status:** ✅ Complete

**Description:**
Create planning logic for multi-day surf trip itineraries.

**Completed Tasks:**
- [x] Create `app/planning/trip_planner.py`
- [x] Implement `TripPlanner` class with data models:
  - `TripSpot` - spot with windows and contextual scores
  - `SurfSession` - individual planned session
  - `TripDay` - day's schedule with sessions
  - `TripItinerary` - complete multi-day trip plan
  - `SessionPriority` enum (must_surf, preferred, optional, backup)
- [x] Multi-spot itinerary planning
- [x] Time/distance optimization (Haversine formula)
- [x] Weather-aware scheduling (best windows first)
- [x] Include contextual factors (parking, crowds, safety scores)
- [x] Automatic rest day scheduling (every 3 consecutive surf days)
- [x] Integrate with ForecastIntegrationAgent

**Key Methods:**
- `plan_trip(spots_data, forecasts, skill_level, days)` - Full multi-day itinerary
- `plan_single_day(spots_data, forecasts, skill_level)` - Single day plan
- `suggest_best_spot(spots_data, forecasts, skill_level)` - Best spot recommendation

**Terminal Command:**
- `/trip <spot1,spot2,...> [skill] [days]` - Plan multi-day trip

**Acceptance Criteria:** ✅
- Generates coherent multi-day plans with sessions
- Clear reasoning for recommendations
- Automatic rest days after consecutive surf days
- Considers travel distance and contextual factors

---

## Phase 7: Guided Trip Planning Flow 

### Issue #22: Implement Guided Information Gathering
**Labels:** agents, conversation, ux  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**
Enhance the Conversational Agent to systematically gather required trip information through natural dialogue before creating a trip plan.

**Required Information to Collect:**
| Field | Description | Example |
|-------|-------------|---------|
| `skill_level` | User's surfing ability | beginner, intermediate, advanced |
| `destination` | Where they want to surf | "San Diego", "North Shore", "Pipeline" |
| `origin` | Where they're traveling from | "Los Angeles", "San Francisco" |
| `transport_mode` | How they plan to travel | car, public_transport |
| `surf_dates` | When they plan to surf | "next weekend", "Jan 28-30", "tomorrow" |

**Tasks:**
- [ ] Create `TripPlanningState` dataclass to track gathered info
- [ ] Add `RequiredField` enum for tracking completion status
- [ ] Implement `_check_missing_info()` method in ConversationalAgent
- [ ] Create natural question prompts for each missing field
- [ ] Add date parsing for flexible date inputs (relative & absolute)
- [ ] Support multi-day date ranges
- [ ] Update system prompt to guide LLM questioning behavior
- [ ] Add `/status` command to show current planning state

**Conversation Flow:**
```
User: I want to plan a surf trip

SurfSense: Great! I'd love to help you plan your surf trip! 🏄
           First, what's your surfing skill level? 
           (beginner, intermediate, or advanced)

User: I'm intermediate

SurfSense: Nice! Intermediate surfers have lots of great options.
           Where would you like to go surfing?

User: Somewhere in San Diego

SurfSense: San Diego is awesome! There's La Jolla, Blacks Beach, 
           Ocean Beach... Where will you be traveling from?

User: I'm coming from LA

SurfSense: Got it - LA to San Diego is a nice drive! 
           Will you be driving or taking public transport?

User: Driving

SurfSense: Perfect, I'll include parking info in your plan.
           When are you planning to surf? (e.g., "next weekend", 
           "January 28-30", or specific dates)

User: Next Saturday and Sunday

SurfSense: ✅ I have everything I need! Let me check the forecast 
           for San Diego spots on Jan 31 - Feb 1...
```

**Components to Create:**
- `app/agents/trip_planning_state.py` - State tracking for planning flow
- Update `app/agents/conversational.py` - Guided questioning logic

**Acceptance Criteria:**
- Agent naturally asks for each missing piece of information
- Accepts flexible date formats (relative and absolute)
- Tracks state across conversation turns
- Clear confirmation when all info is gathered

---

### Issue #23: Add Origin & Transportation Support
**Labels:** data-model, contextual  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**
Extend the system to handle user origin location and transportation mode for travel planning.

**Tasks:**
- [ ] Add `origin` and `transport_mode` to user preferences in AgentState
- [ ] Create `TransportMode` enum (car, public_transport)
- [ ] Implement travel time estimation:
  - Driving: Use Haversine distance with average speed
  - Public transport: Estimate based on region (longer times)
- [ ] Add parking relevance flag (only show parking for car travelers)
- [ ] Update contextual layer to filter info based on transport mode
- [ ] Store common origin locations for quick reference

**Data Model Updates:**
```python
class TransportMode(str, Enum):
    CAR = "car"
    PUBLIC_TRANSPORT = "public_transport"

class TripPreferences(BaseModel):
    skill_level: SkillLevel
    destination: str
    origin: str
    origin_coordinates: Optional[Coordinates]
    transport_mode: TransportMode
    surf_dates: list[date]
```

**Travel Time Logic:**
- Car: `distance_km / 80 km/h` (average highway speed)
- Public Transport: `distance_km / 40 km/h` (accounting for transfers)
- Add buffer time for each mode

**Acceptance Criteria:**
- Origin location stored and used for travel calculations
- Transport mode affects what contextual info is shown
- Parking info only displayed when transport_mode = car

---

### Issue #24: Implement Forecast Preview & Confirmation Flow
**Labels:** agents, ux, forecast  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**
After gathering all trip info, show the user a forecast preview and wait for confirmation before generating the full itinerary.

**Tasks:**
- [ ] Create `ForecastPreview` display format
- [ ] Fetch forecasts for all requested dates
- [ ] Show condensed daily summaries with ratings
- [ ] Highlight best windows per day
- [ ] Ask user to confirm or adjust dates
- [ ] Handle user modifications (different dates, spots)
- [ ] Add "looks good" / "let me change" response handling

**Preview Format:**
```
📊 Forecast Preview for San Diego (Jan 31 - Feb 1)

┌─────────────────────────────────────────────────────┐
│ 📅 Saturday, January 31                             │
├─────────────────────────────────────────────────────┤
│ 🌊 Waves: 1-1.5m | 🌬️ Wind: 8 km/h offshore          │
│ 🏄 Rating: ⭐⭐⭐⭐ EXCELLENT for intermediate       │
│ ⏰ Best Window: 6:00 AM - 10:00 AM                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 📅 Sunday, February 1                               │
├─────────────────────────────────────────────────────┤
│ 🌊 Waves: 0.6-1.2m | 🌬️ Wind: 12 km/h cross-shore      │
│ 🏄 Rating: ⭐⭐⭐ GOOD for intermediate              │
│ ⏰ Best Window: 7:00 AM - 11:00 AM                  │
└─────────────────────────────────────────────────────┘

Does this look good? Say "yes" to generate your itinerary,
or tell me if you'd like to check different dates.
```

**State Transitions:**
```
GATHERING_INFO → INFO_COMPLETE → SHOWING_PREVIEW → 
    → (user confirms) → GENERATING_ITINERARY
    → (user adjusts) → GATHERING_INFO (partial)
```

**Acceptance Criteria:**
- Clear, visual forecast preview
- User can confirm or request changes
- Smooth transition to itinerary generation

---

### Issue #25: Calendar-Format Itinerary Generator
**Labels:** planning, output, ux  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**
Generate a complete trip itinerary in a clean calendar format, including all contextual information (parking, conditions, timing).

**Tasks:**
- [ ] Create `CalendarItinerary` output formatter
- [ ] Design ASCII calendar grid layout
- [ ] Include per-day breakdown:
  - Departure time from origin
  - Travel duration
  - Arrival time at spot
  - Surf session window
  - Parking information (if driving)
  - Conditions summary
  - Return time estimate
- [ ] Add session preparation tips
- [ ] Generate shareable text format
- [ ] Add `/calendar` command to regenerate last itinerary

**Calendar Output Format:**
```
═══════════════════════════════════════════════════════════════
🏄 SURF TRIP ITINERARY: San Diego
📅 January 31 - February 1, 2026
🚗 From: Los Angeles (driving)
═══════════════════════════════════════════════════════════════

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📅 SATURDAY, JANUARY 31                                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                              ┃
┃ 🚗 TRAVEL                                                    ┃
┃    Depart LA: 4:30 AM                                        ┃
┃    Drive time: ~2 hours                                      ┃
┃    Arrive La Jolla: 6:30 AM                                  ┃
┃                                                              ┃
┃ 🏄 SURF SESSION @ La Jolla Shores                            ┃
┃    Window: 6:30 AM - 10:30 AM (4 hours)                      ┃
┃    Conditions: 1-1.2m, offshore wind, EXCELLENT               ┃
┃    Water temp: 17°C - consider 4/3 wetsuit                   ┃
┃                                                              ┃
┃ 🅿️ PARKING                                                   ┃
┃    Location: Kellogg Park Lot                                ┃
┃    Cost: Free before 8 AM, then $3/hr                        ┃
┃    Tip: Arrive early, fills up by 8 AM on weekends           ┃
┃                                                              ┃
┃ 🏠 RETURN                                                    ┃
┃    Depart: 11:00 AM                                          ┃
┃    Arrive LA: ~1:00 PM                                       ┃
┃                                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📅 SUNDAY, FEBRUARY 1                                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                              ┃
┃ 🚗 TRAVEL                                                    ┃
┃    Depart LA: 5:00 AM                                        ┃
┃    Drive time: ~2.5 hours (traffic lighter)                  ┃
┃    Arrive Blacks Beach: 7:30 AM                              ┃
┃                                                              ┃
┃ 🏄 SURF SESSION @ Blacks Beach                               ┃
┃    Window: 7:30 AM - 11:00 AM (3.5 hours)                    ┃
┃    Conditions: 1.2-1.5m, light cross-shore, GOOD                ┃
┃    ⚠️ Note: Steep trail access, intermediate+ recommended    ┃
┃                                                              ┃
┃ 🅿️ PARKING                                                   ┃
┃    Location: Gliderport parking lot                          ┃
┃    Cost: $5 flat rate                                        ┃
┃    Tip: 10-15 min hike down to beach                         ┃
┃                                                              ┃
┃ 🏠 RETURN                                                    ┃
┃    Depart: 11:30 AM                                          ┃
┃    Arrive LA: ~2:00 PM                                       ┃
┃                                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

═══════════════════════════════════════════════════════════════
📝 TRIP SUMMARY
═══════════════════════════════════════════════════════════════
Total surf time: 7.5 hours across 2 sessions
Total drive time: ~9 hours round-trip
Estimated fuel cost: ~$45 (assuming 25 mpg)
Best day: Saturday @ La Jolla (EXCELLENT conditions)

💡 TIPS:
• Pack food - limited options near Blacks Beach
• Check Surfline morning of for last-minute changes
• Bring sunscreen - forecast shows clear skies both days
═══════════════════════════════════════════════════════════════
```

**Components to Create:**
- `app/planning/calendar_formatter.py` - Calendar output generation
- `CalendarDay` dataclass for daily structure
- `CalendarItinerary` dataclass for full trip

**Acceptance Criteria:**
- Clean, readable calendar format
- All contextual info included (parking, conditions, travel)
- Travel times calculated from origin
- Practical tips and summary section

---

### Issue #26: End-to-End Trip Planning Integration
**Labels:** integration, agents  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**
Wire together all components for the complete guided trip planning flow.

**Tasks:**
- [ ] Create `TripPlanningOrchestrator` to manage the full flow
- [ ] Implement state machine for planning stages:
  ```
  IDLE → GATHERING → PREVIEWING → CONFIRMED → GENERATING → COMPLETE
  ```
- [ ] Connect ConversationalAgent → ForecastAgent → ContextualAgent → CalendarFormatter
- [ ] Handle edge cases:
  - No good surf windows in date range
  - Unknown destination (suggest alternatives)
  - Very long travel distances (suggest staying overnight)
- [ ] Add conversation recovery (user can restart at any point)
- [ ] Store completed itineraries for reference

**Planning Flow Diagram:**
```
┌─────────────────────────────────────────────────────────────┐
│                    User: "Plan a surf trip"                 │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 1: Gather Information                     │
│  ConversationalAgent asks for:                              │
│  • Skill level → Destination → Origin → Transport → Dates   │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 2: Fetch & Preview Forecast               │
│  ForecastIntegrationAgent:                                  │
│  • Fetches forecast for dates                               │
│  • Finds best windows                                       │
│  • Shows preview to user                                    │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 3: User Confirmation                      │
│  • User confirms dates/spots                                │
│  • Or requests adjustments → back to Stage 1/2              │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 4: Generate Itinerary                     │
│  TripPlanner + ContextualAgent:                             │
│  • Plan optimal sessions                                    │
│  • Get parking, safety info                                 │
│  • Calculate travel times                                   │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 5: Output Calendar                        │
│  CalendarFormatter:                                         │
│  • Generate calendar view                                   │
│  • Include all details                                      │
│  • Display to user                                          │
└─────────────────────────────────────────────────────────────┘
```

**Acceptance Criteria:**
- Complete flow from "plan a trip" to calendar output
- Graceful handling of all edge cases
- User can modify at any stage
- All layers properly integrated

---

## Phase 9: ML Surf Condition Model (Mini Project)

> **Goal:** Replace the rule-based scoring heuristics in `ConditionAssessor` with a
> fine-tuned gradient-boosted tree model (XGBoost / LightGBM) trained on historical
> surf condition data. This is treated as a self-contained data science mini project
> with its own data pipeline, training workflow, and evaluation.
>
> **Thesis relevance:** Demonstrates domain adaptation of ML to surf forecasting,
> provides quantitative comparison against rule-based baseline, and delivers
> interpretable feature importance analysis.

### Issue #27: Historical Surf Data Collection Pipeline
**Labels:** ml, data-engineering, mini-project  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**  
Build a data collection pipeline to gather historical surf conditions paired with
quality ratings for model training. The dataset must map weather/ocean variables
to a surf quality target variable.

**Data Sources to Evaluate:**
| Source | Data Available | Access | Notes |
|--------|---------------|--------|-------|
| NOAA Hindcast (WaveWatch III) | Wave height, period, direction | Free / bulk download | Global, hourly, multi-decade |
| Open-Meteo Historical API | Wind, swell, weather | Free API | Up to 1940, hourly |
| Surfline historical reports | Condition ratings (1-5 stars) | Web scraping / manual | Human-labeled quality target |
| CDIP (Scripps) buoy data | Real-time & historical buoy | Free API | US West Coast focused |
| Copernicus ERA5 | Reanalysis ocean/atmo data | Free (registration) | Research-grade, global |

**Tasks:**
- [ ] Evaluate data sources for coverage, quality, and accessibility
- [ ] Select primary source(s) for features and target variable
- [ ] Build data download scripts in `ml/data/collect.py`
- [ ] Create raw data storage format (Parquet or CSV)
- [ ] Collect minimum **2 years** of hourly data for **5+ spots**
- [ ] Document data provenance, licensing, and limitations
- [ ] Store raw data in `ml/data/raw/` (gitignored)

**Target Dataset Schema (per row = 1 hour at 1 spot):**
```
spot_id, timestamp, lat, lon,
wave_height_m, wave_period_s, wave_direction_deg,
swell_height_m, swell_period_s, swell_direction_deg,
wind_speed_kph, wind_gust_kph, wind_direction_deg,
tide_height_m,
water_temp_c, air_temp_c, cloud_cover_pct,
surf_quality_score  ← target (0-100 or categorical)
```

**Acceptance Criteria:**
- Reproducible download scripts with clear instructions
- Minimum 50,000 data points across multiple spots and seasons
- Raw data documented with schema and provenance notes
- Data stored in efficient format (Parquet preferred)

---

### Issue #28: Feature Engineering & Dataset Preparation
**Labels:** ml, feature-engineering, mini-project  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**  
Transform raw historical data into a clean, feature-engineered dataset ready for
model training. Features must align with the existing `ForecastPoint` schema so
the trained model can score live forecasts at inference time.

**Tasks:**
- [ ] Create `ml/features/engineer.py` for feature transformations
- [ ] Implement feature extraction pipeline:
  - **Wave features:** height, height range, avg height
  - **Swell features:** height, period, direction (sin/cos encoded)
  - **Wind features:** speed, gust, direction (sin/cos encoded), is_offshore flag
  - **Tide features:** height, state (encoded)
  - **Temporal features:** hour of day (sin/cos), month (sin/cos), day of week
  - **Derived features:**
    - Wave energy proxy: `swell_height² × swell_period`
    - Wind-wave interaction: `wind_speed × cos(wind_dir - swell_dir)`
    - Swell-to-wind ratio: `swell_period / wind_speed`
    - Tide trend (rising/falling from consecutive readings)
- [ ] Create `ForecastPointFeatureExtractor` class that converts a `ForecastPoint` → feature vector
  - This is the **shared component** used in both training and inference
- [ ] Handle missing values (imputation strategy)
- [ ] Create train/validation/test split (70/15/15)
  - Split by **time** (not random) to prevent data leakage
  - Test set = most recent 3 months
- [ ] Save processed dataset to `ml/data/processed/`
- [ ] Generate exploratory data analysis (EDA) notebook: `ml/notebooks/01_eda.ipynb`

**Feature Vector (expected ~25-30 features):**
```python
[
    wave_height_min, wave_height_max, wave_height_avg,
    swell_height, swell_period, swell_dir_sin, swell_dir_cos,
    wind_speed, wind_gust, wind_dir_sin, wind_dir_cos,
    is_offshore, is_light_wind,
    tide_height, tide_is_rising,
    wave_energy_proxy, wind_wave_interaction, swell_wind_ratio,
    hour_sin, hour_cos, month_sin, month_cos,
    water_temp, air_temp,
    skill_level_encoded  # 0=beginner, 1=intermediate, 2=advanced, 3=expert
]
```

**Critical Constraint:**  
The `ForecastPointFeatureExtractor` must produce the **exact same feature vector**
from a live `ForecastPoint` object as from a historical data row. This is the
train/serve consistency contract.

**Acceptance Criteria:**
- Clean dataset with no data leakage in splits
- Feature extractor works on both historical rows and live `ForecastPoint` objects
- EDA notebook with distribution plots, correlation matrix, missing value analysis
- Documented feature definitions and engineering rationale

---

### Issue #29: Model Training & Evaluation
**Labels:** ml, model-training, mini-project  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**  
Train a gradient-boosted tree model (XGBoost as primary, LightGBM as comparison)
to predict surf condition quality scores. Evaluate against the rule-based
`ConditionAssessor` baseline.

**Tasks:**
- [ ] Create training script: `ml/train.py`
- [ ] Create training notebook: `ml/notebooks/02_training.ipynb`
- [ ] Implement model training pipeline:
  - XGBoost regressor (primary) predicting score 0-100
  - LightGBM regressor (comparison)
  - Hyperparameter tuning via cross-validation (5-fold, time-series aware)
- [ ] Define evaluation metrics:
  - **Regression:** MAE, RMSE, R² on test set
  - **Classification (binned):** Map scores to `ConditionRating` categories,
    measure accuracy, precision, recall, F1 per class
  - **Ranking:** Spearman correlation (does model rank hours correctly?)
- [ ] Establish rule-based baseline:
  - Run current `ConditionAssessor.assess()` on the test set
  - Record scores and ratings as baseline metrics
- [ ] Generate evaluation report:
  - Model vs. baseline metric comparison table
  - Confusion matrix (predicted vs actual `ConditionRating`)
  - Feature importance plot (top 15 features)
  - SHAP analysis for interpretability
  - Residual analysis by spot, season, and skill level
- [ ] Serialize best model: `ml/models/surf_condition_model.joblib`
- [ ] Save training metadata (hyperparams, metrics, timestamp): `ml/models/model_metadata.json`

**Hyperparameter Search Space (XGBoost):**
```python
param_grid = {
    "n_estimators": [100, 300, 500],
    "max_depth": [4, 6, 8],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
    "min_child_weight": [1, 3, 5],
}
```

**Expected Model Characteristics:**
- Serialized size: < 500 KB
- Inference time: < 5 ms per prediction
- Target: R² ≥ 0.75 on test set, classification accuracy ≥ 80%

**Acceptance Criteria:**
- Model outperforms rule-based baseline on at least 2 of 3 metric categories
- Feature importance analysis completed and documented
- SHAP plots generated for interpretability (thesis figures)
- Model serialized and loadable without training dependencies
- Reproducible training with fixed random seeds

---

### Issue #30: Model Integration into ConditionAssessor
**Labels:** ml, integration, mini-project  
**Priority:** High  
**Status:** 🔲 Pending

**Description:**  
Integrate the trained ML model into the SurfSense runtime by creating a
`SurfConditionModel` class and wiring it into the existing `ConditionAssessor`.

**Tasks:**
- [ ] Create `app/ml/__init__.py` module
- [ ] Create `app/ml/surf_model.py` with `SurfConditionModel` class:
  ```python
  class SurfConditionModel:
      def __init__(self, model_path: str = "ml/models/surf_condition_model.joblib")
      def predict(self, forecast: ForecastPoint, skill_level: str) -> float  # score 0-100
      def predict_rating(self, forecast: ForecastPoint, skill_level: str) -> ConditionRating
      def predict_batch(self, forecasts: list[ForecastPoint], skill_level: str) -> list[float]
      def get_feature_contributions(self, forecast: ForecastPoint, skill_level: str) -> dict
  ```
- [ ] Move `ForecastPointFeatureExtractor` from `ml/features/` into `app/ml/feature_extractor.py`
  - This is the shared component used at both training and inference time
- [ ] Update `ConditionAssessor.assess()` to use `SurfConditionModel.predict()`:
  - Replace the manual `score += wave_score + swell_score + wind_score` logic
  - ML model provides the score; assessor still maps score → rating + builds explanation
- [ ] Update `ConditionAssessor.__init__()` to load the model on startup
- [ ] Add `ML_MODEL_PATH` to `config/settings.py`
- [ ] Add `xgboost` and `joblib` to `requirements.txt`
- [ ] Ship the serialized model file in `ml/models/` (committed to repo)
- [ ] Add model version logging on startup

**Integration Point in `ConditionAssessor.assess()`:**
```python
# BEFORE (rule-based):
score = 50.0
score += wave_score    # from _assess_waves()
score += swell_score   # from _assess_swell_period()
score += wind_score    # from _assess_wind()

# AFTER (ML model):
score = self._model.predict(forecast, skill_level)  # 0-100
```

**Key Design Decisions:**
- The ML model **replaces** the score calculation only
- Rating derivation (`_calculate_rating`), summary building, and safety warnings
  remain rule-based (these are interpretability/safety features, not predictions)
- `get_feature_contributions()` uses SHAP values to explain individual predictions
  to the user ("wind was the main negative factor")

**File Structure After Integration:**
```
app/
  ml/
    __init__.py
    surf_model.py            # SurfConditionModel class
    feature_extractor.py     # ForecastPointFeatureExtractor
ml/
    data/
        raw/                 # Raw downloaded data (gitignored)
        processed/           # Cleaned datasets (gitignored)
    features/
        engineer.py          # Training-time feature pipeline
    models/
        surf_condition_model.joblib   # Serialized model (committed)
        model_metadata.json           # Training metadata (committed)
    notebooks/
        01_eda.ipynb
        02_training.ipynb
    train.py                 # Training entry point
    requirements.txt         # ML-specific dependencies (sklearn, xgboost, shap)
```

**Acceptance Criteria:**
- Model loads on startup and logs version info
- `ConditionAssessor.assess()` returns ML-based scores
- No change to the public API of `ConditionAssessor` (downstream code unaffected)
- Inference adds < 10 ms to forecast processing
- Feature contributions available for explainability

---

### Issue #31: ML Model Evaluation Report & Thesis Figures
**Labels:** ml, evaluation, thesis, mini-project  
**Priority:** Medium  
**Status:** 🔲 Pending

**Description:**  
Generate the final evaluation comparing the ML model against the rule-based
baseline. Produce publication-ready figures and tables for the thesis.

**Tasks:**
- [ ] Create evaluation notebook: `ml/notebooks/03_evaluation.ipynb`
- [ ] Run both systems on the held-out test set:
  - Rule-based `ConditionAssessor` (original heuristic scoring)
  - ML `SurfConditionModel` (XGBoost)
- [ ] Generate comparison metrics:
  | Metric | Rule-Based | ML Model |
  |--------|-----------|----------|
  | MAE | — | — |
  | RMSE | — | — |
  | R² | — | — |
  | Rating Accuracy | — | — |
  | Rating F1 (macro) | — | — |
  | Spearman ρ | — | — |
- [ ] Generate thesis-ready figures:
  - Feature importance bar chart (top 15)
  - SHAP summary plot (beeswarm)
  - SHAP dependence plots for top 3 features
  - Confusion matrix heatmap (predicted vs actual ConditionRating)
  - Score distribution: ML vs rule-based vs actual (histogram overlay)
  - Scatter plot: predicted vs actual score with R² annotation
  - Per-spot accuracy breakdown (bar chart)
  - Per-season accuracy breakdown
- [ ] Write evaluation summary (markdown) for thesis appendix
- [ ] Document model limitations and failure modes
- [ ] Export all figures as high-res PNG/PDF in `ml/figures/`

**Acceptance Criteria:**
- All figures are publication-quality (300 DPI, proper labels, legends)
- Clear narrative comparing ML vs rule-based approach
- Honest discussion of limitations and edge cases
- Reproducible from notebook with fixed seeds

---

## Phase 8: Testing & Documentation

### Issue #20: Write Unit Tests
**Labels:** testing, quality  
**Priority:** Medium  
**Status:** 🔲 Pending

**Description:**
Create unit tests for core components.

**Tasks:**
- [ ] Set up pytest in `tests/` directory
- [ ] Test agent base classes
- [ ] Test contextual providers
- [ ] Test forecast models
- [ ] Test condition assessment
- [ ] Test window finder
- [ ] Test trip planner
- [ ] Test guided information gathering (Issue #22)
- [ ] Test calendar formatter (Issue #25)
- [ ] Test ML feature extractor (Issue #28)
- [ ] Test SurfConditionModel loading and prediction (Issue #30)
- [ ] Test ML-integrated ConditionAssessor (Issue #30)

**Acceptance Criteria:**
- Core components have tests
- Tests pass consistently
- ML model tests work with a small fixture model

---

### Issue #21: Write Documentation
**Labels:** documentation  
**Priority:** Low  
**Status:** 🔲 Pending

**Description:**
Create comprehensive documentation.

**Tasks:**
- [ ] Document 3-layer architecture
- [ ] Add example conversations
- [ ] Document slash commands
- [ ] Explain how to add new providers
- [ ] API documentation for agents
- [ ] Document guided trip planning flow
- [ ] Add calendar output examples
- [ ] Document ML model architecture and training process
- [ ] Document how to retrain the model with new data

**Acceptance Criteria:**
- Architecture clearly explained
- Users can extend the system
- ML pipeline is reproducible from documentation

---

## Summary

**Total Issues: 31**

**Status:**
- ✅ Completed: 19 issues (Phase 1-6)
- ⏭️ Skipped: 1 issue
- 🔲 Pending: 11 issues (Phase 7-9)

**Completed by Phase:**

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation | ✅ Complete |
| 2 | LLM Core | ✅ Complete |
| 3 | Agent Architecture | ✅ Complete |
| 4 | Forecast API Integration | ✅ Complete |
| 5 | Knowledge Integration | ✅ Complete |
| 6 | Planning Engine | ✅ Complete |
| 7 | Guided Trip Planning Flow | 🔲 Pending |
| 8 | Testing & Documentation | 🔲 Pending |
| 9 | **ML Surf Condition Model (Mini Project)** | 🆕 Pending |

**Phase 7 Issues (Guided Trip Planning):**

| Issue | Title | Priority |
|-------|-------|----------|
| #22 | Implement Guided Information Gathering | High |
| #23 | Add Origin & Transportation Support | High |
| #24 | Implement Forecast Preview & Confirmation Flow | High |
| #25 | Calendar-Format Itinerary Generator | High |
| #26 | End-to-End Trip Planning Integration | High |

**Phase 9 Issues (ML Mini Project):**

| Issue | Title | Priority | Dependency |
|-------|-------|----------|------------|
| #27 | Historical Surf Data Collection Pipeline | High | — |
| #28 | Feature Engineering & Dataset Preparation | High | #27 |
| #29 | Model Training & Evaluation (XGBoost) | High | #28 |
| #30 | Model Integration into ConditionAssessor | High | #29 |
| #31 | ML Model Evaluation Report & Thesis Figures | Medium | #29, #30 |

**Architecture Implemented:**

```
Layer 1: ConversationalAgent (dialogue, personalization)
    ↓
Layer 2: Contextual Layer (parking, accessibility, reviews, safety)
    ↓
Layer 3: ForecastIntegrationAgent (forecast APIs, analysis)
    ↓
ML Model: XGBoost SurfConditionModel (score prediction 0-100)
    ↓
ConditionAssessor (rating, explanations, safety warnings)
```

**ML Model Data Flow:**

```
Forecast APIs → ForecastPoint → FeatureExtractor → XGBoost → score 0-100
                                                                  ↓
                                               ConditionAssessor.assess()
                                                                  ↓
                                              SurfWindow / TripPlanner
```

**Planning Flow:**

```
User Input → Guided Questions → Forecast Preview → 
User Confirms → Generate Itinerary → Calendar Output
```

**Key Files:**
- `app/agents/base.py` - BaseAgent, AgentState, AgentMessage
- `app/agents/conversational.py` - Layer 1 agent
- `app/agents/forecast_integration.py` - Layer 3 agent
- `app/contextual/*.py` - Layer 2 providers
- `app/forecasting/models.py` - Forecast data models
- `app/__main__.py` - Terminal interface with commands
- `app/agents/trip_planning_state.py` - 🆕 Planning state tracking
- `app/planning/calendar_formatter.py` - 🆕 Calendar output
- `app/ml/surf_model.py` - 🆕 ML model inference wrapper
- `app/ml/feature_extractor.py` - 🆕 ForecastPoint → feature vector
- `ml/train.py` - 🆕 Model training entry point
- `ml/notebooks/` - 🆕 EDA, training, evaluation notebooks
- `ml/models/surf_condition_model.joblib` - 🆕 Serialized model
