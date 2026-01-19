"""
SurfSense Conversational Agent (Layer 1)

The user-facing LLM agent responsible for:
- Personalized planning and dialogue management
- Understanding user intent and preferences
- Coordinating with other agents (Forecast, Contextual)
- Maintaining conversation state and context
"""

from typing import Any, Optional

from app.agents.base import AgentRole, BaseAgent
from app.core.llm_service import LLMService
from app.core.logger import get_logger

logger = get_logger(__name__)


class ConversationalAgent(BaseAgent):
    """
    Layer 1: Conversational Agent Core
    
    This is the main user-facing agent that:
    - Manages dialogue and conversation flow
    - Extracts user preferences and intent
    - Personalizes responses based on user profile
    - Delegates to specialized agents (Forecast, Contextual)
    """
    
    SYSTEM_PROMPT = """You are SurfSense, an AI surf trip planning assistant.

Your role is to help surfers plan their trips by:
1. Understanding their skill level, preferences, and constraints
2. Providing personalized surf spot recommendations
3. Analyzing forecast conditions for optimal timing
4. Considering practical factors (parking, accessibility, crowds)

Personality:
- Friendly and enthusiastic about surfing
- Clear and concise in explanations
- Safety-conscious (always consider user skill level)
- Helpful but honest about limitations

When gathering information, ask about:
- Skill level (beginner, intermediate, advanced)
- Preferred wave types and conditions
- Travel constraints (dates, distance, budget)
- Special needs (parking, accessibility)

Current conversation context:
{context}

User preferences:
{preferences}
"""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        forecast_agent: Optional["ForecastIntegrationAgent"] = None,
        contextual_agent: Optional["ContextualAgent"] = None,
    ):
        """
        Initialize the Conversational Agent.
        
        Args:
            llm_service: LLM service for generating responses.
            forecast_agent: Reference to forecast agent for data queries.
            contextual_agent: Reference to contextual agent for spot context.
        """
        super().__init__(
            role=AgentRole.CONVERSATIONAL,
            name="SurfSense Conversational Agent"
        )
        
        self._llm_service = llm_service
        self._forecast_agent = forecast_agent
        self._contextual_agent = contextual_agent
        
        # Register built-in tools
        self._register_default_tools()
    
    def _register_default_tools(self) -> None:
        """Register the default tools available to this agent."""
        self.register_tool(
            "get_forecast",
            self._tool_get_forecast,
            "Get surf forecast for a specific spot and date range"
        )
        self.register_tool(
            "set_user_skill",
            self._tool_set_user_skill,
            "Set the user's surfing skill level"
        )
        self.register_tool(
            "get_spot_info",
            self._tool_get_spot_info,
            "Get information about a surf spot"
        )
        self.register_tool(
            "get_spot_context",
            self._tool_get_spot_context,
            "Get contextual information (parking, safety, reviews, accessibility) for a surf spot"
        )
    
    async def _tool_get_forecast(
        self,
        spot_name: str,
        days: int = 3
    ) -> dict:
        """
        Tool: Get forecast data via the forecast agent.
        
        Args:
            spot_name: Name of the surf spot.
            days: Number of days to forecast.
            
        Returns:
            Forecast data dictionary.
        """
        if self._forecast_agent is None:
            return {"error": "Forecast agent not available"}
        
        # Delegate to forecast integration agent
        return await self._forecast_agent.get_forecast(spot_name, days)
    
    async def _tool_set_user_skill(self, skill_level: str) -> dict:
        """
        Tool: Set user's skill level preference.
        
        Args:
            skill_level: One of "beginner", "intermediate", "advanced"
            
        Returns:
            Confirmation dictionary.
        """
        valid_levels = ["beginner", "intermediate", "advanced"]
        skill_level = skill_level.lower()
        
        if skill_level not in valid_levels:
            return {"error": f"Invalid skill level. Choose from: {valid_levels}"}
        
        self.update_user_preference("skill_level", skill_level)
        return {"success": True, "skill_level": skill_level}
    
    async def _tool_get_spot_info(self, spot_name: str) -> dict:
        """
        Tool: Get information about a surf spot.
        
        Combines basic spot info from forecast agent with contextual data.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Spot information dictionary with contextual data.
        """
        result: dict[str, Any] = {
            "name": spot_name,
        }
        
        # Get basic spot info from forecast agent
        if self._forecast_agent is not None:
            spot_info = self._forecast_agent.get_spot_info(spot_name)
            if spot_info:
                result.update(spot_info)
        
        # Enrich with contextual data
        if self._contextual_agent is not None:
            try:
                context = await self._contextual_agent.get_spot_context(spot_name)
                result["context"] = self._contextual_agent.context_to_dict(context)
            except Exception as e:
                self.log_warning(f"Failed to get context for {spot_name}: {e}")
                result["context_error"] = str(e)
        else:
            result["context_note"] = "Contextual agent not available"
        
        return result
    
    async def _tool_get_spot_context(self, spot_name: str) -> dict:
        """
        Tool: Get contextual information for a surf spot.
        
        Returns parking, safety, reviews, and accessibility info.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Dictionary with contextual data.
        """
        if self._contextual_agent is None:
            return {"error": "Contextual agent not available"}
        
        try:
            context = await self._contextual_agent.get_spot_context(spot_name)
            return self._contextual_agent.context_to_dict(context)
        except Exception as e:
            self.log_error(f"Failed to get context: {e}")
            return {"error": str(e)}
    
    def get_system_prompt(self) -> str:
        """Build the system prompt with current context and preferences."""
        # Format context
        context_items = []
        if self.state.context:
            for key, value in self.state.context.items():
                context_items.append(f"- {key}: {value}")
        context_str = "\n".join(context_items) if context_items else "None"
        
        # Format preferences
        pref_items = []
        if self.state.user_preferences:
            for key, value in self.state.user_preferences.items():
                pref_items.append(f"- {key}: {value}")
        pref_str = "\n".join(pref_items) if pref_items else "None"
        
        return self.SYSTEM_PROMPT.format(
            context=context_str,
            preferences=pref_str
        )
    
    async def process(self, user_input: str) -> str:
        """
        Process user input and generate a response.
        
        This is the main conversation loop:
        1. Add user message to history
        2. Build prompt with context
        3. Generate response via LLM
        4. Extract any tool calls or preference updates
        5. Return response
        
        Args:
            user_input: The user's message.
            
        Returns:
            The agent's response.
        """
        # Add user message to state
        self.state.add_message("user", user_input)
        self.log_debug(f"Processing user input: {user_input[:50]}...")
        
        # Check for direct preference setting
        await self._extract_preferences(user_input)
        
        # Build the full prompt
        prompt = self._build_prompt(user_input)
        
        # Generate response
        if self._llm_service is None:
            response = self._fallback_response(user_input)
        else:
            try:
                response = self._llm_service.generate(prompt)
            except Exception as e:
                self.log_error(f"LLM generation failed: {e}")
                response = "I'm having trouble processing that. Could you try again?"
        
        # Add assistant response to history
        self.state.add_message("assistant", response)
        
        return response
    
    async def _extract_preferences(self, user_input: str) -> None:
        """
        Extract and store user preferences from input.
        
        Looks for common preference patterns like skill level mentions.
        """
        user_lower = user_input.lower()
        
        # Simple skill level detection
        if "beginner" in user_lower:
            self.update_user_preference("skill_level", "beginner")
        elif "intermediate" in user_lower:
            self.update_user_preference("skill_level", "intermediate")
        elif "advanced" in user_lower or "expert" in user_lower:
            self.update_user_preference("skill_level", "advanced")
    
    def _build_prompt(self, user_input: str) -> str:
        """
        Build the full prompt for the LLM.
        
        Combines system prompt, conversation history, and user input.
        """
        # Get recent conversation history
        recent = self.state.get_recent_messages(6)
        
        # Build conversation context
        history_text = ""
        for msg in recent[:-1]:  # Exclude current message
            if msg.role == "user":
                history_text += f"User: {msg.content}\n"
            elif msg.role == "assistant":
                history_text += f"Assistant: {msg.content}\n"
        
        # Combine into prompt
        system = self.get_system_prompt()
        
        if history_text:
            prompt = f"{system}\n\nConversation so far:\n{history_text}\nUser: {user_input}"
        else:
            prompt = f"{system}\n\nUser: {user_input}"
        
        return prompt
    
    def _fallback_response(self, user_input: str) -> str:
        """Generate a fallback response when LLM is unavailable."""
        return (
            "I'm SurfSense, your surf trip planning assistant! "
            "I'm currently running in limited mode without full LLM capabilities. "
            "Please ensure the LLM service is properly configured."
        )
    
    def set_forecast_agent(self, agent: "ForecastIntegrationAgent") -> None:
        """Set the forecast integration agent reference."""
        self._forecast_agent = agent
        self.log_info("Forecast agent connected")
    
    def set_contextual_agent(self, agent: "ContextualAgent") -> None:
        """Set the contextual agent reference."""
        self._contextual_agent = agent
        self.log_info("Contextual agent connected")
    
    def set_llm_service(self, service: LLMService) -> None:
        """Set the LLM service."""
        self._llm_service = service
        self.log_info("LLM service connected")


# Avoid circular import
from app.agents.forecast_integration import ForecastIntegrationAgent
from app.agents.contextual_agent import ContextualAgent
