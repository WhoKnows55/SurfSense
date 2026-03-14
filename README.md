# 🏄 SurfSense - AI Surf Trip Planning Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A **terminal-based conversational AI assistant** that helps surfers plan trips by analyzing surf forecasts, evaluating conditions against skill levels, and creating optimized multi-day itineraries. Powered by **Azure OpenAI GPT-4o** with function-calling, delegating to deterministic sub-agents for data aggregation, condition assessment, and trip planning.

## 🌊 Features

- **🤖 Azure OpenAI Orchestrator**: GPT-4o with function-calling manages dialogue and delegates to specialized sub-agents
- **💬 Terminal Chat Interface**: Natural conversation — no slash commands needed, just describe your trip
- **🌊 Multi-Source Forecasts**: Integrates Stormglass (paid) and Open-Meteo (free, no API key) for wave, swell, wind, and tide data
- **📊 Skill-Level Safety**: Deterministic scoring evaluates conditions against beginner/intermediate/advanced thresholds
- **📅 Trip Optimization**: Greedy multi-day itinerary planning with travel-time penalties (Haversine) and spot diversity
- **🏖️ Contextual Data**: Parking, accessibility, reviews, and safety information for surf spots
- **🗺️ 16 Built-in Spots**: Pre-configured surf spot database with coordinates, break types, and hazard data

## 📋 Prerequisites

- **Python 3.10+**
- **Azure OpenAI** API access (GPT-4o deployment with function-calling support)
- macOS, Linux, or Windows

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd SurfSense

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
make install
# Or manually:
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials:
#   AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
#   AZURE_OPENAI_API_KEY=<your-key>
#   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

### 4. Start Chatting!

```bash
make run
# Or:
python -m app
```

## 💬 Example Conversation

```
============================================================
🏄 SurfSense - AI Surf Trip Planning Assistant
============================================================

Version: 0.1.0

📋 Configuration Summary:
   LLM Provider: azure_openai
   Deployment: gpt-4o

✅ Ready! Type 'quit' or 'exit' to leave.

------------------------------------------------------------

🧑 You: I'm planning a surf trip to Oahu next weekend. I'm an intermediate surfer.

🤖 SurfSense: Great choice! Let me check the conditions for Oahu spots...

   Day 1 (Saturday): Waikiki, 7-11am
   - Conditions: 2-3ft waves, light offshore winds, ideal for intermediate
   - Parking: $5/hr in nearby lots

   Day 2 (Sunday): Waikiki 7-10am, then Sunset Beach 2-4pm
   - Sunset has a suitable window with manageable conditions.

   ⚠️ Safety note: Pipeline is recommended for advanced+ surfers
   and has been excluded from your itinerary.

🧑 You: /reset

🔄 Conversation reset.

🧑 You: quit

👋 Goodbye!
```

## 📁 Project Structure

```
SurfSense/
├── app/
│   ├── __init__.py              # Package info and version
│   ├── __main__.py              # Terminal chat entry point
│   ├── agents/
│   │   ├── orchestrator.py      # LLM-powered orchestrator (function-calling)
│   │   ├── forecast_data_agent.py   # Data aggregation sub-agent
│   │   ├── condition_agent.py       # Condition assessment sub-agent
│   │   └── trip_planning_agent.py   # Trip planning sub-agent
│   ├── core/
│   │   ├── llm_service.py       # Azure OpenAI + fallback providers
│   │   └── logger.py            # Structured logging with redaction
│   ├── forecasting/
│   │   ├── models.py            # Unified forecast data models (Pydantic)
│   │   ├── openmeteo_client.py  # Open-Meteo API (free, no key)
│   │   ├── stormglass_client.py # Stormglass API (paid, 10 req/day free)
│   │   └── noaa_client.py       # NOAA Marine Weather (US only)
│   ├── contextual/
│   │   ├── parking.py           # Parking data provider
│   │   ├── accessibility.py     # Accessibility data provider
│   │   ├── reviews.py           # Reviews data provider
│   │   └── safety.py            # Safety/hazard data provider
│   ├── planning/
│   │   ├── condition_assessor.py    # Deterministic condition scoring
│   │   ├── window_finder.py         # Surf window identification
│   │   ├── trip_planner.py          # Multi-day itinerary optimization
│   │   └── travel_utils.py          # Haversine distance calculations
│   └── knowledge/
│       └── spot_database.py     # Surf spot database (16 spots)
├── config/
│   └── settings.py              # Type-safe Pydantic configuration
├── data/
│   └── spots.json               # Surf spot metadata
├── tests/                       # Unit tests for sub-agents
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
├── Makefile                     # Common commands
└── README.md
```

## ⚙️ Configuration

All settings are in `.env` (copy from `.env.example`):

### Azure OpenAI (Required)

| Variable | Default | Description |
|----------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | *(empty)* | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_API_KEY` | *(empty)* | Azure OpenAI API key |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o` | Azure deployment name |
| `AZURE_OPENAI_API_VERSION` | `2024-10-21` | API version |
| `AZURE_OPENAI_TEMPERATURE` | `0.7` | Sampling temperature (0.0–2.0) |
| `AZURE_OPENAI_MAX_TOKENS` | `2000` | Max tokens in LLM response |

### Forecast API (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `FORECAST_API_PROVIDER` | `stormglass` | Forecast data source |
| `FORECAST_API_KEY` | *(empty)* | API key (Stormglass). Open-Meteo is used as free fallback |

### Skill Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `BEGINNER_MAX_WAVE_HEIGHT` | `1.5` | Max wave height (m) for beginner |
| `BEGINNER_MAX_WIND_SPEED` | `15` | Max wind speed (kph) for beginner |
| `INTERMEDIATE_MAX_WAVE_HEIGHT` | `2.5` | Max wave height (m) for intermediate |
| `INTERMEDIATE_MAX_WIND_SPEED` | `20` | Max wind speed (kph) for intermediate |
| `ADVANCED_MAX_WAVE_HEIGHT` | `5.0` | Max wave height (m) for advanced |
| `ADVANCED_MAX_WIND_SPEED` | `30` | Max wind speed (kph) for advanced |

## 🛠️ Development

### Make Commands

```bash
make help      # Show all available commands
make install   # Install dependencies
make run       # Start the chat application
make test      # Run test suite
make clean     # Remove cache files
```

### Chat Commands

| Command | Description |
|---------|-------------|
| `/reset` | Clear conversation history and cached data |
| `/help` | Show available commands |
| `quit` / `exit` | Exit the application |

## 🏗️ Architecture

SurfSense follows a **single-orchestrator, multi-agent** pattern:

```
User (Terminal)
      │
      ▼
┌──────────────────────────────────────────────────┐
│          Orchestrator (LLM-powered)              │
│  Azure OpenAI GPT-4o with function-calling       │
│  • Manages dialogue and preference elicitation   │
│  • Selects which sub-agent tool to call          │
│  • Synthesises sub-agent outputs into responses  │
└─────────┬──────────────┬──────────────┬──────────┘
          │              │              │
          ▼              ▼              ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│  Forecast & │  │  Condition   │  │    Trip      │
│    Data     │  │  Assessment  │  │  Planning    │
│ Aggregation │  │    Agent     │  │    Agent     │
│    Agent    │  │              │  │              │
│             │  │ • assess_    │  │ • find_surf_ │
│ • fetch_    │  │   conditions │  │   windows    │
│   forecast  │  │ • check_    │  │ • plan_      │
│ • fetch_    │  │   safety    │  │   itinerary  │
│   context   │  │ • get_skill_│  │ • rank_spots │
│ • get_spot_ │  │   thresholds│  │              │
│   metadata  │  │              │  │              │
└─────────────┘  └──────────────┘  └──────────────┘
       │                │                  │
       ▼                ▼                  ▼
  External APIs    config/settings.py   Haversine +
  (Open-Meteo,     (SkillLevel          greedy
   Stormglass)      Thresholds)         optimisation
```

### Design Principles

- **Single LLM point**: Only the orchestrator calls Azure OpenAI — predictable token costs, no non-determinism in safety scoring
- **Function-calling as delegation**: GPT-4o decides which tools to invoke; tool results feed back into the conversation
- **Deterministic sub-agents**: Python classes with scoring formulas, API calls, and optimization algorithms — no LLM calls

## 🧪 Testing

```bash
# Run all tests
make test

# Or with pytest directly
pytest tests/ -v
```

## 🆘 Troubleshooting

### Azure OpenAI Connection Error?

Verify your credentials in `.env`:

```bash
# Test your Azure OpenAI setup
python -c "from openai import AzureOpenAI; print('OK')"
```

Ensure your deployment supports function-calling (GPT-4o recommended).

### Import Errors?

```bash
# Ensure venv is activated and dependencies installed
source .venv/bin/activate
pip install -r requirements.txt
```

### Forecast Data Unavailable?

Open-Meteo (free, no API key) is used as the default forecast source. If it's down, configure Stormglass as a fallback:

```bash
# In .env:
FORECAST_API_PROVIDER=stormglass
FORECAST_API_KEY=<your-stormglass-key>
```

---

**Built with ❤️ for the surfing community** 🌊
