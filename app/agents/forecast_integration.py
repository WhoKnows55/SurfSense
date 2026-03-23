"""
SurfSense Forecast Integration Agent (Layer 3)

Responsible for integrating forecast APIs:
- Fetches data from Stormglass API (primary, requires API key)
- Enriches/fallbacks with Open-Meteo (free, global coverage)
- Normalizes data to unified forecast models
- Provides forecast analysis and recommendations
- Caches and manages forecast data
- Assesses conditions for different skill levels
"""

from datetime import datetime, timedelta
from typing import Any, Optional
import traceback

from app.agents.base import AgentRole, BaseAgent
from app.core.logger import get_logger
from app.forecasting.models import (
    Coordinates,
    DataSource,
    ForecastPoint,
    ForecastResponse,
    SpotMetadata,
)
from app.forecasting.stormglass_client import StormglassClient, StormglassAPIError
from app.forecasting.openmeteo_client import OpenMeteoClient
from app.knowledge import get_spot_database
from app.planning.condition_assessor import ConditionAssessor, ConditionRating
from app.planning.window_finder import SurfWindowFinder, WindowFinderResult
from app.planning.trip_planner import TripPlanner, TripItinerary

logger = get_logger(__name__)


class ForecastDebugInfo:
    """Encapsulates debugging information for forecast failures."""
    
    def __init__(self, spot_name: str):
        self.spot_name = spot_name
        self.errors: list[dict[str, Any]] = []
        self.resolution_steps: list[str] = []
        
    def add_resolution_step(self, step: str) -> None:
        """Log a spot resolution attempt."""
        self.resolution_steps.append(step)
        logger.debug(f"Spot resolution step: {step}", spot=self.spot_name)
    
    def add_error(self, stage: str, error: Exception, details: Optional[dict] = None) -> None:
        """Record an error during the forecast process."""
        error_info = {
            "stage": stage,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        if details:
            error_info["details"] = details
        self.errors.append(error_info)
        logger.debug(f"Forecast error at {stage}: {error}", spot=self.spot_name, **error_info)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert debug info to dictionary for response."""
        return {
            "spot_name": self.spot_name,
            "resolution_steps": self.resolution_steps,
            "errors": self.errors,
            "error_count": len(self.errors),
        }


# Known surf spots with coordinates
KNOWN_SPOTS: dict[str, Coordinates] = {
    "pipeline": Coordinates(latitude=21.6650, longitude=-158.0539),
    "sunset beach": Coordinates(latitude=21.6789, longitude=-158.0417),
    "waikiki": Coordinates(latitude=21.2766, longitude=-157.8278),
    "mavericks": Coordinates(latitude=37.4950, longitude=-122.4967),
    "huntington beach": Coordinates(latitude=33.6553, longitude=-117.9992),
    "san onofre": Coordinates(latitude=33.3753, longitude=-117.5689),
    "trestles": Coordinates(latitude=33.3817, longitude=-117.5886),
    "rincon": Coordinates(latitude=34.3742, longitude=-119.4761),
    "teahupoo": Coordinates(latitude=-17.8368, longitude=-149.2584),
    "nazare": Coordinates(latitude=39.6025, longitude=-9.0706),
    "hossegor": Coordinates(latitude=43.6676, longitude=-1.4412),
    "jeffreys bay": Coordinates(latitude=-34.0407, longitude=24.9309),
    "uluwatu": Coordinates(latitude=-8.8294, longitude=115.0853),
    "bells beach": Coordinates(latitude=-38.3714, longitude=144.2803),
    "gold coast": Coordinates(latitude=-28.0167, longitude=153.4000),
}


class ForecastIntegrationAgent(BaseAgent):
    """
    Layer 3: Forecasting Component Integration
    
    This agent is responsible for:
    - Integrating with forecast APIs (Stormglass, NOAA, etc.)
    - Normalizing forecast data to unified models
    - Analyzing conditions for surf quality
    - Caching forecast data to reduce API calls
    """
    
    SYSTEM_PROMPT = """You are the Forecast Integration Agent for SurfSense.

Your role is to:
1. Fetch and process surf forecast data from APIs
2. Analyze wave, swell, wind, and tide conditions
3. Determine optimal surfing windows
4. Provide condition assessments for different skill levels

You have access to:
- Wave height, period, and direction data
- Swell information (height, period, direction)
- Wind speed, gusts, and direction
- Tide heights and states
- Weather conditions

When analyzing conditions, consider:
- Larger swells with longer periods = better waves
- Offshore or light winds = cleaner conditions
- Rising tide often brings better waves
- Skill level requirements for different conditions
"""

    def __init__(self):
        """Initialize the Forecast Integration Agent."""
        super().__init__(
            role=AgentRole.FORECAST_INTEGRATION,
            name="SurfSense Forecast Integration Agent"
        )
        
        # Forecast cache: {spot_name: {date: ForecastResponse}}
        self._cache: dict[str, dict[str, ForecastResponse]] = {}
        self._cache_ttl = timedelta(hours=1)
        
        # Initialize API clients
        # Primary: Stormglass (requires API key, better wave data)
        self._stormglass_client = StormglassClient()
        
        # Secondary: Open-Meteo (FREE, global coverage, enriches data)
        self._openmeteo_client = OpenMeteoClient()
        
        # Condition assessor for skill-based analysis
        self._condition_assessor = ConditionAssessor()
        
        # Window finder for identifying optimal surf times
        self._window_finder = SurfWindowFinder(self._condition_assessor)
        
        # Trip planner for multi-day itineraries
        self._trip_planner = TripPlanner(self._condition_assessor, self._window_finder)
        
        if not self._stormglass_client.is_configured:
            self.log_warning(
                "Stormglass API key not configured. "
                "Using Open-Meteo as primary source (free, global coverage). "
                "Set FORECAST_API_KEY in .env for premium Stormglass data."
            )
        
        # Initialize spot database for coordinate lookups
        self._spot_db = get_spot_database()
        
        # Register tools
        self._register_default_tools()
    
    def _get_spot_coordinates(self, spot_name: str) -> Optional[Coordinates]:
        """
        Look up coordinates for a known surf spot.
        
        First checks the comprehensive spot database, then falls back
        to the legacy KNOWN_SPOTS dictionary for basic spots.
        
        Args:
            spot_name: Name of the surf spot.
            
        Returns:
            Coordinates if found, None otherwise.
        """
        # Try the spot database first
        coords = self._spot_db.get_coordinates(spot_name)
        if coords:
            return Coordinates(latitude=coords[0], longitude=coords[1])
        
        # Fallback to legacy KNOWN_SPOTS
        normalized = spot_name.lower().strip()
        return KNOWN_SPOTS.get(normalized)
    
    def get_spot_info(self, spot_name: str) -> Optional[dict[str, Any]]:
        """
        Get comprehensive information about a surf spot.
        
        Args:
            spot_name: Name of the spot.
            
        Returns:
            Spot information dictionary, or None if not found.
        """
        spot = self._spot_db.get_spot(spot_name.lower())
        if not spot:
            matches = self._spot_db.search_by_name(spot_name)
            if matches:
                spot = matches[0]
        
        if spot:
            return self._spot_db.to_dict(spot)
        return None
    
    def get_all_spots(self) -> list[str]:
        """
        Get list of all known spot names.
        
        Returns:
            List of all spot names from the database and KNOWN_SPOTS.
        """
        # Get spots from database
        db_spots = list(self._spot_db._spots.keys())
        
        # Add spots from KNOWN_SPOTS that aren't already in db
        for spot_name in KNOWN_SPOTS.keys():
            if spot_name.lower() not in [s.lower() for s in db_spots]:
                db_spots.append(spot_name)
        
        return db_spots
    
    def find_spots_near(self, location: str, max_results: int = 5) -> list[str]:
        """
        Find surf spots near a given location.
        
        Args:
            location: Location name or spot name to search near.
            max_results: Maximum number of results to return.
            
        Returns:
            List of spot names near the location.
        """
        # First try direct search in spot database
        matches = self._spot_db.search_by_name(location)
        if matches:
            return [m.name for m in matches[:max_results]]
        
        # Try to find by region
        matches = self._spot_db.search_by_region(location)
        if matches:
            return [m.name for m in matches[:max_results]]
        
        # Check KNOWN_SPOTS as fallback
        location_lower = location.lower()
        known_matches = [
            name for name in KNOWN_SPOTS.keys()
            if location_lower in name.lower()
        ]
        if known_matches:
            return known_matches[:max_results]
        
        # Return empty list if nothing found
        return []
    
    def _register_default_tools(self) -> None:
        """Register forecast-related tools."""
        self.register_tool(
            "fetch_forecast",
            self._tool_fetch_forecast,
            "Fetch raw forecast data from API"
        )
        self.register_tool(
            "analyze_conditions",
            self._tool_analyze_conditions,
            "Analyze forecast for surfing quality"
        )
        self.register_tool(
            "find_best_window",
            self._tool_find_best_window,
            "Find the best surfing window in a forecast"
        )
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return self.SYSTEM_PROMPT
    
    async def process(self, user_input: str) -> str:
        """
        Process a forecast-related query.
        
        Args:
            user_input: Query about forecasts.
            
        Returns:
            Forecast information or analysis.
        """
        self.state.add_message("user", user_input)
        
        # Parse the request and determine action
        # For now, return a placeholder
        response = (
            "Forecast Integration Agent received your request. "
            "Full API integration is pending implementation."
        )
        
        self.state.add_message("assistant", response)
        return response
    
    async def get_forecast(
        self,
        spot_name: str,
        days: int = 3,
        coordinates: Optional[Coordinates] = None
    ) -> dict[str, Any]:
        """
        Get forecast for a surf spot.
        
        This is the main method called by other agents.
        
        Args:
            spot_name: Name of the surf spot.
            days: Number of days to forecast.
            coordinates: Optional coordinates (if known).
            
        Returns:
            Forecast data dictionary.
        """
        self.log_info(f"Getting forecast for {spot_name}, {days} days")
        debug_info = ForecastDebugInfo(spot_name)
        
        # Check cache first
        cached = self._get_cached_forecast(spot_name)
        if cached:
            self.log_debug("Returning cached forecast")
            return self._forecast_to_dict(cached)
        
        # Fetch from API
        try:
            forecast = await self._fetch_from_api(spot_name, days, coordinates, debug_info)
            
            # Cache the result
            self._cache_forecast(spot_name, forecast)
            
            return self._forecast_to_dict(forecast)
            
        except Exception as e:
            self.log_error(f"Failed to fetch forecast: {e}", **debug_info.to_dict())
            return {
                "error": str(e),
                "spot": spot_name,
                "message": "Unable to fetch forecast data",
                "debug": debug_info.to_dict(),
                "recovery_suggestion": self._suggest_recovery(debug_info, e),
            }
    
    async def _fetch_from_api(
        self,
        spot_name: str,
        days: int,
        coordinates: Optional[Coordinates],
        debug_info: ForecastDebugInfo
    ) -> ForecastResponse:
        """
        Fetch forecast from available API services.
        
        Priority:
        1. Stormglass (if API key configured) - Premium wave data
        2. Open-Meteo (always available) - Free, global coverage
        
        Raises:
            ValueError: If coordinates unknown.
            Exception: If all API requests fail.
        """
        # Try to get coordinates for known spots
        if coordinates is None:
            debug_info.add_resolution_step("Resolving spot coordinates from database")
            coordinates = self._get_spot_coordinates(spot_name)
        else:
            debug_info.add_resolution_step("Using provided coordinates")
        
        if not coordinates:
            # Provide detailed debug info about what we tried
            available_spots = list(KNOWN_SPOTS.keys())[:5]
            error_detail = {
                "spot_requested": spot_name,
                "available_spots_sample": available_spots,
                "total_known_spots": len(KNOWN_SPOTS),
                "database_spots_count": self._spot_db.spot_count,
            }
            debug_info.add_error(
                "spot_resolution",
                ValueError(f"Unknown spot: '{spot_name}'"),
                error_detail
            )
            raise ValueError(
                f"Unknown spot: '{spot_name}'. "
                "Please provide coordinates or use a known spot name. "
                f"Available example spots: {', '.join(available_spots)}"
            )
        
        lat = coordinates.latitude
        lon = coordinates.longitude
        debug_info.add_resolution_step(f"Resolved to coordinates: {lat}, {lon}")
        
        # Try Stormglass first if configured
        if self._stormglass_client.is_configured:
            try:
                debug_info.add_resolution_step("Attempting Stormglass API fetch")
                self.log_info(
                    f"Fetching forecast from Stormglass for {spot_name}",
                    lat=lat,
                    lon=lon
                )
                result = await self._stormglass_client.get_forecast(
                    latitude=lat,
                    longitude=lon,
                    spot_name=spot_name,
                    days=days,
                )
                debug_info.add_resolution_step("Stormglass API succeeded")
                return result
            except StormglassAPIError as e:
                debug_info.add_error("stormglass_api", e, {"attempt": "primary"})
                self.log_warning(
                    f"Stormglass failed: {e}. Falling back to Open-Meteo."
                )
        
        # Fallback/primary: Open-Meteo (free, always available)
        try:
            debug_info.add_resolution_step("Attempting Open-Meteo API fetch")
            self.log_info(
                f"Fetching forecast from Open-Meteo for {spot_name}",
                lat=lat,
                lon=lon
            )
            result = await self._openmeteo_client.get_forecast(
                latitude=lat,
                longitude=lon,
                spot_name=spot_name,
                days=days,
            )
            debug_info.add_resolution_step("Open-Meteo API succeeded")
            return result
        except Exception as e:
            debug_info.add_error("openmeteo_api", e, {"attempt": "fallback"})
            raise
    
    def _suggest_recovery(self, debug_info: ForecastDebugInfo, error: Exception) -> str:
        """
        Provide a helpful recovery suggestion based on the error.
        
        Args:
            debug_info: Debug information collected during the attempt.
            error: The exception that occurred.
            
        Returns:
            A human-readable suggestion for recovery.
        """
        if not debug_info.errors:
            return "Unknown error occurred. Check logs for details."
        
        last_error = debug_info.errors[-1]
        error_stage = last_error["stage"]
        error_type = last_error["error_type"]
        
        suggestions = {
            "spot_resolution": (
                f"The spot '{debug_info.spot_name}' is not recognized. "
                f"Try providing coordinates (latitude, longitude) or using a known spot name. "
                f"Check available spots in the database."
            ),
            "stormglass_api": (
                "The Stormglass API encountered an issue. "
                "This could be a temporary service outage. Try again in a moment, "
                "or the system will automatically use the free Open-Meteo service."
            ),
            "openmeteo_api": (
                "Both forecast APIs are currently unavailable. "
                "Please check your internet connection and try again."
            ),
        }
        
        return suggestions.get(error_stage, str(error))
    
    def _get_cached_forecast(
        self,
        spot_name: str
    ) -> Optional[ForecastResponse]:
        """Get forecast from cache if still valid."""
        if spot_name not in self._cache:
            return None
        
        spot_cache = self._cache[spot_name]
        today = datetime.utcnow().date().isoformat()
        
        if today not in spot_cache:
            return None
        
        cached = spot_cache[today]
        age = datetime.utcnow() - cached.fetched_at
        
        if age > self._cache_ttl:
            return None
        
        return cached
    
    def _cache_forecast(
        self,
        spot_name: str,
        forecast: ForecastResponse
    ) -> None:
        """Cache a forecast response."""
        if spot_name not in self._cache:
            self._cache[spot_name] = {}
        
        today = datetime.utcnow().date().isoformat()
        self._cache[spot_name][today] = forecast
    
    def _forecast_to_dict(self, forecast: ForecastResponse) -> dict[str, Any]:
        """Convert ForecastResponse to dictionary for API/agent use."""
        return {
            "spot": forecast.spot.name,
            "coordinates": {
                "lat": forecast.spot.coordinates.latitude,
                "lon": forecast.spot.coordinates.longitude
            },
            "source": forecast.source.value,
            "fetched_at": forecast.fetched_at.isoformat(),
            "forecast_count": len(forecast.forecasts),
            "forecasts": [
                {
                    "timestamp": f.timestamp.isoformat(),
                    "summary": f.summary(),
                    "waves": {
                        "min_m": f.waves.height_min,
                        "max_m": f.waves.height_max,
                        "avg_m": f.waves.height_avg
                    },
                    "swell": {
                        "height_m": f.swell.height,
                        "period_s": f.swell.period,
                        "direction": f.swell.direction.value if f.swell.direction else None
                    },
                    "wind": {
                        "speed_kph": f.wind.speed,
                        "direction": f.wind.direction.value if f.wind.direction else None,
                        "is_offshore": f.is_offshore_wind,
                        "is_light": f.is_light_wind
                    }
                }
                for f in forecast.forecasts
            ]
        }
    
    async def _tool_fetch_forecast(
        self,
        spot_name: str,
        days: int = 3
    ) -> dict[str, Any]:
        """Tool: Fetch forecast data."""
        return await self.get_forecast(spot_name, days)
    
    async def _tool_analyze_conditions(
        self,
        forecast_data: dict[str, Any],
        skill_level: str = "intermediate"
    ) -> dict[str, Any]:
        """
        Tool: Analyze forecast conditions for surfing quality.
        
        Uses the ConditionAssessor for skill-based evaluation.
        
        Args:
            forecast_data: Forecast data dictionary.
            skill_level: User's skill level.
            
        Returns:
            Analysis with quality ratings and recommendations.
        """
        if "forecasts" not in forecast_data or not forecast_data["forecasts"]:
            return {
                "error": "No forecast data available",
                "skill_level": skill_level,
            }
        
        # We need ForecastPoint objects for the assessor
        # For now, use the cached response if available
        spot_name = forecast_data.get("spot", "Unknown")
        cached = self._get_cached_forecast(spot_name)
        
        if cached and cached.forecasts:
            # Use actual ForecastPoint objects
            daily_summary = self._condition_assessor.get_daily_summary(
                cached.forecasts,
                skill_level
            )
            
            # Find best conditions
            best_conditions = self._condition_assessor.find_best_conditions(
                cached.forecasts,
                skill_level,
                min_rating=ConditionRating.SUITABLE
            )
            
            return {
                "spot": spot_name,
                "skill_level": skill_level,
                "summary": daily_summary,
                "best_windows": [
                    a.to_dict() for a in best_conditions[:5]
                ],
                "recommendation": daily_summary.get("recommendation", ""),
            }
        
        # Fallback: simple analysis from dict data
        return self._simple_analyze(forecast_data, skill_level)
    
    def _simple_analyze(
        self,
        forecast_data: dict[str, Any],
        skill_level: str
    ) -> dict[str, Any]:
        """Simple analysis when ForecastPoint objects aren't available."""
        analysis = {
            "skill_level": skill_level,
            "overall_rating": "Unknown",
            "best_times": [],
            "warnings": [],
            "recommendations": []
        }
        
        for fc in forecast_data.get("forecasts", []):
            wind = fc.get("wind", {})
            waves = fc.get("waves", {})
            
            # Rate based on wind and waves
            if wind.get("is_light") and wind.get("is_offshore"):
                analysis["best_times"].append({
                    "timestamp": fc["timestamp"],
                    "rating": "Excellent",
                    "reason": "Light offshore winds"
                })
            elif wind.get("is_light"):
                analysis["best_times"].append({
                    "timestamp": fc["timestamp"],
                    "rating": "Good",
                    "reason": "Light winds"
                })
        
        # Skill-based warnings
        max_wave = {"beginner": 1.5, "intermediate": 2.5, "advanced": 5.0}
        limit = max_wave.get(skill_level, 2.5)
        
        for fc in forecast_data.get("forecasts", []):
            waves = fc.get("waves", {})
            if waves.get("max_m", 0) > limit:
                analysis["warnings"].append(
                    f"Wave height ({waves.get('max_m')}m) exceeds {skill_level} limit at {fc['timestamp']}"
                )
        
        return analysis
    
    async def assess_conditions(
        self,
        spot_name: str,
        skill_level: str = "intermediate",
        days: int = 1,
    ) -> dict[str, Any]:
        """
        Get forecast and assess conditions for a skill level.
        
        This is the main method for condition assessment.
        
        Args:
            spot_name: Name of the surf spot.
            skill_level: Skill level to assess for.
            days: Number of days to assess.
            
        Returns:
            Dictionary with assessments and recommendations.
        """
        # Fetch forecast
        forecast = await self.get_forecast(spot_name, days)
        
        if "error" in forecast:
            return forecast
        
        # Get cached ForecastResponse for proper assessment
        cached = self._get_cached_forecast(spot_name)
        
        if not cached or not cached.forecasts:
            return {
                "spot": spot_name,
                "skill_level": skill_level,
                "error": "No forecast data for assessment",
            }
        
        # Get daily summary
        summary = self._condition_assessor.get_daily_summary(
            cached.forecasts,
            skill_level
        )
        
        # Get individual assessments
        assessments = self._condition_assessor.assess_forecast_range(
            cached.forecasts,
            skill_level
        )
        
        return {
            "spot": spot_name,
            "source": forecast.get("source"),
            "skill_level": skill_level,
            "summary": summary,
            "assessments": [a.to_dict() for a in assessments],
            "total_hours_assessed": len(assessments),
        }
    
    async def find_surf_windows(
        self,
        spot_name: str,
        skill_level: str = "intermediate",
        days: int = 3,
    ) -> dict[str, Any]:
        """
        Find optimal surfing windows in the forecast.
        
        Identifies contiguous periods of favorable conditions
        for a given skill level.
        
        Args:
            spot_name: Name of the surf spot.
            skill_level: Skill level to find windows for.
            days: Number of days to search.
            
        Returns:
            Dictionary with windows and recommendations.
        """
        # Fetch forecast
        forecast = await self.get_forecast(spot_name, days)
        
        if "error" in forecast:
            return forecast
        
        # Get cached ForecastResponse
        cached = self._get_cached_forecast(spot_name)
        
        if not cached or not cached.forecasts:
            return {
                "spot": spot_name,
                "skill_level": skill_level,
                "error": "No forecast data for window analysis",
            }
        
        # Find windows
        result = self._window_finder.find_windows(
            cached.forecasts,
            skill_level,
            spot_name,
        )
        
        return {
            "spot": result.spot_name,
            "skill_level": result.skill_level,
            "source": forecast.get("source"),
            "forecast_period": {
                "start": result.forecast_start.isoformat(),
                "end": result.forecast_end.isoformat(),
            },
            "total_surfable_hours": result.total_surfable_hours,
            "window_count": len(result.windows),
            "best_window": result.best_window.to_dict() if result.best_window else None,
            "all_windows": [w.to_dict() for w in result.windows],
            "recommendation": result.recommendation,
            "display": result.format_for_display(),
        }
    
    async def find_windows_by_day(
        self,
        spot_name: str,
        skill_level: str = "intermediate",
        days: int = 3,
    ) -> dict[str, Any]:
        """
        Find surf windows grouped by day.
        
        Args:
            spot_name: Name of the surf spot.
            skill_level: Skill level to find windows for.
            days: Number of days to search.
            
        Returns:
            Dictionary with windows organized by date.
        """
        # Fetch forecast
        forecast = await self.get_forecast(spot_name, days)
        
        if "error" in forecast:
            return forecast
        
        # Get cached ForecastResponse
        cached = self._get_cached_forecast(spot_name)
        
        if not cached or not cached.forecasts:
            return {
                "spot": spot_name,
                "skill_level": skill_level,
                "error": "No forecast data",
            }
        
        # Find windows by day
        results_by_day = self._window_finder.find_windows_by_day(
            cached.forecasts,
            skill_level,
            spot_name,
        )
        
        return {
            "spot": spot_name,
            "skill_level": skill_level,
            "source": forecast.get("source"),
            "days": {
                date: {
                    "window_count": len(result.windows),
                    "total_surfable_hours": result.total_surfable_hours,
                    "best_window": result.best_window.to_dict() if result.best_window else None,
                    "recommendation": result.recommendation,
                }
                for date, result in results_by_day.items()
            },
        }
    
    async def _tool_find_best_window(
        self,
        forecast_data: dict[str, Any],
        min_hours: int = 2
    ) -> dict[str, Any]:
        """
        Tool: Find the best surfing window in the forecast.
        
        Uses the SurfWindowFinder for comprehensive analysis.
        
        Args:
            forecast_data: Forecast data dictionary.
            min_hours: Minimum window duration in hours.
            
        Returns:
            Best window information.
        """
        spot_name = forecast_data.get("spot", "Unknown")
        
        # Try to use cached forecasts for proper analysis
        cached = self._get_cached_forecast(spot_name)
        
        if cached and cached.forecasts:
            result = self._window_finder.find_windows(
                cached.forecasts,
                "intermediate",  # Default skill level
                spot_name,
                min_duration_hours=float(min_hours),
            )
            
            if result.best_window:
                return {
                    "best_time": result.best_window.start_time.isoformat(),
                    "end_time": result.best_window.end_time.isoformat(),
                    "duration_hours": result.best_window.duration_hours,
                    "quality": result.best_window.quality.value,
                    "score": result.best_window.average_score,
                    "recommendation": result.recommendation,
                }
        
        # Fallback to simple analysis
        if "forecasts" not in forecast_data:
            return {"error": "No forecast data"}
        
        best = None
        best_score = 0
        
        for fc in forecast_data["forecasts"]:
            wind = fc.get("wind", {})
            swell = fc.get("swell", {})
            
            score = 0
            if wind.get("is_light"):
                score += 3
            if wind.get("is_offshore"):
                score += 2
            if swell.get("period_s", 0) > 10:
                score += 2
            
            if score > best_score:
                best_score = score
                best = fc
        
        if best:
            return {
                "best_time": best["timestamp"],
                "summary": best["summary"],
                "score": best_score,
            }
        
        return {"message": "No clear best window found"}
    
    def clear_cache(self) -> None:
        """Clear all cached forecasts."""
        self._cache = {}
        self.log_info("Forecast cache cleared")

    async def plan_trip(
        self,
        spot_names: list[str],
        skill_level: str = "intermediate",
        days: int = 3,
        start_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Plan a multi-day surf trip across multiple spots.
        
        Fetches forecasts for all spots and creates an optimized
        itinerary considering weather, travel time, and logistics.
        
        Args:
            spot_names: List of spot names to consider.
            skill_level: User's skill level.
            days: Number of days for the trip.
            start_date: Trip start date (defaults to tomorrow).
            
        Returns:
            Dictionary with trip itinerary and recommendations.
        """
        from datetime import date as date_type
        
        self.log_info(f"Planning {days}-day trip across {len(spot_names)} spots")
        
        # Collect spot data and forecasts
        spots_data = []
        forecasts_by_spot = {}
        
        for spot_name in spot_names:
            # Get spot coordinates
            coords = self._get_spot_coordinates(spot_name)
            if not coords:
                self.log_warning(f"Unknown spot: {spot_name}, skipping")
                continue
            
            # Get spot info for contextual factors
            spot_info = self.get_spot_info(spot_name)
            
            # Calculate contextual scores
            crowd_score = 50.0
            parking_score = 50.0
            safety_score = 50.0
            
            if spot_info:
                # Map crowd level to score (inverse - low crowd = high score)
                crowd_map = {
                    "low": 90.0,
                    "medium": 70.0,
                    "high": 40.0,
                    "very_high": 20.0,
                }
                char = spot_info.get("characteristics", {})
                crowd_level = char.get("crowd_level", "medium")
                crowd_score = crowd_map.get(crowd_level, 50.0)
                
                # Parking score based on facilities
                facilities = spot_info.get("facilities", [])
                parking_score = 80.0 if "parking" in facilities else 40.0
                
                # Safety score (lower hazards = higher score)
                hazards = spot_info.get("hazards", [])
                safety_score = max(30.0, 100.0 - len(hazards) * 15)
            
            spots_data.append({
                "id": spot_name.lower().replace(" ", "_"),
                "name": spot_name,
                "latitude": coords.latitude,
                "longitude": coords.longitude,
                "parking_score": parking_score,
                "crowd_score": crowd_score,
                "safety_score": safety_score,
            })
            
            # Fetch forecast
            try:
                await self.get_forecast(spot_name, days + 1)  # Extra day for planning
                cached = self._get_cached_forecast(spot_name)
                if cached and cached.forecasts:
                    spot_id = spot_name.lower().replace(" ", "_")
                    forecasts_by_spot[spot_id] = cached.forecasts
            except Exception as e:
                self.log_warning(f"Failed to fetch forecast for {spot_name}: {e}")
        
        if not spots_data:
            return {
                "error": "No valid spots found",
                "message": "Could not find coordinates for any of the specified spots.",
            }
        
        if not forecasts_by_spot:
            return {
                "error": "No forecast data available",
                "message": "Could not fetch forecasts for any spots.",
            }
        
        # Convert start_date to date object
        trip_start = None
        if start_date:
            trip_start = start_date.date() if isinstance(start_date, datetime) else start_date
        
        # Plan the trip
        try:
            itinerary = self._trip_planner.plan_trip(
                spots_data=spots_data,
                forecasts_by_spot=forecasts_by_spot,
                skill_level=skill_level,
                trip_days=days,
                start_date=trip_start,
            )
            
            return {
                "success": True,
                "itinerary": itinerary.to_dict(),
                "display": itinerary.format_for_display(),
                "spots_checked": len(spots_data),
                "spots_with_forecasts": len(forecasts_by_spot),
            }
            
        except Exception as e:
            self.log_error(f"Trip planning failed: {e}")
            return {
                "error": str(e),
                "message": "Failed to generate trip itinerary.",
            }

    async def suggest_best_spot(
        self,
        spot_names: list[str],
        skill_level: str = "intermediate",
    ) -> dict[str, Any]:
        """
        Suggest the single best spot from a list.
        
        Args:
            spot_names: List of spots to consider.
            skill_level: User's skill level.
            
        Returns:
            Best spot recommendation.
        """
        spots_data = []
        forecasts_by_spot = {}
        
        for spot_name in spot_names:
            coords = self._get_spot_coordinates(spot_name)
            if not coords:
                continue
            
            spots_data.append({
                "id": spot_name.lower().replace(" ", "_"),
                "name": spot_name,
                "latitude": coords.latitude,
                "longitude": coords.longitude,
            })
            
            try:
                await self.get_forecast(spot_name, 2)
                cached = self._get_cached_forecast(spot_name)
                if cached and cached.forecasts:
                    spot_id = spot_name.lower().replace(" ", "_")
                    forecasts_by_spot[spot_id] = cached.forecasts
            except Exception:
                pass
        
        if not spots_data or not forecasts_by_spot:
            return {"error": "No valid spots or forecasts available"}
        
        result = self._trip_planner.suggest_best_spot(
            spots_data, forecasts_by_spot, skill_level
        )
        
        if result:
            return result
        
        return {"message": "No surfable conditions found at any spot"}
