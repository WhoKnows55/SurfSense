"""
SurfSense Forecast Integration Agent (Layer 3)

Responsible for integrating forecast APIs and models:
- Fetches data from forecast services (Stormglass, etc.)
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
    SwellData,
    TideData,
    WaveData,
    WeatherData,
    WindData,
)

logger = get_logger(__name__)


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
        
        # API clients (to be initialized)
        self._stormglass_client = None
        
        # Register tools
        self._register_default_tools()
    
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
        Fetch forecast from the API service.
        
        Currently returns mock data. Will be replaced with actual
        API integration (Stormglass, etc.)
        """
        # TODO: Implement actual API integration
        # For now, return mock data for development
        
        mock_forecasts = self._generate_mock_forecast(spot_name, days)
        
        return ForecastResponse(
            spot=SpotMetadata(
                name=spot_name,
                coordinates=coordinates or Coordinates(
                    latitude=0.0,
                    longitude=0.0
                ),
                timezone="UTC"
            ),
            forecasts=mock_forecasts,
            source=DataSource.LOCAL_MODEL,
            fetched_at=datetime.utcnow()
        )
    
    def _generate_mock_forecast(
        self,
        spot_name: str,
        days: int
    ) -> list[ForecastPoint]:
        """Generate mock forecast data for development."""
        import random
        
        forecasts = []
        base_time = datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0)
        
        for day in range(days):
            for hour in [6, 9, 12, 15, 18]:
                timestamp = base_time + timedelta(days=day, hours=hour-6)
                
                # Generate somewhat realistic mock data
                wave_min = round(random.uniform(0.5, 2.0), 1)
                wave_max = wave_min + round(random.uniform(0.3, 1.0), 1)
                
                point = ForecastPoint(
                    timestamp=timestamp,
                    source=DataSource.LOCAL_MODEL,
                    waves=WaveData(
                        height_min=wave_min,
                        height_max=wave_max
                    ),
                    swell=SwellData(
                        height=round(random.uniform(0.8, 2.5), 1),
                        period=round(random.uniform(8, 16), 0),
                        direction_degrees=round(random.uniform(180, 300), 0)
                    ),
                    wind=WindData(
                        speed=round(random.uniform(5, 30), 0),
                        direction_degrees=round(random.uniform(0, 360), 0)
                    ),
                    tide=TideData(
                        height=round(random.uniform(-0.5, 2.0), 1)
                    ),
                    weather=WeatherData(
                        description="Partly cloudy",
                        temperature=round(random.uniform(15, 25), 0),
                        water_temperature=round(random.uniform(14, 20), 0)
                    )
                )
                forecasts.append(point)
        
        return forecasts
    
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
