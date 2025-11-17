# 🏄 SurfSense - AI Surf Trip Planning Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A conversational desktop web application that helps surfers plan trips by analyzing real-time surf forecasts, providing spot recommendations, and creating personalized multi-day itineraries.

## 🌊 Features

- **Natural Language Interface**: Chat with an AI assistant to plan your surf trips
- **Real-Time Forecasts**: Integration with surf forecast APIs for accurate conditions
- **Smart Recommendations**: Skill-level based suitability assessments
- **Multi-Day Planning**: Optimized itineraries for extended surf trips
- **Spot Comparison**: Compare multiple surf spots for the same time period
- **Local Fallback**: Time-series forecasting when APIs are unavailable

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- An OpenAI API key
- (Optional) Surf forecast API key (Surfline, Stormglass, etc.)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
cd /path/to/your/workspace
git clone <repository-url>
cd SurfSense
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys and settings
# Required: OPENAI_API_KEY
# Optional: FORECAST_API_KEY
```

### 5. Run the Application

```bash
python -m app
```

You should see the welcome message confirming the setup is complete.

## 📁 Project Structure

```
surfsense/
├── app/
│   ├── __init__.py           # Application package
│   ├── __main__.py           # Entry point (python -m app)
│   ├── core/                 # Core services (LLM, tools, config)
│   ├── forecasting/          # Forecast API and models
│   ├── knowledge/            # Surf spot knowledge base
│   ├── planning/             # Trip planning engine
│   ├── state/                # Session and memory management
│   └── interfaces/           # API and web UI
├── tests/                    # Test suite
├── config/                   # Configuration modules
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Or use make command
make test
```

### Available Make Commands

```bash
make help      # Show all available commands
make install   # Install dependencies
make test      # Run test suite
make run       # Start the application
make clean     # Remove cache files
```

## 🔧 Configuration

All configuration is managed through environment variables in the `.env` file:

### Required Settings

- `OPENAI_API_KEY`: Your OpenAI API key for the LLM

### Optional Settings

- `LLM_MODEL_NAME`: OpenAI model to use (default: gpt-4-turbo-preview)
- `LLM_TEMPERATURE`: Response creativity (default: 0.7)
- `FORECAST_API_KEY`: External forecast API key
- `API_PORT`: Web server port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

See `.env.example` for all available configuration options.

## 📖 Usage

### Basic Conversation

```
User: "I want to surf in San Diego next weekend"
SurfSense: Analyzes forecasts and provides recommendations...

User: "What about Trestles vs Blacks Beach?"
SurfSense: Compares spots and suggests best option...
```

### Planning a Multi-Day Trip

```
User: "Plan a 5-day surf trip to Costa Rica in December"
SurfSense: Creates day-by-day itinerary with:
- Best surf windows each day
- Spot recommendations
- Skill-appropriate conditions
- Safety considerations
```

## 🏗️ Architecture

SurfSense follows clean architecture principles:

- **Simplicity**: Clear, single-purpose components
- **Consistency**: Uniform patterns across layers
- **Clarity**: Explicit naming and well-documented code

### Key Layers

1. **Core Layer**: LLM orchestration, configuration, logging
2. **Forecasting Layer**: API integration, local models, data schema
3. **Knowledge Layer**: Surf spot database and search
4. **Planning Layer**: Suitability rules, trip planning algorithms
5. **State Layer**: Session management, context extraction
6. **Interface Layer**: REST API, web UI

## 🧪 Testing Strategy

- **Unit Tests**: Individual component testing with mocked dependencies
- **Integration Tests**: End-to-end workflow testing
- **Test Coverage**: Target >80% code coverage
- **Clear Test Names**: Descriptive test function names

## 🚧 Development Roadmap

See `github_issues.md` for detailed implementation plan:

- [x] Phase 1: Project Setup (Issue #1-4)
- [ ] Phase 2: Core Services (Issue #5-10)
- [ ] Phase 3: Knowledge & Planning (Issue #11-16)
- [ ] Phase 4: State & Memory (Issue #17-18)
- [ ] Phase 5: Interface (Issue #19-21)
- [ ] Phase 6: Quality (Issue #22-24)
- [ ] Phase 7: Polish (Issue #25-28)

## 🤝 Contributing

1. Follow clean code principles
2. Write tests for new features
3. Keep functions small and focused
4. Use clear, descriptive names

## 🆘 Troubleshooting

### Import Errors

```bash
# Make sure you're in the project root and venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

### API Key Issues

```bash
# Check your .env file exists and has the correct keys
cat .env | grep OPENAI_API_KEY
```

### Module Not Found

```bash
# Ensure app/ has __init__.py files
find app -name "__init__.py"
```

## 📞 Support

For issues and questions:
- Review `github_issues.md` for implementation details
- Open an issue on GitHub

---

**Built with ❤️ for the surfing community**
