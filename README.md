# 🏄 SurfSense - AI Surf Trip Planning Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A **terminal-based conversational AI assistant** that helps surfers plan trips by analyzing surf forecasts, providing spot recommendations, and creating personalized itineraries. Powered by a **free, local LLM** (Phi-3 mini) that runs entirely on your machine—no API keys required!

## 🌊 Features

- **🤖 Free Local AI**: Uses Microsoft's Phi-3 mini model—runs locally, no API costs
- **💬 Terminal Chat Interface**: Simple, distraction-free conversation in your terminal
- **🌊 Surf Forecast Analysis**: Integration with forecast APIs for real-time conditions
- **📊 Skill-Level Matching**: Recommendations based on your surfing ability
- **📅 Trip Planning**: Multi-day itinerary suggestions with optimal surf windows
- **🔄 Offline Capable**: Local model works without internet (after initial download)

## 📋 Prerequisites

- **Python 3.10+**
- **8GB+ RAM** recommended (for running local LLM)
- **~5GB disk space** (for model download)
- macOS, Linux, or Windows

> **Note**: GPU is optional but speeds up responses. Works on CPU (Apple Silicon M1/M2/M3 uses Metal acceleration automatically).

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

### 3. Configure (Optional)

```bash
cp .env.example .env
# Edit .env if you want to customize settings
# The defaults work out of the box!
```

### 4. Start Chatting!

```bash
make run
# Or:
python -m app
```

The first run will download the Phi-3 mini model (~2.5GB). After that, it starts instantly.

## 💬 Example Conversation

```
============================================================
🏄 SurfSense - AI Surf Trip Planning Assistant
============================================================

Version: 0.1.0

📋 Configuration Summary:
   LLM Provider: local
   LLM Model: microsoft/Phi-3-mini-4k-instruct

🏄 Loading model... (this may take a moment)

✅ Ready to chat! Type 'quit' or 'exit' to leave.

------------------------------------------------------------

🧑 You: I'm planning a surf trip to San Diego next weekend. I'm an intermediate surfer.

🤖 SurfSense: Great choice! San Diego has excellent options for intermediate surfers...

🧑 You: What about comparing Blacks Beach vs La Jolla Shores?

🤖 SurfSense: Here's a comparison for an intermediate surfer...

🧑 You: quit

👋 Goodbye! Catch some waves!
```

## 📁 Project Structure

```
SurfSense/
├── app/
│   ├── __init__.py           # Package info and version
│   ├── __main__.py           # Terminal chat entry point
│   └── core/
│       ├── __init__.py
│       ├── llm_service.py    # LLM providers (local & OpenAI)
│       └── logger.py         # Structured logging
├── config/
│   ├── __init__.py
│   └── settings.py           # Type-safe configuration
├── tests/                    # Test suite
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── Makefile                  # Common commands
└── README.md                 # This file
```

## ⚙️ Configuration

All settings are in `.env` (copy from `.env.example`):

### LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `local` | `local` for Phi-3, `openai` for OpenAI API |
| `LLM_MODEL_NAME` | `microsoft/Phi-3-mini-4k-instruct` | Hugging Face model or OpenAI model name |
| `LLM_TEMPERATURE` | `0.7` | Response creativity (0.0-2.0) |
| `LLM_MAX_TOKENS` | `500` | Max response length |
| `LLM_USE_CPU` | `false` | Force CPU (disable GPU acceleration) |
| `OPENAI_API_KEY` | *(empty)* | Only needed if `LLM_PROVIDER=openai` |

### Forecast Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `FORECAST_API_PROVIDER` | `stormglass` | Forecast data source |
| `FORECAST_API_KEY` | *(empty)* | API key for forecast provider |

## 🛠️ Development

### Make Commands

```bash
make help      # Show all available commands
make install   # Install dependencies
make run       # Start the chat application
make test      # Run test suite
make clean     # Remove cache files
```

### Using OpenAI Instead

If you prefer OpenAI's models:

```bash
# In .env:
LLM_PROVIDER=openai
LLM_MODEL_NAME=gpt-4-turbo-preview
OPENAI_API_KEY=sk-your-key-here
```

### Switching Models

You can use any Hugging Face model compatible with the `transformers` library:

```bash
# In .env:
LLM_MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
# Or any other chat model
```

## 🏗️ Architecture

SurfSense follows clean code principles:

- **Simplicity**: Single-purpose, focused components
- **Clarity**: Descriptive names, well-documented code
- **Type Safety**: Pydantic models for configuration validation
- **Modularity**: Easy to swap LLM providers or add new features

### Core Components

1. **LLM Service** (`app/core/llm_service.py`): Unified interface for local and API-based LLMs
2. **Configuration** (`config/settings.py`): Type-safe settings with validation
3. **Logging** (`app/core/logger.py`): Structured logging with sensitive data filtering

## 🧪 Testing

```bash
# Run all tests
make test

# Or with pytest directly
pytest tests/ -v
```

## 🆘 Troubleshooting

### Model Download Slow?

The first run downloads ~2.5GB. Use a good internet connection or pre-download:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
AutoModelForCausalLM.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
```

### Out of Memory?

Try forcing CPU mode (slower but uses less RAM):

```bash
# In .env:
LLM_USE_CPU=true
```

### Import Errors?

```bash
# Ensure venv is activated and dependencies installed
source .venv/bin/activate
pip install -r requirements.txt
```

### Slow Responses on CPU?

This is normal for local LLMs on CPU. Consider:
- Using a machine with GPU
- Using OpenAI API instead (`LLM_PROVIDER=openai`)
- Reducing `LLM_MAX_TOKENS`

## 📞 Support

- Check `github_issues.md` for the development roadmap
- Open an issue on GitHub for bugs or feature requests

---

**Built with ❤️ for the surfing community**

*No API keys. No cloud. Just you, your terminal, and the waves.* 🌊
