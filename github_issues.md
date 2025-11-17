# SurfSense Web App - GitHub Issues

## Project Setup

### Issue #1: Initialize Python Web Application Project
**Labels:** setup, infrastructure  
**Priority:** High  

**Description:**
Set up the foundational Python web application structure for SurfSense desktop web app.

**Tasks:**
- [ ] Create project directory structure following clean architecture principles
- [ ] Initialize Python virtual environment (Python 3.10+)
- [ ] Create `requirements.txt` with core dependencies:
  - Flask or FastAPI (for web framework)
  - LangChain (for LLM orchestration)
  - python-dotenv (for configuration)
  - pytest (for testing)
- [ ] Set up `.env.example` for API key templates
- [ ] Create `.gitignore` for Python projects
- [ ] Add `README.md` with setup instructions
- [ ] Create basic project structure:
  ```
  surfsense/
  ├── app/
  │   ├── __init__.py
  │   ├── core/
  │   ├── forecasting/
  │   ├── knowledge/
  │   ├── planning/
  │   ├── state/
  │   └── interfaces/
  ├── tests/
  ├── config/
  ├── requirements.txt
  └── README.md
  ```

**Acceptance Criteria:**
- Project runs with `python -m app`
- All dependencies install without errors
- Clean, documented folder structure

---

### Issue #2: Configure Development Environment and Code Quality Tools
**Labels:** setup, code-quality  
**Priority:** High  

**Description:**
Set up tools to enforce clean code principles: simplicity, consistency, and clarity.

**Tasks:**
- [ ] Add `black` for consistent code formatting
- [ ] Add `flake8` for linting
- [ ] Add `mypy` for type checking
- [ ] Add `isort` for import sorting
- [ ] Create `pyproject.toml` with tool configurations
- [ ] Add pre-commit hooks configuration
- [ ] Create `Makefile` with common commands:
  - `make format` - Run black and isort
  - `make lint` - Run flake8 and mypy
  - `make test` - Run pytest
  - `make run` - Start application

**Acceptance Criteria:**
- All code quality tools run successfully
- Clear documentation on how to use them
- Consistent code style enforced

---

## Core Infrastructure

### Issue #3: Implement Configuration Management System
**Labels:** infrastructure, core  
**Priority:** High  

**Description:**
Create a simple, centralized configuration system for API keys, model settings, and application parameters.

**Tasks:**
- [ ] Create `config/settings.py` with Pydantic models for type-safe configuration
- [ ] Support environment variables via `.env` file
- [ ] Define configuration sections:
  - LLM settings (model name, temperature, max tokens)
  - API endpoints (forecast providers)
  - Skill level thresholds
  - Logging configuration
- [ ] Implement configuration validation on startup
- [ ] Add clear error messages for missing required settings
- [ ] Document all configuration options in README

**Acceptance Criteria:**
- Configuration loads from environment variables
- Invalid configuration raises clear errors
- All settings are type-safe and validated

---

### Issue #4: Set Up Logging System
**Labels:** infrastructure, observability  
**Priority:** Medium  

**Description:**
Implement consistent logging across all components for debugging and monitoring.

**Tasks:**
- [ ] Create `app/core/logger.py` with structured logging setup
- [ ] Use Python's `logging` module with clear formatters
- [ ] Configure log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Add request/response logging for API calls
- [ ] Include timestamps, module names, and log levels
- [ ] Support file and console output
- [ ] Keep log messages clear and actionable

**Acceptance Criteria:**
- Logs are readable and consistently formatted
- Easy to filter by component or severity
- No sensitive data (API keys) in logs

---

## LLM and Orchestration Layer

### Issue #5: Implement LLM Core Service
**Labels:** llm, core  
**Priority:** High  

**Description:**
Build the conversational agent core using LangChain for natural language understanding and tool orchestration.

**Tasks:**
- [ ] Create `app/core/llm_service.py` with clean interface
- [ ] Integrate OpenAI or Anthropic LLM via LangChain
- [ ] Define system prompt for SurfSense persona and capabilities
- [ ] Implement intent extraction (location, dates, skill level, preferences)
- [ ] Create simple, readable prompt templates
- [ ] Add error handling for API failures
- [ ] Implement retry logic with exponential backoff
- [ ] Keep token usage tracking for monitoring

**Acceptance Criteria:**
- LLM responds to basic surf trip queries
- Extracts key parameters correctly
- Handles API errors gracefully
- Code is clear and well-documented

---

### Issue #6: Create Tool Registry for LLM Agent
**Labels:** llm, architecture  
**Priority:** High  

**Description:**
Implement a clean tool registry that the LLM can use to access forecasts, spot data, and planning functions.

**Tasks:**
- [ ] Create `app/core/tools.py` with tool definitions
- [ ] Define tools for:
  - `get_surf_forecast(location, date_range)`
  - `get_spot_info(spot_name)`
  - `compare_spots(spots, date_range)`
  - `create_trip_plan(parameters)`
  - `update_trip_plan(modifications)`
- [ ] Use clear, descriptive tool names and parameters
- [ ] Add detailed docstrings for each tool (LLM uses these)
- [ ] Implement input validation for tool parameters
- [ ] Return structured responses from tools

**Acceptance Criteria:**
- All tools have clear, single responsibilities
- Tool signatures are simple and intuitive
- LLM can successfully invoke tools
- Tool responses are consistently structured

---

## Forecasting Layer

### Issue #7: Design Unified Forecast Data Schema
**Labels:** forecasting, data-model  
**Priority:** High  

**Description:**
Create a consistent internal data model for surf forecasts that works with multiple data sources.

**Tasks:**
- [ ] Create `app/forecasting/models.py` with Pydantic models
- [ ] Define `ForecastPoint` model with fields:
  - timestamp
  - wave_height_min, wave_height_max (meters)
  - swell_period (seconds)
  - swell_direction (degrees)
  - wind_speed, wind_direction
  - tide_height (meters)
  - weather_description
- [ ] Define `ForecastResponse` containing list of forecast points
- [ ] Add validation rules (e.g., wave height > 0)
- [ ] Include spot metadata (name, coordinates)
- [ ] Keep schema simple and extensible

**Acceptance Criteria:**
- Schema validates all required fields
- Clear field names and types
- Works with multiple forecast sources
- Well-documented with examples

---

### Issue #8: Implement External Forecast API Client
**Labels:** forecasting, api-integration  
**Priority:** High  

**Description:**
Build a clean API client for fetching real-time surf forecasts from external providers.

**Tasks:**
- [ ] Create `app/forecasting/api_client.py`
- [ ] Implement client for Surfline, Stormglass, or similar API
- [ ] Transform API responses to unified schema
- [ ] Add request timeout handling (5-10 seconds)
- [ ] Implement caching with TTL (e.g., 1 hour for forecasts)
- [ ] Log API calls and response times
- [ ] Handle rate limiting gracefully
- [ ] Add clear error messages for API failures
- [ ] Keep transformation logic simple and testable

**Acceptance Criteria:**
- Successfully fetches forecast data
- Transforms to internal schema correctly
- Handles network errors without crashing
- Caches responses to reduce API calls
- Code is readable with clear function names

---

### Issue #9: Build Local Forecast Fallback Model
**Labels:** forecasting, ml-model  
**Priority:** Medium  

**Description:**
Implement a lightweight time-series forecasting model (Prophet or ARIMA) as fallback when API is unavailable.

**Tasks:**
- [ ] Create `app/forecasting/local_model.py`
- [ ] Use Prophet or statsmodels ARIMA for wave height prediction
- [ ] Train on historical data (if available) or use simple persistence model
- [ ] Keep model simple - focus on basic wave height trends
- [ ] Return forecasts in same unified schema
- [ ] Add clear disclaimer that these are estimates
- [ ] Document model limitations in code comments
- [ ] Optimize for lightweight execution

**Acceptance Criteria:**
- Model generates basic forecasts offline
- Uses same schema as API client
- Fast execution (< 2 seconds for 7-day forecast)
- Clear, honest about accuracy limitations
- Simple, maintainable code

---

### Issue #10: Create Forecast Service Orchestrator
**Labels:** forecasting, service  
**Priority:** High  

**Description:**
Build service layer that tries API first, then falls back to local model, with clear error handling.

**Tasks:**
- [ ] Create `app/forecasting/forecast_service.py`
- [ ] Implement `get_forecast(location, start_date, end_date)` method
- [ ] Try API client first
- [ ] On API failure, switch to local model
- [ ] Log which source was used
- [ ] Include data source in response metadata
- [ ] Keep logic simple with clear control flow
- [ ] Add health check method for monitoring

**Acceptance Criteria:**
- Seamlessly switches between API and local model
- User is informed of data source
- No complex exception handling - keep it simple
- Well-tested fallback behavior

---

## Contextual Knowledge Layer

### Issue #11: Create Surf Spot Knowledge Base
**Labels:** knowledge, data  
**Priority:** Medium  

**Description:**
Build a simple storage and retrieval system for surf spot metadata and contextual information.

**Tasks:**
- [ ] Create `app/knowledge/spot_data.py`
- [ ] Define `SpotInfo` model with fields:
  - name, location (coordinates)
  - skill_levels (beginner, intermediate, advanced)
  - break_type (beach, reef, point)
  - access_notes
  - parking_info
  - safety_warnings
  - best_tide, best_wind_direction
  - seasonal_notes
- [ ] Start with JSON file storage (`data/spots.json`)
- [ ] Implement `get_spot_info(spot_name)` function
- [ ] Implement `search_spots_by_location(lat, lon, radius)` function
- [ ] Keep data structure flat and readable
- [ ] Document data schema clearly

**Acceptance Criteria:**
- Can retrieve spot information by name
- JSON file is human-readable
- Simple search functionality works
- Easy to add new spots
- Clear data validation

---

### Issue #12: Implement Spot Search and Filtering
**Labels:** knowledge, search  
**Priority:** Medium  

**Description:**
Add simple search capabilities for finding surf spots based on various criteria.

**Tasks:**
- [ ] Create `app/knowledge/spot_search.py`
- [ ] Implement search by:
  - Location (nearest spots to coordinates)
  - Skill level
  - Break type
- [ ] Use simple distance calculations (haversine formula)
- [ ] Return ranked results
- [ ] Keep search logic straightforward
- [ ] Add clear function signatures and docstrings

**Acceptance Criteria:**
- Search returns relevant spots
- Results are sorted logically
- Fast execution for moderate datasets
- Code is easy to understand and modify

---

## Planning Engine

### Issue #13: Define Skill Level Suitability Rules
**Labels:** planning, business-logic  
**Priority:** High  

**Description:**
Implement clear, simple rules for determining if surf conditions match a user's skill level.

**Tasks:**
- [ ] Create `app/planning/suitability.py`
- [ ] Define thresholds in configuration:
  ```python
  SKILL_THRESHOLDS = {
      "beginner": {"max_wave_height": 1.5, "max_wind_speed": 15},
      "intermediate": {"max_wave_height": 2.5, "max_wind_speed": 20},
      "advanced": {"max_wave_height": 5.0, "max_wind_speed": 30}
  }
  ```
- [ ] Implement `assess_conditions(forecast, skill_level)` function
- [ ] Return simple rating: "ideal", "suitable", "challenging", "unsafe"
- [ ] Include clear reasoning for the assessment
- [ ] Add safety warnings for dangerous conditions
- [ ] Keep logic transparent and easy to adjust

**Acceptance Criteria:**
- Rules are clearly documented
- Assessments match expected outcomes
- Easy to modify thresholds
- Returns human-readable explanations

---

### Issue #14: Build Multi-Day Trip Planner
**Labels:** planning, core  
**Priority:** High  

**Description:**
Create planning logic that analyzes multi-day forecasts and identifies optimal surf windows.

**Tasks:**
- [ ] Create `app/planning/trip_planner.py`
- [ ] Implement `create_trip_plan(location, dates, skill_level, preferences)`
- [ ] For each day:
  - Get forecast
  - Assess suitability
  - Identify best surf windows (based on tide, wind)
- [ ] Rank days by overall conditions
- [ ] Suggest alternative spots if conditions are poor
- [ ] Keep algorithm simple and explainable
- [ ] Return structured plan with daily breakdown

**Acceptance Criteria:**
- Generates coherent multi-day plans
- Identifies best surf times each day
- Provides clear reasoning
- Code is readable with clear logic flow

---

### Issue #15: Implement Spot Comparison Logic
**Labels:** planning, comparison  
**Priority:** Medium  

**Description:**
Build functionality to compare multiple surf spots for the same time period.

**Tasks:**
- [ ] Create `app/planning/spot_comparison.py`
- [ ] Implement `compare_spots(spot_names, date_range, skill_level)`
- [ ] For each spot:
  - Get forecast
  - Calculate suitability score
  - Retrieve contextual info
- [ ] Rank spots by combined score
- [ ] Present clear comparison table
- [ ] Include pros/cons for each spot
- [ ] Keep scoring algorithm simple and transparent

**Acceptance Criteria:**
- Comparison results are intuitive
- Ranking makes sense to users
- Easy to understand why one spot is preferred
- Clear, structured output

---

### Issue #16: Add Dynamic Plan Update Capability
**Labels:** planning, updates  
**Priority:** Medium  

**Description:**
Enable updating existing trip plans when forecasts change or user modifies parameters.

**Tasks:**
- [ ] Create `app/planning/plan_updates.py`
- [ ] Implement `update_plan(existing_plan, new_forecast)` function
- [ ] Detect significant forecast changes
- [ ] Recalculate suitability for affected days
- [ ] Suggest plan modifications when needed
- [ ] Keep update logic simple and predictable
- [ ] Return clear change summary

**Acceptance Criteria:**
- Detects meaningful forecast changes
- Updates plans appropriately
- Communicates changes clearly
- Preserves user preferences when possible

---

## State and Memory Layer

### Issue #17: Implement Session State Manager
**Labels:** state, memory  
**Priority:** High  

**Description:**
Create a simple in-memory state manager for maintaining conversation context within a session.

**Tasks:**
- [ ] Create `app/state/session_manager.py`
- [ ] Define `SessionState` model with:
  - session_id
  - user_profile (skill_level, preferences)
  - trip_parameters (location, dates)
  - current_plan
  - conversation_history (last 10 messages)
- [ ] Implement `get_session(session_id)` and `update_session(session_id, data)`
- [ ] Use simple in-memory dictionary for storage (for MVP)
- [ ] Add session timeout logic (30 minutes)
- [ ] Keep state structure flat and simple
- [ ] Add clear methods for updating specific fields

**Acceptance Criteria:**
- State persists across conversation turns
- Memory usage is bounded
- Simple, clear API for state access
- Session cleanup works correctly

---

### Issue #18: Build Context Extraction Service
**Labels:** state, nlp  
**Priority:** Medium  

**Description:**
Extract and update trip parameters from user messages without requiring repeated input.

**Tasks:**
- [ ] Create `app/state/context_extractor.py`
- [ ] Implement `extract_parameters(message, current_state)` function
- [ ] Parse entities: locations, dates, skill levels, preferences
- [ ] Use LLM for extraction (via structured output)
- [ ] Merge new parameters with existing state
- [ ] Handle conflicts (e.g., changed dates) explicitly
- [ ] Keep extraction logic simple and explicit
- [ ] Return updated state with change summary

**Acceptance Criteria:**
- Extracts parameters accurately
- Handles partial updates correctly
- Clear handling of conflicting information
- Doesn't lose previously extracted data

---

## Web Interface Layer

### Issue #19: Create REST API Endpoints
**Labels:** api, interface  
**Priority:** High  

**Description:**
Build clean REST API for the web frontend using Flask or FastAPI.

**Tasks:**
- [ ] Create `app/interfaces/api.py`
- [ ] Implement endpoints:
  - `POST /api/chat` - Send message, get response
  - `GET /api/session/{session_id}` - Get session state
  - `POST /api/session` - Create new session
  - `GET /api/forecast/{location}` - Get current forecast
  - `GET /api/spots` - List available spots
- [ ] Use clear request/response models (Pydantic)
- [ ] Add input validation on all endpoints
- [ ] Include error handling with meaningful messages
- [ ] Keep endpoint logic thin - delegate to services
- [ ] Add CORS support for local development

**Acceptance Criteria:**
- All endpoints work correctly
- Clear API documentation (OpenAPI/Swagger)
- Proper error responses
- Simple, RESTful design

---

### Issue #20: Build Simple Chat Web Interface
**Labels:** frontend, ui  
**Priority:** High  

**Description:**
Create a minimal, clean desktop web UI for conversational interaction.

**Tasks:**
- [ ] Create `app/static/` and `app/templates/` directories
- [ ] Build simple HTML chat interface:
  - Message input box
  - Chat history display
  - Typing indicator
  - Clean, readable typography
- [ ] Add minimal CSS for desktop layout (no mobile yet)
- [ ] Implement JavaScript for:
  - Sending messages via API
  - Receiving and displaying responses
  - Managing session state
- [ ] Keep UI simple and functional (no fancy animations)
- [ ] Use vanilla JavaScript or minimal framework
- [ ] Focus on clarity and usability

**Acceptance Criteria:**
- Chat interface works on desktop browsers
- Messages send and display correctly
- Clean, professional appearance
- No complex dependencies

---

### Issue #21: Add Response Formatting Service
**Labels:** interface, formatting  
**Priority:** Medium  

**Description:**
Format LLM responses into structured, readable output for the web interface.

**Tasks:**
- [ ] Create `app/interfaces/response_formatter.py`
- [ ] Parse LLM output into sections:
  - Conditions summary
  - Surf windows
  - Safety notes
  - Recommendations
  - Alternative options
- [ ] Convert to structured JSON for frontend
- [ ] Support markdown formatting in responses
- [ ] Keep formatting logic simple
- [ ] Add clear visual hierarchy

**Acceptance Criteria:**
- Responses are well-structured
- Easy to scan and read
- Consistent formatting across response types
- Simple, maintainable code

---

## Testing and Quality

### Issue #22: Write Unit Tests for Core Services
**Labels:** testing, quality  
**Priority:** High  

**Description:**
Create comprehensive unit tests for all service layer components.

**Tasks:**
- [ ] Set up pytest structure in `tests/` directory
- [ ] Write tests for:
  - LLM service (with mocked API)
  - Forecast service (API and local model)
  - Planning engine
  - Suitability rules
  - State manager
- [ ] Use clear test names describing behavior
- [ ] Mock external dependencies (APIs, LLM)
- [ ] Aim for >80% code coverage
- [ ] Keep tests simple and focused
- [ ] Use fixtures for common test data

**Acceptance Criteria:**
- All core services have tests
- Tests pass consistently
- Clear test failure messages
- Fast test execution (< 30 seconds total)

---

### Issue #23: Create Integration Tests
**Labels:** testing, integration  
**Priority:** Medium  

**Description:**
Build integration tests for end-to-end workflows.

**Tasks:**
- [ ] Create `tests/integration/` directory
- [ ] Test complete user flows:
  - Create trip plan from conversation
  - Update plan with new parameters
  - Compare multiple spots
  - Handle forecast updates
- [ ] Use test fixtures for forecast data
- [ ] Test API endpoints with test client
- [ ] Keep tests readable and well-documented
- [ ] Verify state persistence across requests

**Acceptance Criteria:**
- Key user workflows are tested
- Tests catch integration issues
- Clear documentation of test scenarios
- Tests are maintainable

---

### Issue #24: Add API Health Monitoring
**Labels:** monitoring, reliability  
**Priority:** Low  

**Description:**
Implement simple health checks for external dependencies.

**Tasks:**
- [ ] Create `app/core/health.py`
- [ ] Implement health check for forecast API
- [ ] Track API response times and error rates
- [ ] Create `/api/health` endpoint returning system status
- [ ] Log health check results
- [ ] Keep monitoring simple and lightweight
- [ ] Add basic metrics (uptime, error count)

**Acceptance Criteria:**
- Health endpoint returns accurate status
- API issues are detected and logged
- Simple dashboard or JSON response
- Minimal performance overhead

---

## Documentation

### Issue #25: Write Developer Documentation
**Labels:** documentation  
**Priority:** Medium  

**Description:**
Create clear documentation for developers working on the project.

**Tasks:**
- [ ] Document architecture in `docs/architecture.md`
- [ ] Create API reference in `docs/api.md`
- [ ] Write setup guide in main README
- [ ] Document configuration options
- [ ] Add code examples for common tasks
- [ ] Document deployment process
- [ ] Keep docs concise and accurate
- [ ] Include diagrams for key workflows

**Acceptance Criteria:**
- New developers can set up and run the app
- All major components are documented
- Examples are working and tested
- Documentation is version controlled

---

### Issue #26: Create User Guide
**Labels:** documentation, user-facing  
**Priority:** Low  

**Description:**
Write simple guide explaining how to use SurfSense.

**Tasks:**
- [ ] Create `docs/user_guide.md`
- [ ] Document common use cases:
  - Planning a single-day surf trip
  - Multi-day trip planning
  - Comparing surf spots
  - Understanding forecast information
- [ ] Include example conversations
- [ ] Explain skill level recommendations
- [ ] Add FAQ section
- [ ] Keep language clear and jargon-free

**Acceptance Criteria:**
- Users understand how to interact with system
- Common questions are answered
- Examples are realistic and helpful
- Easy to navigate and search

---

## Deployment and Operations

### Issue #27: Create Docker Configuration
**Labels:** deployment, infrastructure  
**Priority:** Medium  

**Description:**
Containerize the application for consistent deployment.

**Tasks:**
- [ ] Create `Dockerfile` with multi-stage build
- [ ] Use lightweight Python base image
- [ ] Create `docker-compose.yml` for local development
- [ ] Document environment variable requirements
- [ ] Keep Docker setup simple and standard
- [ ] Add health check in container
- [ ] Optimize image size

**Acceptance Criteria:**
- Application runs in Docker container
- Easy local development with docker-compose
- Clear documentation for Docker setup
- Fast build times

---

### Issue #28: Set Up Local Development Scripts
**Labels:** developer-experience, tooling  
**Priority:** Low  

**Description:**
Create helper scripts for common development tasks.

**Tasks:**
- [ ] Create `scripts/dev_server.sh` to run app locally
- [ ] Create `scripts/setup.sh` for initial environment setup
- [ ] Create `scripts/test.sh` to run full test suite
- [ ] Add `scripts/seed_data.sh` to populate sample spots
- [ ] Keep scripts simple and well-commented
- [ ] Make scripts cross-platform where possible
- [ ] Document all scripts in README

**Acceptance Criteria:**
- Scripts work on macOS and Linux
- Clear output and error messages
- Idempotent (safe to run multiple times)
- Well-documented

---

## Summary

**Total Issues: 28**

**Priority Breakdown:**
- High: 14 issues (core functionality)
- Medium: 11 issues (important features)
- Low: 3 issues (nice-to-have)

**Suggested Implementation Order:**
1. **Phase 1 - Foundation** (Issues #1-4): Project setup and infrastructure
2. **Phase 2 - Core Services** (Issues #5-10): LLM and forecasting layers
3. **Phase 3 - Knowledge & Planning** (Issues #11-16): Spot data and planning logic
4. **Phase 4 - State & Memory** (Issues #17-18): Session management
5. **Phase 5 - Interface** (Issues #19-21): API and web UI
6. **Phase 6 - Quality** (Issues #22-24): Testing and monitoring
7. **Phase 7 - Polish** (Issues #25-28): Documentation and deployment

**Clean Code Principles Applied:**
- **Simplicity**: Each issue focuses on a single, well-defined component
- **Consistency**: Similar patterns across services (models, API clients, etc.)
- **Clarity**: Descriptive names, clear acceptance criteria, explicit over implicit
