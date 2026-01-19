"""
SurfSense Agent Layer

Provides intelligent agents that orchestrate the system:
- ConversationalAgent: User-facing dialogue and personalization (Layer 1)
- ForecastIntegrationAgent: Integrates forecast APIs and data (Layer 3)
"""

from app.agents.base import BaseAgent
from app.agents.conversational import ConversationalAgent
from app.agents.forecast_integration import ForecastIntegrationAgent

__all__ = [
    "BaseAgent",
    "ConversationalAgent",
    "ForecastIntegrationAgent",
]
