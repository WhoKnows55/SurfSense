"""
SurfSense Base Agent

Abstract base class for all agents in the system.
Agents are intelligent components that can reason, use tools, and maintain state.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.core.logger import LoggerMixin, get_logger

logger = get_logger(__name__)


class AgentRole(str, Enum):
    """Defines the role/type of an agent."""
    CONVERSATIONAL = "conversational"
    FORECAST_INTEGRATION = "forecast_integration"
    CONTEXTUAL = "contextual"


@dataclass
class AgentMessage:
    """A message in the agent's conversation history."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentState:
    """Tracks the state of an agent during a conversation."""
    conversation_history: list[AgentMessage] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    
    def add_message(self, role: str, content: str, **metadata) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append(
            AgentMessage(role=role, content=content, metadata=metadata)
        )
        if role == "user":
            self.turn_count += 1
    
    def get_recent_messages(self, n: int = 10) -> list[AgentMessage]:
        """Get the n most recent messages."""
        return self.conversation_history[-n:]
    
    def clear_history(self) -> None:
        """Clear conversation history but keep preferences."""
        self.conversation_history = []
        self.turn_count = 0


class BaseAgent(ABC, LoggerMixin):
    """
    Abstract base class for all SurfSense agents.
    
    Agents are intelligent components that:
    - Maintain conversation state
    - Can use tools/functions
    - Reason about user intent
    - Coordinate with other agents
    """
    
    def __init__(self, role: AgentRole, name: str):
        """
        Initialize the agent.
        
        Args:
            role: The agent's role in the system.
            name: Human-readable name for logging.
        """
        self.role = role
        self.name = name
        self.state = AgentState()
        self._tools: dict[str, callable] = {}
        self.log_info(f"Agent initialized: {name} ({role.value})")
    
    @abstractmethod
    async def process(self, user_input: str) -> str:
        """
        Process user input and generate a response.
        
        This is the main entry point for agent interaction.
        
        Args:
            user_input: The user's message.
            
        Returns:
            The agent's response.
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt that defines this agent's behavior.
        
        Returns:
            The system prompt string.
        """
        pass
    
    def register_tool(self, name: str, func: callable, description: str = "") -> None:
        """
        Register a tool that this agent can use.
        
        Args:
            name: Tool name for LLM function calling.
            func: The callable to execute.
            description: Description of what the tool does.
        """
        self._tools[name] = {
            "function": func,
            "description": description,
        }
        self.log_debug(f"Registered tool: {name}")
    
    def get_available_tools(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())
    
    async def call_tool(self, name: str, **kwargs) -> Any:
        """
        Call a registered tool.
        
        Args:
            name: The tool name.
            **kwargs: Arguments to pass to the tool.
            
        Returns:
            The tool's result.
            
        Raises:
            KeyError: If tool is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        
        tool = self._tools[name]
        self.log_debug(f"Calling tool: {name}", kwargs=kwargs)
        
        result = tool["function"](**kwargs)
        
        # Handle async tools
        if hasattr(result, "__await__"):
            result = await result
        
        return result
    
    def update_user_preference(self, key: str, value: Any) -> None:
        """
        Update a user preference.
        
        Args:
            key: Preference key (e.g., "skill_level", "preferred_spots").
            value: The preference value.
        """
        self.state.user_preferences[key] = value
        self.log_debug(f"Updated preference: {key}={value}")
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference value."""
        return self.state.user_preferences.get(key, default)
    
    def set_context(self, key: str, value: Any) -> None:
        """Set a context value for the current conversation."""
        self.state.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.state.context.get(key, default)
    
    def reset(self) -> None:
        """Reset the agent state for a new conversation."""
        self.state = AgentState()
        self.log_info(f"Agent reset: {self.name}")
