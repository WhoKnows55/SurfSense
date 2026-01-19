"""
SurfSense Contextual Agent (Layer 2)

Aggregates contextual data providers to enrich surf spot recommendations:
- Parking information
- Accessibility details
- User reviews and ratings
- Safety information

This agent bridges the gap between raw forecast data and practical
trip planning by providing auxiliary information about surf spots.
"""

from typing import Any

from app.agents.base import AgentRole, BaseAgent
from app.contextual import (
    AccessibilityProvider,
    ParkingProvider,
    ReviewsProvider,
    SafetyProvider,
    SpotContext,
)
from app.contextual.base import (
    AccessibilityInfo,
    ParkingInfo,
    ReviewSummary,
    SafetyInfo,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class ContextualAgent(BaseAgent):
    """
    Layer 2: Contextual Data Aggregation Agent
    
    This agent is responsible for:
    - Aggregating data from multiple contextual providers
    - Providing unified SpotContext objects
    - Caching contextual data to reduce repeated lookups
    - Enriching recommendations with practical information
    """
    
    SYSTEM_PROMPT = """You are the Contextual Agent for SurfSense.

Your role is to provide practical, auxiliary information about surf spots:
- Parking: availability, cost, distance to beach
- Accessibility: wheelchair access, beach wheelchairs, paved paths
- Reviews: ratings, highlights, concerns, best skill levels
- Safety: hazards, lifeguards, warnings, recommended skill level

This information helps surfers plan their trips beyond just wave conditions.
Always highlight safety concerns prominently, especially for beginners.
"""

    def __init__(self):
        """Initialize the Contextual Agent with all providers."""
        super().__init__(
            role=AgentRole.CONTEXTUAL,
            name="SurfSense Contextual Agent"
        )
        
        # Initialize all contextual data providers
        self._parking_provider = ParkingProvider()
        self._accessibility_provider = AccessibilityProvider()
        self._reviews_provider = ReviewsProvider()
        self._safety_provider = SafetyProvider()
        
        # Cache for aggregated context: {spot_name: SpotContext}
        self._context_cache: dict[str, SpotContext] = {}
        
        # Register tools
        self._register_default_tools()
        
        self.log_info("Contextual Agent initialized with all providers")
    
    def _register_default_tools(self) -> None:
        """Register contextual data tools."""
        self.register_tool(
            "get_spot_context",
            self._tool_get_spot_context,
            "Get complete contextual information for a surf spot"
        )
        self.register_tool(
            "get_parking_info",
            self._tool_get_parking_info,
            "Get parking information for a surf spot"
        )
        self.register_tool(
            "get_safety_info",
            self._tool_get_safety_info,
            "Get safety information for a surf spot"
        )
        self.register_tool(
            "get_accessibility_info",
            self._tool_get_accessibility_info,
            "Get accessibility information for a surf spot"
        )
        self.register_tool(
            "get_reviews",
            self._tool_get_reviews,
            "Get review summary for a surf spot"
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return self.SYSTEM_PROMPT
    
    async def process(self, user_input: str) -> str:
        """
        Process a contextual data query.
        
        Args:
            user_input: Query about contextual information.
            
        Returns:
            Contextual information or analysis.
        """
        self.state.add_message("user", user_input)
        
        response = (
            "Contextual Agent received your request. "
            "Use get_spot_context() for complete spot information."
        )
        
        self.state.add_message("assistant", response)
        return response
    
    async def get_spot_context(self, spot_name: str) -> SpotContext:
        """
        Get complete contextual information for a surf spot.
        
        Aggregates data from all providers into a single SpotContext.
        Results are cached for efficiency.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            SpotContext with all available contextual data.
        """
        # Check cache first
        if spot_name in self._context_cache:
            self.log_debug(f"Cache hit for context: {spot_name}")
            return self._context_cache[spot_name]
        
        self.log_info(f"Fetching context for: {spot_name}")
        
        # Fetch from all providers in parallel (conceptually)
        parking = await self._parking_provider.get_data(spot_name)
        accessibility = await self._accessibility_provider.get_data(spot_name)
        reviews = await self._reviews_provider.get_data(spot_name)
        safety = await self._safety_provider.get_data(spot_name)
        
        # Build unified context
        context = SpotContext(
            spot_name=spot_name,
            parking=parking,
            accessibility=accessibility,
            reviews=reviews,
            safety=safety,
        )
        
        # Cache for future requests
        self._context_cache[spot_name] = context
        
        return context
    
    async def _tool_get_spot_context(self, spot_name: str) -> dict[str, Any]:
        """
        Tool: Get complete contextual information.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Dictionary with all contextual data.
        """
        context = await self.get_spot_context(spot_name)
        return self.context_to_dict(context)
    
    async def _tool_get_parking_info(self, spot_name: str) -> dict[str, Any]:
        """
        Tool: Get parking information only.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Parking information dictionary.
        """
        parking = await self._parking_provider.get_data(spot_name)
        return self.parking_to_dict(parking)
    
    async def _tool_get_safety_info(self, spot_name: str) -> dict[str, Any]:
        """
        Tool: Get safety information only.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Safety information dictionary.
        """
        safety = await self._safety_provider.get_data(spot_name)
        return self.safety_to_dict(safety)
    
    async def _tool_get_accessibility_info(self, spot_name: str) -> dict[str, Any]:
        """
        Tool: Get accessibility information only.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Accessibility information dictionary.
        """
        accessibility = await self._accessibility_provider.get_data(spot_name)
        return self.accessibility_to_dict(accessibility)
    
    async def _tool_get_reviews(self, spot_name: str) -> dict[str, Any]:
        """
        Tool: Get review summary only.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Review summary dictionary.
        """
        reviews = await self._reviews_provider.get_data(spot_name)
        return self.reviews_to_dict(reviews)
    
    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._context_cache.clear()
        self.log_info("Context cache cleared")
    
    # -------------------------------------------------------------------------
    # Serialization helpers
    # -------------------------------------------------------------------------
    
    @staticmethod
    def parking_to_dict(parking: ParkingInfo) -> dict[str, Any]:
        """Convert ParkingInfo to a dictionary."""
        return {
            "type": parking.parking_type.value,
            "capacity": parking.capacity,
            "cost_per_hour": parking.cost_per_hour,
            "max_stay_hours": parking.max_stay_hours,
            "distance_to_beach_m": parking.distance_to_beach_m,
            "notes": parking.notes,
            "confidence": parking.confidence.value,
        }
    
    @staticmethod
    def accessibility_to_dict(accessibility: AccessibilityInfo) -> dict[str, Any]:
        """Convert AccessibilityInfo to a dictionary."""
        return {
            "level": accessibility.level.value,
            "wheelchair_access": accessibility.wheelchair_access,
            "beach_wheelchair_available": accessibility.beach_wheelchair_available,
            "paved_path": accessibility.paved_path,
            "accessible_facilities": accessibility.accessible_facilities,
            "notes": accessibility.notes,
            "confidence": accessibility.confidence.value,
        }
    
    @staticmethod
    def reviews_to_dict(reviews: ReviewSummary) -> dict[str, Any]:
        """Convert ReviewSummary to a dictionary."""
        return {
            "average_rating": reviews.average_rating,
            "total_reviews": reviews.total_reviews,
            "recent_reviews": reviews.recent_reviews,
            "highlights": reviews.highlights,
            "concerns": reviews.concerns,
            "best_for": reviews.best_for,
            "confidence": reviews.confidence.value,
        }
    
    @staticmethod
    def safety_to_dict(safety: SafetyInfo) -> dict[str, Any]:
        """Convert SafetyInfo to a dictionary."""
        return {
            "hazards": [h.value for h in safety.hazards],
            "lifeguard_on_duty": safety.lifeguard_on_duty,
            "lifeguard_hours": safety.lifeguard_hours,
            "emergency_access": safety.emergency_access,
            "recommended_skill_level": safety.recommended_skill_level,
            "warnings": safety.warnings,
            "notes": safety.notes,
            "confidence": safety.confidence.value,
        }
    
    def context_to_dict(self, context: SpotContext) -> dict[str, Any]:
        """Convert SpotContext to a complete dictionary."""
        return {
            "spot_name": context.spot_name,
            "parking": self.parking_to_dict(context.parking),
            "accessibility": self.accessibility_to_dict(context.accessibility),
            "reviews": self.reviews_to_dict(context.reviews),
            "safety": self.safety_to_dict(context.safety),
            "last_updated": context.last_updated.isoformat(),
            "summary": context.summary(),
        }
    
    def format_context_for_display(self, context: SpotContext) -> str:
        """
        Format SpotContext for human-readable display.
        
        Args:
            context: The SpotContext to format.
            
        Returns:
            Formatted string for terminal display.
        """
        lines = [
            f"📍 Contextual Information for {context.spot_name}",
            "=" * 50,
        ]
        
        # Parking
        lines.append("\n🅿️  Parking:")
        lines.append(f"   Type: {context.parking.parking_type.value.replace('_', ' ').title()}")
        if context.parking.capacity:
            lines.append(f"   Capacity: ~{context.parking.capacity} spots")
        if context.parking.cost_per_hour:
            lines.append(f"   Cost: ${context.parking.cost_per_hour:.2f}/hour")
        if context.parking.distance_to_beach_m:
            lines.append(f"   Distance: {context.parking.distance_to_beach_m}m to beach")
        if context.parking.notes:
            lines.append(f"   Notes: {context.parking.notes}")
        
        # Accessibility
        lines.append("\n♿ Accessibility:")
        lines.append(f"   Level: {context.accessibility.level.value.replace('_', ' ').title()}")
        if context.accessibility.wheelchair_access:
            lines.append("   ✓ Wheelchair access to beach")
        if context.accessibility.beach_wheelchair_available:
            lines.append("   ✓ Beach wheelchairs available")
        if context.accessibility.paved_path:
            lines.append("   ✓ Paved path to beach")
        if context.accessibility.accessible_facilities:
            lines.append("   ✓ Accessible restrooms/showers")
        if context.accessibility.notes:
            lines.append(f"   Notes: {context.accessibility.notes}")
        
        # Reviews
        lines.append("\n⭐ Reviews:")
        if context.reviews.average_rating:
            lines.append(
                f"   Rating: {context.reviews.average_rating:.1f}/5 "
                f"({context.reviews.total_reviews} reviews)"
            )
        if context.reviews.highlights:
            lines.append(f"   Highlights: {', '.join(context.reviews.highlights[:3])}")
        if context.reviews.concerns:
            lines.append(f"   Concerns: {', '.join(context.reviews.concerns[:3])}")
        if context.reviews.best_for:
            lines.append(f"   Best for: {', '.join(context.reviews.best_for)}")
        
        # Safety (important - highlight prominently)
        lines.append("\n⚠️  Safety:")
        if context.safety.recommended_skill_level:
            lines.append(f"   Recommended skill: {context.safety.recommended_skill_level.upper()}")
        if context.safety.hazards:
            hazard_list = ", ".join(h.value.replace("_", " ").title() for h in context.safety.hazards)
            lines.append(f"   Hazards: {hazard_list}")
        if context.safety.lifeguard_on_duty is not None:
            status = "Yes" if context.safety.lifeguard_on_duty else "No"
            lines.append(f"   Lifeguard: {status}")
            if context.safety.lifeguard_hours:
                lines.append(f"   Hours: {context.safety.lifeguard_hours}")
        if context.safety.warnings:
            lines.append("   Warnings:")
            for warning in context.safety.warnings:
                lines.append(f"     • {warning}")
        if context.safety.notes:
            lines.append(f"   Notes: {context.safety.notes}")
        
        return "\n".join(lines)
