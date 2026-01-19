"""
SurfSense Forecast Integration Agent (Layer 3)

Responsible for integrating forecast APIs:
- Fetches data from Stormglass API (primary, requires API key)
- Enriches/fallbacks with Open-Meteo (free, global coverage)
- Normalizes data to unified forecast models
- Provides forecast analysis and recommendations
- Caches and manages forecast data
"""

from datetime import datetime, timedelta
from typing import Any, Optional

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

logger = get_logger(__name__)


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
        
        # Check cache first
        cached = self._get_cached_forecast(spot_name)
        if cached:
            self.log_debug("Returning cached forecast")
            return self._forecast_to_dict(cached)
        
        # Fetch from API
        try:
            forecast = await self._fetch_from_api(spot_name, days, coordinates)
            
            # Cache the result
            self._cache_forecast(spot_name, forecast)
            
            return self._forecast_to_dict(forecast)
            
        except Exception as e:
            self.log_error(f"Failed to fetch forecast: {e}")
            return {
                "error": str(e),
                "spot": spot_name,
                "message": "Unable to fetch forecast data"
            }
    
    async def _fetch_from_api(
        self,
        spot_name: str,
        days: int,
        coordinates: Optional[Coordinates]
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
            coordinates = self._get_spot_coordinates(spot_name)
        
        if not coordinates:
            raise ValueError(
                f"Unknown spot: '{spot_name}'. "
                "Please provide coordinates or use a known spot name."
            )
        
        lat = coordinates.latitude
        lon = coordinates.longitude
        
        # Try Stormglass first if configured
        if self._stormglass_client.is_configured:
            try:
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
                return result
            except StormglassAPIError as e:
                self.log_warning(
                    f"Stormglass failed: {e}. Falling back to Open-Meteo."
                )
        
        # Fallback/primary: Open-Meteo (free, always available)
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
        
        return result
    
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
        
        Args:
            forecast_data: Forecast data dictionary.
            skill_level: User's skill level.
            
        Returns:
            Analysis with quality ratings and recommendations.
        """
        # Simple analysis based on conditions
        analysis = {
            "skill_level": skill_level,
            "overall_rating": "Unknown",
            "best_times": [],
            "warnings": [],
            "recommendations": []
        }
        
        if "forecasts" not in forecast_data:
            return analysis
        
        for fc in forecast_data["forecasts"]:
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
        if skill_level == "beginner":
            for fc in forecast_data["forecasts"]:
                waves = fc.get("waves", {})
                if waves.get("max_m", 0) > 1.5:
                    analysis["warnings"].append(
                        f"Wave height may be challenging at {fc['timestamp']}"
                    )
        
        return analysis
    
    async def _tool_find_best_window(
        self,
        forecast_data: dict[str, Any],
        min_hours: int = 2
    ) -> dict[str, Any]:
        """
        Tool: Find the best surfing window in the forecast.
        
        Args:
            forecast_data: Forecast data dictionary.
            min_hours: Minimum window duration in hours.
            
        Returns:
            Best window information.
        """
        if "forecasts" not in forecast_data:
            return {"error": "No forecast data"}
        
        # Simple implementation: find period with best conditions
        best = None
        best_score = 0
        
        for fc in forecast_data["forecasts"]:
            wind = fc.get("wind", {})
            waves = fc.get("waves", {})
            swell = fc.get("swell", {})
            
            # Simple scoring
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
                "conditions": best
            }
        
        return {"message": "No clear best window found"}
    
    def clear_cache(self) -> None:
        """Clear all cached forecasts."""
        self._cache = {}
        self.log_info("Forecast cache cleared")
