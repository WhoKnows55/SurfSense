"""
SurfSense Conversational Agent (Layer 1)

The user-facing LLM agent responsible for:
- Personalized planning and dialogue management
- Understanding user intent and preferences
- Coordinating with other agents (Forecast, Contextual)
- Maintaining conversation state and context
- Guided trip planning flow
"""

from typing import TYPE_CHECKING, Any, Optional

from app.agents.base import AgentRole, BaseAgent
from app.agents.trip_planning_state import (
    PlanningStage,
    RequiredField,
    TransportMode,
    TripInfoExtractor,
    TripPlanningState,
)
from app.core.llm_service import LLMService
from app.core.logger import get_logger

if TYPE_CHECKING:
    from app.agents.forecast_integration import ForecastIntegrationAgent
    from app.agents.contextual_agent import ContextualAgent

logger = get_logger(__name__)


# Intent detection patterns
TRIP_PLANNING_TRIGGERS = [
    "plan a trip",
    "plan my trip",
    "plan a surf trip",
    "planning a trip",
    "help me plan",
    "want to surf",
    "going surfing",
    "surf trip",
    "trip to",
    "want to go to",
    "weekend surf",
    "surfing this weekend",
    "let's plan",
    "help plan",
]


class ConversationalAgent(BaseAgent):
    """
    Layer 1: Conversational Agent Core
    
    This is the main user-facing agent that:
    - Manages dialogue and conversation flow
    - Extracts user preferences and intent
    - Personalizes responses based on user profile
    - Delegates to specialized agents (Forecast, Contextual)
    - Guides users through trip planning with targeted questions
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

Trip planning status:
{trip_planning_status}
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
        
        # Trip planning state
        self._trip_state = TripPlanningState()
        self._info_extractor = TripInfoExtractor()
        
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
        
        # Format trip planning status
        if self._trip_state.stage != PlanningStage.IDLE:
            trip_status = self._trip_state.format_summary()
        else:
            trip_status = "Not currently planning a trip"
        
        return self.SYSTEM_PROMPT.format(
            context=context_str,
            preferences=pref_str,
            trip_planning_status=trip_status,
        )
    
    async def process(self, user_input: str) -> str:
        """
        Process user input and generate a response.
        
        This is the main conversation loop:
        1. Add user message to history
        2. Check for trip planning intent or continuation
        3. Extract information from user input
        4. Build prompt with context
        5. Generate response via LLM
        6. Return response (possibly with guided questions)
        
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
        
        # Handle trip planning flow
        trip_response = await self._handle_trip_planning(user_input)
        if trip_response:
            self.state.add_message("assistant", trip_response)
            return trip_response
        
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
    
    async def _handle_trip_planning(self, user_input: str) -> Optional[str]:
        """
        Handle the guided trip planning flow.
        
        Returns a response if we're in trip planning mode, or None to 
        continue with normal processing.
        """
        user_lower = user_input.lower()
        
        # Check if user wants to cancel/restart
        if any(word in user_lower for word in ["cancel", "start over", "reset", "nevermind"]):
            if self._trip_state.stage != PlanningStage.IDLE:
                self._trip_state.reset()
                return "No problem! Trip planning cancelled. Let me know when you'd like to start fresh. 🏄"
        
        # Check if this triggers trip planning
        if self._trip_state.stage == PlanningStage.IDLE:
            if self._detect_trip_intent(user_input):
                return await self._start_trip_planning(user_input)
            return None  # Not trip planning, continue normal flow
        
        # We're in the middle of trip planning
        return await self._continue_trip_planning(user_input)
    
    def _detect_trip_intent(self, user_input: str) -> bool:
        """Detect if user wants to plan a surf trip."""
        user_lower = user_input.lower()
        
        for trigger in TRIP_PLANNING_TRIGGERS:
            if trigger in user_lower:
                return True
        return False
    
    async def _start_trip_planning(self, user_input: str) -> str:
        """Start the guided trip planning flow."""
        self.log_info("Starting guided trip planning flow")
        self._trip_state.stage = PlanningStage.GATHERING_INFO
        
        # Try to extract any info already provided in the initial message
        response_parts = ["Awesome, let's plan your surf trip! 🌊🏄"]
        
        extracted = self._extract_trip_info(user_input)
        if extracted:
            confirmations = []
            for field, value in extracted:
                conf = self._trip_state.get_confirmation_message(field, str(value))
                confirmations.append(conf)
            response_parts.append(" ".join(confirmations))
        
        # Ask for next missing piece of info
        next_q = self._trip_state.get_next_question()
        if next_q:
            field, question = next_q
            response_parts.append(f"\n\n{question}")
        else:
            # All info already provided!
            return await self._complete_info_gathering()
        
        return " ".join(response_parts)
    
    async def _continue_trip_planning(self, user_input: str) -> str:
        """Continue the guided trip planning flow with user's response."""
        # Extract info from this response
        extracted = self._extract_trip_info(user_input)
        
        if not extracted and self._trip_state.last_asked_field:
            # Try to interpret as direct answer to last question
            field = self._trip_state.last_asked_field
            value = self._interpret_field_response(field, user_input)
            if value:
                extracted = [(field, value)]
        
        response_parts = []
        
        if extracted:
            for field, value in extracted:
                # Set the field
                if field == RequiredField.SURF_DATES:
                    self._trip_state.set_surf_dates(value)
                else:
                    self._trip_state.set_field(field, value)
                
                # Add confirmation
                if field == RequiredField.SURF_DATES:
                    date_str = ", ".join(d.strftime("%b %d") for d in value)
                    conf = self._trip_state.get_confirmation_message(field, date_str)
                else:
                    conf = self._trip_state.get_confirmation_message(field, str(value))
                response_parts.append(conf)
        else:
            # Didn't understand the response
            response_parts.append(
                "I didn't quite catch that. "
            )
        
        # Check if we have all info
        if self._trip_state.is_info_complete():
            return await self._complete_info_gathering()
        
        # Ask for next missing piece
        next_q = self._trip_state.get_next_question()
        if next_q:
            field, question = next_q
            response_parts.append(f"\n\n{question}")
        
        return " ".join(response_parts) if response_parts else await self._complete_info_gathering()
    
    def _extract_trip_info(self, text: str) -> list[tuple[RequiredField, Any]]:
        """Extract all trip planning info from text."""
        extracted = []
        
        # Skill level
        if not self._trip_state.skill_level:
            skill = self._info_extractor.extract_skill_level(text)
            if skill:
                self._trip_state.skill_level = skill
                extracted.append((RequiredField.SKILL_LEVEL, skill))
        
        # Transport mode
        if not self._trip_state.transport_mode:
            transport = self._info_extractor.extract_transport_mode(text)
            if transport:
                self._trip_state.transport_mode = transport
                mode_str = "Driving" if transport == TransportMode.CAR else "Public transport"
                extracted.append((RequiredField.TRANSPORT_MODE, mode_str))
        
        # Dates
        if not self._trip_state.surf_dates:
            dates = self._info_extractor.extract_dates(text)
            if dates:
                self._trip_state.set_surf_dates(dates)
                extracted.append((RequiredField.SURF_DATES, dates))
        
        # Destination (simple keyword matching for now)
        if not self._trip_state.destination:
            dest = self._extract_destination(text)
            if dest:
                self._trip_state.destination = dest
                extracted.append((RequiredField.DESTINATION, dest))
        
        # Origin
        if not self._trip_state.origin:
            origin = self._extract_origin(text)
            if origin:
                self._trip_state.origin = origin
                extracted.append((RequiredField.ORIGIN, origin))
        
        return extracted
    
    def _extract_destination(self, text: str) -> Optional[str]:
        """Extract destination from text."""
        # Look for known spots/regions from forecast agent
        if self._forecast_agent:
            spots = self._forecast_agent.get_all_spots()
            text_lower = text.lower()
            for spot in spots:
                if spot.lower() in text_lower:
                    return spot
        
        # Look for destination patterns
        patterns = [
            "to ",
            "surf at ",
            "surfing at ",
            "want to go to ",
            "heading to ",
            "going to ",
        ]
        text_lower = text.lower()
        for pattern in patterns:
            if pattern in text_lower:
                idx = text_lower.index(pattern) + len(pattern)
                # Get the next few words
                remaining = text[idx:].strip()
                words = remaining.split()[:3]  # Take up to 3 words
                if words:
                    # Clean up common endings
                    dest = " ".join(words).rstrip(".,!?")
                    return dest
        
        return None
    
    def _extract_origin(self, text: str) -> Optional[str]:
        """Extract origin from text."""
        patterns = [
            "from ",
            "coming from ",
            "traveling from ",
            "starting from ",
            "leaving from ",
            "live in ",
            "based in ",
        ]
        text_lower = text.lower()
        for pattern in patterns:
            if pattern in text_lower:
                idx = text_lower.index(pattern) + len(pattern)
                remaining = text[idx:].strip()
                words = remaining.split()[:3]
                if words:
                    origin = " ".join(words).rstrip(".,!?")
                    return origin
        return None
    
    def _interpret_field_response(
        self, field: RequiredField, text: str
    ) -> Optional[Any]:
        """Interpret a response as a direct answer to a specific question."""
        text = text.strip()
        
        if field == RequiredField.SKILL_LEVEL:
            text_lower = text.lower()
            if "begin" in text_lower or "new" in text_lower:
                return "beginner"
            elif "inter" in text_lower or "some" in text_lower:
                return "intermediate"
            elif "adv" in text_lower or "exp" in text_lower:
                return "advanced"
        
        elif field == RequiredField.TRANSPORT_MODE:
            text_lower = text.lower()
            if any(w in text_lower for w in ["car", "driv", "vehicle"]):
                return "car"
            elif any(w in text_lower for w in ["public", "transit", "bus", "train"]):
                return "public transport"
        
        elif field == RequiredField.SURF_DATES:
            return self._info_extractor.extract_dates(text)
        
        elif field in (RequiredField.DESTINATION, RequiredField.ORIGIN):
            # Accept the raw text as the location
            if len(text) > 2 and len(text) < 100:
                return text
        
        return None
    
    async def _complete_info_gathering(self) -> str:
        """Called when all required info has been gathered."""
        self._trip_state.stage = PlanningStage.INFO_COMPLETE
        self.log_info(f"Trip planning info complete: {self._trip_state.to_dict()}")
        
        summary = self._trip_state.format_summary()
        
        response = f"""
{summary}

Let me check the forecast for your trip dates and show you a preview...

🔍 Fetching surf conditions...
"""
        
        # Trigger forecast preview (this will be expanded in Issue #24)
        preview = await self._generate_forecast_preview()
        if preview:
            response += f"\n{preview}\n\nDoes this look good? Type 'yes' to generate your full itinerary or 'no' to adjust your plans."
            self._trip_state.stage = PlanningStage.AWAITING_CONFIRMATION
        else:
            response += "\nI'm having trouble getting forecast data. Would you like me to try again?"
        
        return response
    
    async def _generate_forecast_preview(self) -> Optional[str]:
        """Generate a condensed forecast preview."""
        if not self._forecast_agent or not self._trip_state.destination:
            return None
        
        try:
            # Get spots for the destination
            spots = self._forecast_agent.find_spots_near(self._trip_state.destination)
            if not spots:
                spots = [self._trip_state.destination]
            
            # Get forecast for first spot
            spot_name = spots[0] if spots else self._trip_state.destination
            days = len(self._trip_state.surf_dates) if self._trip_state.surf_dates else 3
            
            forecast_data = await self._forecast_agent.get_forecast(spot_name, days)
            
            if "error" in forecast_data:
                return None
            
            # Format preview
            preview_lines = [f"📊 Forecast Preview for {spot_name}:"]
            preview_lines.append("-" * 40)
            
            if "daily_summary" in forecast_data:
                for day_info in forecast_data["daily_summary"][:5]:  # Max 5 days
                    preview_lines.append(
                        f"  {day_info.get('date', 'N/A')}: "
                        f"{day_info.get('conditions', 'Check forecast')}"
                    )
            else:
                preview_lines.append("  Forecast data available for your dates.")
            
            return "\n".join(preview_lines)
            
        except Exception as e:
            self.log_error(f"Failed to generate forecast preview: {e}")
            return None
    
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


# Runtime imports for actual usage (after class definition to avoid circular imports)
from app.agents.forecast_integration import ForecastIntegrationAgent
from app.agents.contextual_agent import ContextualAgent
