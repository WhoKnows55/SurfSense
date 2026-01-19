# SurfSense - GitHub Issues

## Project Overview

SurfSense is a **terminal-based conversational AI** for surf trip planning, powered by a **free local LLM** (Phi-3 mini). No API keys required for basic usage!

### Architecture

The system follows a **3-layer agent architecture**:

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
                                  └─────────────────┘
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

## Phase 6: Planning Engine

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

## Phase 7: Testing & Documentation

### Issue #20: Write Unit Tests
**Labels:** testing, quality  
**Priority:** Medium  

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

**Acceptance Criteria:**
- Core components have tests
- Tests pass consistently

---

### Issue #21: Write Documentation
**Labels:** documentation  
**Priority:** Low  

**Description:**
Create comprehensive documentation.

**Tasks:**
- [ ] Document 3-layer architecture
- [ ] Add example conversations
- [ ] Document slash commands
- [ ] Explain how to add new providers
- [ ] API documentation for agents

**Acceptance Criteria:**
- Architecture clearly explained
- Users can extend the system

---

## Summary

**Total Issues: 21**

**Status:**
- ✅ Completed: 12 issues (Phase 1-3)
- ⏭️ Skipped: 1 issue
- 📋 Remaining: 8 issues

**Completed by Phase:**

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation | ✅ Complete |
| 2 | LLM Core | ✅ Complete |
| 3 | Agent Architecture | ✅ Complete |
| 4 | Forecast API Integration | 🔲 Pending |
| 5 | Knowledge Integration | 🔲 Pending |
| 6 | Planning Engine | 🔲 Pending |
| 7 | Testing & Documentation | 🔲 Pending |

**Architecture Implemented:**

```
Layer 1: ConversationalAgent (dialogue, personalization)
    ↓
Layer 2: Contextual Layer (parking, accessibility, reviews, safety)
    ↓
Layer 3: ForecastIntegrationAgent (forecast APIs, analysis)
```

**Key Files:**
- `app/agents/base.py` - BaseAgent, AgentState, AgentMessage
- `app/agents/conversational.py` - Layer 1 agent
- `app/agents/forecast_integration.py` - Layer 3 agent
- `app/contextual/*.py` - Layer 2 providers
- `app/forecasting/models.py` - Forecast data models
- `app/__main__.py` - Terminal interface with commands
