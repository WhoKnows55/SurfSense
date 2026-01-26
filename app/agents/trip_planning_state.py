"""
SurfSense Trip Planning State

Tracks the state of a guided trip planning conversation.
Manages collection of required information before generating itineraries.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from app.core.logger import LoggerMixin, get_logger

logger = get_logger(__name__)


class TransportMode(str, Enum):
    """Mode of transportation for the trip."""
    CAR = "car"
    PUBLIC_TRANSPORT = "public_transport"


class PlanningStage(str, Enum):
    """Stages of the trip planning flow."""
    IDLE = "idle"                      # Not planning yet
    GATHERING_INFO = "gathering_info"  # Collecting required info
    INFO_COMPLETE = "info_complete"    # All info gathered
    SHOWING_PREVIEW = "showing_preview"  # Showing forecast preview
    AWAITING_CONFIRMATION = "awaiting_confirmation"  # Waiting for user to confirm
    GENERATING_ITINERARY = "generating_itinerary"  # Creating the trip plan
    COMPLETE = "complete"              # Itinerary delivered


class RequiredField(str, Enum):
    """Fields required for trip planning."""
    SKILL_LEVEL = "skill_level"
    DESTINATION = "destination"
    ORIGIN = "origin"
    TRANSPORT_MODE = "transport_mode"
    SURF_DATES = "surf_dates"


# Questions to ask for each missing field
FIELD_QUESTIONS = {
    RequiredField.SKILL_LEVEL: (
        "What's your surfing skill level? "
        "(beginner, intermediate, or advanced)"
    ),
    RequiredField.DESTINATION: (
        "Where would you like to go surfing? "
        "(e.g., 'San Diego', 'North Shore', or a specific spot like 'Pipeline')"
    ),
    RequiredField.ORIGIN: (
        "Where will you be traveling from? "
        "(e.g., 'Los Angeles', 'San Francisco')"
    ),
    RequiredField.TRANSPORT_MODE: (
        "How are you planning to get there - driving or public transport?"
    ),
    RequiredField.SURF_DATES: (
        "When are you planning to surf? "
        "(e.g., 'next weekend', 'January 28-30', 'tomorrow')"
    ),
}

# Follow-up confirmations for each field
FIELD_CONFIRMATIONS = {
    RequiredField.SKILL_LEVEL: "Got it, {value} level! 🏄",
    RequiredField.DESTINATION: "Nice choice! {value} has some great waves. 🌊",
    RequiredField.ORIGIN: "Traveling from {value} - noted! 📍",
    RequiredField.TRANSPORT_MODE: "{value} it is! {extra}",
    RequiredField.SURF_DATES: "Perfect, I'll check conditions for {value}. 📅",
}


@dataclass
class TripPlanningState:
    """
    State tracker for guided trip planning.
    
    Tracks which information has been gathered and manages
    the flow through planning stages.
    """
    
    # Planning stage
    stage: PlanningStage = PlanningStage.IDLE
    
    # Collected information
    skill_level: Optional[str] = None
    destination: Optional[str] = None
    destination_spots: list[str] = field(default_factory=list)  # Resolved spot names
    origin: Optional[str] = None
    origin_coordinates: Optional[tuple[float, float]] = None
    transport_mode: Optional[TransportMode] = None
    surf_dates: list[date] = field(default_factory=list)
    
    # Derived/computed fields
    travel_time_hours: Optional[float] = None
    
    # Flow control
    last_asked_field: Optional[RequiredField] = None
    confirmation_pending: bool = False
    
    # Results
    forecast_preview: Optional[dict] = None
    generated_itinerary: Optional[str] = None
    
    def is_field_complete(self, field: RequiredField) -> bool:
        """Check if a specific field has been filled."""
        if field == RequiredField.SKILL_LEVEL:
            return self.skill_level is not None
        elif field == RequiredField.DESTINATION:
            return self.destination is not None
        elif field == RequiredField.ORIGIN:
            return self.origin is not None
        elif field == RequiredField.TRANSPORT_MODE:
            return self.transport_mode is not None
        elif field == RequiredField.SURF_DATES:
            return len(self.surf_dates) > 0
        return False
    
    def get_missing_fields(self) -> list[RequiredField]:
        """Get list of fields that still need to be collected."""
        missing = []
        for field in RequiredField:
            if not self.is_field_complete(field):
                missing.append(field)
        return missing
    
    def is_info_complete(self) -> bool:
        """Check if all required information has been gathered."""
        return len(self.get_missing_fields()) == 0
    
    def get_next_question(self) -> Optional[tuple[RequiredField, str]]:
        """
        Get the next question to ask the user.
        
        Returns:
            Tuple of (field, question) or None if all complete.
        """
        missing = self.get_missing_fields()
        if not missing:
            return None
        
        # Return first missing field's question
        next_field = missing[0]
        self.last_asked_field = next_field
        return (next_field, FIELD_QUESTIONS[next_field])
    
    def get_confirmation_message(self, field: RequiredField, value: str) -> str:
        """Get a confirmation message for a collected field."""
        template = FIELD_CONFIRMATIONS.get(field, "Got it: {value}")
        
        extra = ""
        if field == RequiredField.TRANSPORT_MODE:
            if value.lower() == "car" or self.transport_mode == TransportMode.CAR:
                extra = "I'll include parking info in your plan."
            else:
                extra = "I'll focus on spots with good public transit access."
        
        return template.format(value=value, extra=extra)
    
    def set_field(self, field: RequiredField, value: Any) -> bool:
        """
        Set a field value.
        
        Returns:
            True if successfully set, False otherwise.
        """
        if field == RequiredField.SKILL_LEVEL:
            if value.lower() in ["beginner", "intermediate", "advanced"]:
                self.skill_level = value.lower()
                return True
        elif field == RequiredField.DESTINATION:
            self.destination = value
            return True
        elif field == RequiredField.ORIGIN:
            self.origin = value
            return True
        elif field == RequiredField.TRANSPORT_MODE:
            value_lower = value.lower()
            if "car" in value_lower or "driv" in value_lower:
                self.transport_mode = TransportMode.CAR
                return True
            elif "public" in value_lower or "transit" in value_lower or "bus" in value_lower or "train" in value_lower:
                self.transport_mode = TransportMode.PUBLIC_TRANSPORT
                return True
        elif field == RequiredField.SURF_DATES:
            # Dates should be set via set_surf_dates method
            return True
        return False
    
    def set_surf_dates(self, dates: list[date]) -> None:
        """Set the surf dates."""
        self.surf_dates = sorted(dates)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for display/logging."""
        return {
            "stage": self.stage.value,
            "skill_level": self.skill_level,
            "destination": self.destination,
            "destination_spots": self.destination_spots,
            "origin": self.origin,
            "transport_mode": self.transport_mode.value if self.transport_mode else None,
            "surf_dates": [d.isoformat() for d in self.surf_dates],
            "travel_time_hours": self.travel_time_hours,
            "is_complete": self.is_info_complete(),
            "missing_fields": [f.value for f in self.get_missing_fields()],
        }
    
    def format_summary(self) -> str:
        """Format a human-readable summary of collected info."""
        lines = ["📋 Trip Planning Info:"]
        
        if self.skill_level:
            lines.append(f"   🏄 Skill Level: {self.skill_level}")
        if self.destination:
            lines.append(f"   📍 Destination: {self.destination}")
        if self.origin:
            lines.append(f"   🏠 From: {self.origin}")
        if self.transport_mode:
            mode = "🚗 Driving" if self.transport_mode == TransportMode.CAR else "🚌 Public Transport"
            lines.append(f"   {mode}")
        if self.surf_dates:
            date_str = ", ".join(d.strftime("%b %d") for d in self.surf_dates)
            lines.append(f"   📅 Dates: {date_str}")
        
        missing = self.get_missing_fields()
        if missing:
            lines.append(f"\n   ⏳ Still need: {', '.join(f.value.replace('_', ' ') for f in missing)}")
        else:
            lines.append("\n   ✅ All info collected!")
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """Reset the planning state."""
        self.stage = PlanningStage.IDLE
        self.skill_level = None
        self.destination = None
        self.destination_spots = []
        self.origin = None
        self.origin_coordinates = None
        self.transport_mode = None
        self.surf_dates = []
        self.travel_time_hours = None
        self.last_asked_field = None
        self.confirmation_pending = False
        self.forecast_preview = None
        self.generated_itinerary = None


class TripInfoExtractor(LoggerMixin):
    """
    Extracts trip planning information from natural language.
    
    Parses user messages to identify skill levels, locations, 
    dates, and transport preferences.
    """
    
    # Keywords for skill level detection
    SKILL_KEYWORDS = {
        "beginner": ["beginner", "newbie", "learning", "first time", "just started", "new to"],
        "intermediate": ["intermediate", "some experience", "comfortable", "been surfing"],
        "advanced": ["advanced", "expert", "experienced", "pro", "years of experience"],
    }
    
    # Keywords for transport mode
    TRANSPORT_KEYWORDS = {
        TransportMode.CAR: ["drive", "driving", "car", "vehicle", "road trip"],
        TransportMode.PUBLIC_TRANSPORT: ["public", "transit", "bus", "train", "metro", "uber", "lyft"],
    }
    
    def extract_skill_level(self, text: str) -> Optional[str]:
        """Extract skill level from text."""
        text_lower = text.lower()
        
        for level, keywords in self.SKILL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return level
        return None
    
    def extract_transport_mode(self, text: str) -> Optional[TransportMode]:
        """Extract transport mode from text."""
        text_lower = text.lower()
        
        for mode, keywords in self.TRANSPORT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return mode
        return None
    
    def extract_dates(self, text: str, reference_date: Optional[date] = None) -> list[date]:
        """
        Extract dates from natural language text.
        
        Handles:
        - "tomorrow", "today"
        - "next weekend", "this weekend"
        - "next Saturday", "next Sunday"
        - "January 28", "Jan 28-30"
        - Date ranges like "28th to 30th"
        
        Args:
            text: The text to parse.
            reference_date: Reference date for relative dates (default: today).
            
        Returns:
            List of extracted dates.
        """
        from datetime import timedelta
        import re
        
        if reference_date is None:
            reference_date = date.today()
        
        text_lower = text.lower()
        dates = []
        
        # Today/tomorrow
        if "today" in text_lower:
            dates.append(reference_date)
        if "tomorrow" in text_lower:
            dates.append(reference_date + timedelta(days=1))
        
        # This/next weekend
        days_until_saturday = (5 - reference_date.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7  # If today is Saturday, get next Saturday
        
        if "this weekend" in text_lower:
            # This weekend = coming Saturday and Sunday
            if reference_date.weekday() < 5:  # Mon-Fri
                saturday = reference_date + timedelta(days=days_until_saturday)
            else:  # Already weekend
                saturday = reference_date if reference_date.weekday() == 5 else reference_date - timedelta(days=1)
            dates.extend([saturday, saturday + timedelta(days=1)])
        
        if "next weekend" in text_lower:
            if reference_date.weekday() >= 5:  # Already weekend
                days_until_saturday = 7 + (5 - reference_date.weekday()) % 7
            saturday = reference_date + timedelta(days=days_until_saturday)
            if reference_date.weekday() < 5:
                saturday = saturday + timedelta(days=7)  # Skip to next week
            dates.extend([saturday, saturday + timedelta(days=1)])
        
        # Next [day of week]
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day_name in enumerate(day_names):
            if f"next {day_name}" in text_lower:
                days_ahead = (i - reference_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                dates.append(reference_date + timedelta(days=days_ahead))
            elif day_name in text_lower and "next" not in text_lower:
                # Just "Saturday" means this coming Saturday
                days_ahead = (i - reference_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                dates.append(reference_date + timedelta(days=days_ahead))
        
        # Month day patterns: "January 28", "Jan 28", "jan 28th"
        month_names = {
            "january": 1, "jan": 1,
            "february": 2, "feb": 2,
            "march": 3, "mar": 3,
            "april": 4, "apr": 4,
            "may": 5,
            "june": 6, "jun": 6,
            "july": 7, "jul": 7,
            "august": 8, "aug": 8,
            "september": 9, "sep": 9, "sept": 9,
            "october": 10, "oct": 10,
            "november": 11, "nov": 11,
            "december": 12, "dec": 12,
        }
        
        for month_name, month_num in month_names.items():
            # Pattern: "jan 28" or "january 28th" or "jan 28-30"
            pattern = rf"{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*[-–to]+\s*(\d{{1,2}})(?:st|nd|rd|th)?)?"
            matches = re.findall(pattern, text_lower)
            for match in matches:
                start_day = int(match[0])
                year = reference_date.year
                # If the date is in the past, assume next year
                try:
                    start_date = date(year, month_num, start_day)
                    if start_date < reference_date:
                        start_date = date(year + 1, month_num, start_day)
                    dates.append(start_date)
                    
                    # Handle range (e.g., "jan 28-30")
                    if match[1]:
                        end_day = int(match[1])
                        current = start_date + timedelta(days=1)
                        end_date = date(start_date.year, month_num, end_day)
                        while current <= end_date:
                            dates.append(current)
                            current += timedelta(days=1)
                except ValueError:
                    pass  # Invalid date
        
        # Remove duplicates and sort
        dates = sorted(set(dates))
        return dates
    
    def extract_all(self, text: str, current_state: TripPlanningState) -> dict[RequiredField, Any]:
        """
        Extract all possible trip info from text.
        
        Args:
            text: User message to parse.
            current_state: Current planning state for context.
            
        Returns:
            Dictionary of extracted field values.
        """
        extracted = {}
        
        # Skill level
        skill = self.extract_skill_level(text)
        if skill:
            extracted[RequiredField.SKILL_LEVEL] = skill
        
        # Transport mode
        transport = self.extract_transport_mode(text)
        if transport:
            extracted[RequiredField.TRANSPORT_MODE] = transport
        
        # Dates
        dates = self.extract_dates(text)
        if dates:
            extracted[RequiredField.SURF_DATES] = dates
        
        # Note: Destination and origin extraction would need 
        # more sophisticated NLP or a location database lookup
        # For now, these are handled by the conversational agent
        
        return extracted
