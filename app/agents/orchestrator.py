"""
SurfSense Orchestrator

LLM-powered orchestrator that manages dialogue and delegates tasks to
three deterministic sub-agents through OpenAI function-calling.

This is the only component that calls the LLM directly.
"""

import json

from app.agents.condition_agent import ConditionAssessmentAgent
from app.agents.forecast_data_agent import ForecastDataAgent
from app.agents.trip_planning_agent import TripPlanningAgent
from app.core.llm_service import AzureOpenAIProvider
from app.core.logger import LoggerMixin, get_logger

logger = get_logger(__name__)


class Orchestrator(LoggerMixin):
    """LLM-powered orchestrator that delegates to deterministic sub-agents.

    Workflow:
    1. Maintains conversation history as an OpenAI message list.
    2. Collects all tool definitions from the three sub-agents.
    3. Calls Azure OpenAI with function-calling enabled.
    4. When the model returns a tool call, dispatches to the appropriate sub-agent.
    5. Feeds tool results back into the conversation and re-calls the model.
    6. Repeats until the model returns a text response.
    """

    SYSTEM_PROMPT = """You are SurfSense, an AI surf trip planning assistant.

You help surfers plan trips by having a natural conversation to understand their needs,
then using your tools to fetch data, evaluate conditions, and build itineraries.

WORKFLOW:
1. Greet the user and ask about their trip: dates, location preferences, skill level, group size.
2. Once you have enough info, call fetch_forecast for candidate spots.
3. Call assess_conditions to evaluate each spot for the user's skill level.
4. Call check_safety if any spots have concerning conditions.
5. Call find_surf_windows to identify the best times.
6. For multi-day trips, call plan_itinerary to optimise the schedule.
7. Present results in a clear, enthusiastic but safety-conscious manner.

RULES:
- Always ask for skill level before making recommendations.
- Never recommend spots rated "unsafe" for the user's level without explicit warnings.
- Be concise. Present key info first, details on request.
- If a tool call fails, explain the issue and suggest alternatives.
"""

    MAX_TOOL_ROUNDS = 10

    def __init__(self, llm_provider: AzureOpenAIProvider, settings):
        self._llm = llm_provider
        self._forecast_agent = ForecastDataAgent(settings)
        self._condition_agent = ConditionAssessmentAgent(settings)
        self._trip_agent = TripPlanningAgent()

        # Conversation history (OpenAI message format)
        self._messages: list[dict] = [
            {"role": "system", "content": self.SYSTEM_PROMPT}
        ]

        # Tool dispatch table: tool_name -> (agent, method_name)
        self._tool_dispatch = {
            "fetch_forecast": (self._forecast_agent, "fetch_forecast"),
            "fetch_contextual_info": (self._forecast_agent, "fetch_contextual_info"),
            "get_spot_metadata": (self._forecast_agent, "get_spot_metadata"),
            "assess_conditions": (self._condition_agent, "assess_conditions"),
            "check_safety": (self._condition_agent, "check_safety"),
            "get_skill_thresholds": (self._condition_agent, "get_skill_thresholds"),
            "find_surf_windows": (self._trip_agent, "find_surf_windows"),
            "plan_itinerary": (self._trip_agent, "plan_itinerary"),
            "rank_spots": (self._trip_agent, "rank_spots"),
        }

        # Collect all tool definitions
        self._tools = (
            ForecastDataAgent.get_tool_definitions()
            + ConditionAssessmentAgent.get_tool_definitions()
            + TripPlanningAgent.get_tool_definitions()
        )

        # Session data store for cross-tool dependencies
        self._session_data: dict[str, dict] = {}

    async def process(self, user_input: str) -> str:
        """Process user input through the orchestrator loop.

        1. Append user message to history.
        2. Call Azure OpenAI with tools.
        3. If model returns tool_calls, execute them and feed results back.
        4. Repeat until model returns a text response.
        5. Return the text response.
        """
        self._messages.append({"role": "user", "content": user_input})

        for _ in range(self.MAX_TOOL_ROUNDS):
            response = self._llm.chat_with_tools(self._messages, self._tools)
            message = response.choices[0].message

            # If no tool calls, we have a final text response
            if not message.tool_calls:
                content = message.content or ""
                self._messages.append({"role": "assistant", "content": content})
                return content

            # Process tool calls - append the assistant message with tool_calls
            self._messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                result = await self._execute_tool(tool_name, tool_args)

                self._messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

        return (
            "I've gathered the data but need to simplify my analysis. "
            "Let me summarise what I found..."
        )

    async def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """Dispatch a tool call to the appropriate sub-agent."""
        if tool_name not in self._tool_dispatch:
            return {"error": f"Unknown tool: {tool_name}"}

        agent, method_name = self._tool_dispatch[tool_name]
        method = getattr(agent, method_name)

        try:
            enriched_args = self._enrich_args(tool_name, args)

            result = method(**enriched_args)
            # Handle async methods
            if hasattr(result, "__await__"):
                result = await result

            self._cache_result(tool_name, args, result)
            return result

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return {"error": str(e)}

    def _enrich_args(self, tool_name: str, args: dict) -> dict:
        """Inject cached session data into tool arguments where needed."""
        if tool_name == "assess_conditions":
            spot = args.get("spot_name", "")
            if spot in self._session_data and "forecast" in self._session_data[spot]:
                args["forecast_data"] = self._session_data[spot]["forecast"]
        elif tool_name == "check_safety":
            spot = args.get("spot_name", "")
            if spot in self._session_data:
                if "forecast" in self._session_data[spot]:
                    args["forecast_data"] = self._session_data[spot]["forecast"]
                if "contextual" in self._session_data[spot]:
                    args["safety_info"] = self._session_data[spot][
                        "contextual"
                    ].get("safety", {})
        elif tool_name == "find_surf_windows":
            spot = args.get("spot_name", "")
            if (
                spot in self._session_data
                and "assessments" in self._session_data[spot]
            ):
                args["assessments"] = self._session_data[spot]["assessments"]
        elif tool_name == "plan_itinerary":
            spots_data = {}
            for spot_name in args.get("spot_names", []):
                if spot_name in self._session_data:
                    spots_data[spot_name] = self._session_data[spot_name]
            args["spots_data"] = spots_data
        elif tool_name == "rank_spots":
            spot_assessments = {}
            for spot_name in args.get("spot_names", []):
                if (
                    spot_name in self._session_data
                    and "assessments" in self._session_data[spot_name]
                ):
                    spot_assessments[spot_name] = self._session_data[
                        spot_name
                    ]["assessments"]
            args["spot_assessments"] = spot_assessments
        return args

    def _cache_result(self, tool_name: str, args: dict, result) -> None:
        """Store tool results in session cache for cross-tool dependencies."""
        spot = args.get("spot_name", "")
        if not spot:
            return

        if spot not in self._session_data:
            self._session_data[spot] = {}

        if tool_name == "fetch_forecast":
            self._session_data[spot]["forecast"] = result
            if isinstance(result, dict) and "coordinates" in result:
                self._session_data[spot]["coordinates"] = result["coordinates"]
        elif tool_name == "fetch_contextual_info":
            self._session_data[spot]["contextual"] = result
        elif tool_name == "assess_conditions":
            self._session_data[spot]["assessments"] = result
        elif tool_name == "find_surf_windows":
            self._session_data[spot]["windows"] = result

    def reset(self) -> None:
        """Reset conversation and session data."""
        self._messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        self._session_data = {}
