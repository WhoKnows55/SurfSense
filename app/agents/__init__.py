"""
SurfSense Agent Layer

Provides intelligent agents that orchestrate the system:
- ConversationalAgent: User-facing dialogue and personalization (Layer 1)
- ContextualAgent: Aggregates contextual data providers (Layer 2)
- ForecastIntegrationAgent: Integrates forecast APIs and data (Layer 3)
"""

from app.agents.base import BaseAgent
from app.agents.contextual_agent import ContextualAgent
from app.agents.conversational import ConversationalAgent
from app.agents.forecast_integration import ForecastIntegrationAgent

__all__ = [
    "BaseAgent",
    "ContextualAgent",
    "ConversationalAgent",
    "ForecastIntegrationAgent",
]
