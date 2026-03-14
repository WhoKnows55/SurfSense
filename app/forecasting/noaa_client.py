"""
NOAA Marine Weather API Client

Fetches marine weather data from NOAA's free public APIs.
No API key required!

Data sources:
- NOAA Marine Weather Forecast: https://www.weather.gov/documentation/services-web-api
- NDBC (National Data Buoy Center): https://www.ndbc.noaa.gov/

Note: NOAA data is primarily for US coastal waters.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from app.core.logger import LoggerMixin, get_logger
from app.forecasting.base_client import ForecastAPIClient
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


class NOAAClient(ForecastAPIClient, LoggerMixin):
    """
    Client for NOAA marine weather data.
    
    FREE - no API key required!
    
    Limitations:
    - Only covers US coastal waters
    - Less detailed wave data than Stormglass
    - Rate limited (fair use policy)
    """
    
    # NOAA Weather API base URL
    WEATHER_API_BASE = "https://api.weather.gov"
    
    # NDBC (Buoy data) base URL
    NDBC_BASE = "https://www.ndbc.noaa.gov/data/realtime2"
    
    # US coastal bounding box (approximate)
    US_COASTAL_BOUNDS = {
        "min_lat": 24.5,   # Southern Florida
        "max_lat": 49.0,   # Northern Washington
        "min_lon": -125.0, # West Coast
        "max_lon": -66.0,  # East Coast
    }
    
    # Hawaiian Islands
    HAWAII_BOUNDS = {
        "min_lat": 18.0,
        "max_lat": 23.0,
        "min_lon": -161.0,
        "max_lon": -154.0,
    }
    
    def __init__(self, timeout: float = 15.0):
        """
        Initialize the NOAA client.
        
        Args:
            timeout: Request timeout in seconds (NOAA can be slow).
        """
        self.timeout = timeout
        self._user_agent = "(SurfSense, github.com/surfsense)"
    
    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "noaa"
    
    @property
    def is_configured(self) -> bool:
        """NOAA is always configured (no API key needed)."""
        return True
    
    @property
    def requires_api_key(self) -> bool:
        """NOAA does not require an API key."""
        return False
    
    def supports_location(self, lat: float, lon: float) -> bool:
        """
        Check if NOAA covers this location.
        
        NOAA primarily covers US coastal waters including Hawaii.
        """
        # Check US continental coastal waters
        us = self.US_COASTAL_BOUNDS
        if (us["min_lat"] <= lat <= us["max_lat"] and 
            us["min_lon"] <= lon <= us["max_lon"]):
            return True
        
        # Check Hawaii
        hi = self.HAWAII_BOUNDS
        if (hi["min_lat"] <= lat <= hi["max_lat"] and 
            hi["min_lon"] <= lon <= hi["max_lon"]):
            return True
        
        return False
    
    def _get_headers(self) -> dict[str, str]:
        """Get request headers with user agent."""
        return {
            "User-Agent": self._user_agent,
            "Accept": "application/geo+json",
        }
    
    async def get_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 5,
    ) -> Optional[ForecastResponse]:
        """
        Fetch marine weather forecast from NOAA.
        
        Uses the Weather.gov API which provides detailed forecasts
        for US locations.
        
        Args:
            lat: Latitude of the location.
            lon: Longitude of the location.
            days: Number of days to forecast (max ~7 for NOAA).
            
        Returns:
            ForecastResponse if successful, None if failed.
        """
        if not self.supports_location(lat, lon):
            self.log_warning(
                f"NOAA does not cover location: {lat}, {lon}"
            )
            return None
        
        self.log_info(f"Fetching NOAA forecast for {lat}, {lon}")
        
        try:
            # Step 1: Get grid point for location
            grid_info = await self._get_grid_point(lat, lon)
            if not grid_info:
                return None
            
            # Step 2: Get forecast from grid endpoint
            forecast_data = await self._get_forecast_data(grid_info)
            if not forecast_data:
                return None
            
            # Step 3: Transform to our schema
            forecast_points = self._transform_forecast(forecast_data, days)
            
            return ForecastResponse(
                spot=SpotMetadata(
                    name=f"NOAA Grid {grid_info.get('gridId', 'Unknown')}",
                    coordinates=Coordinates(latitude=lat, longitude=lon),
                    timezone=grid_info.get("timeZone", "America/Los_Angeles"),
                ),
                forecasts=forecast_points,
                source=DataSource.NOAA,
                fetched_at=datetime.utcnow(),
            )
            
        except Exception as e:
            self.log_error(f"NOAA forecast failed: {e}")
            return None
    
    async def _get_grid_point(self, lat: float, lon: float) -> Optional[dict]:
        """
        Get NOAA grid point info for a location.
        
        This is required to get the forecast endpoint URL.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = f"{self.WEATHER_API_BASE}/points/{lat},{lon}"
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code != 200:
                    self.log_warning(
                        f"NOAA grid point lookup failed: {response.status_code}"
                    )
                    return None
                
                data = response.json()
                props = data.get("properties", {})
                
                return {
                    "gridId": props.get("gridId"),
                    "gridX": props.get("gridX"),
                    "gridY": props.get("gridY"),
                    "forecastUrl": props.get("forecast"),
                    "forecastHourlyUrl": props.get("forecastHourly"),
                    "timeZone": props.get("timeZone"),
                }
                
        except httpx.TimeoutException:
            self.log_warning("NOAA grid point request timed out")
            return None
        except Exception as e:
            self.log_warning(f"NOAA grid point error: {e}")
            return None
    
    async def _get_forecast_data(self, grid_info: dict) -> Optional[dict]:
        """
        Fetch forecast data from the grid endpoint.
        """
        forecast_url = grid_info.get("forecastHourlyUrl")
        if not forecast_url:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    forecast_url, 
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    self.log_warning(
                        f"NOAA forecast fetch failed: {response.status_code}"
                    )
                    return None
                
                return response.json()
                
        except httpx.TimeoutException:
            self.log_warning("NOAA forecast request timed out")
            return None
        except Exception as e:
            self.log_warning(f"NOAA forecast error: {e}")
            return None
    
    def _transform_forecast(
        self,
        data: dict,
        days: int
    ) -> list[ForecastPoint]:
        """
        Transform NOAA forecast response to our schema.
        
        NOAA provides hourly forecasts with wind, temperature,
        and general weather conditions.
        """
        forecast_points = []
        
        properties = data.get("properties", {})
        periods = properties.get("periods", [])
        
        # Limit to requested days (24 hours per day)
        max_periods = days * 24
        
        for period in periods[:max_periods]:
            try:
                point = self._parse_period(period)
                if point:
                    forecast_points.append(point)
            except Exception as e:
                self.log_warning(f"Failed to parse NOAA period: {e}")
                continue
        
        self.log_info(f"Parsed {len(forecast_points)} NOAA forecast points")
        return forecast_points
    
    def _parse_period(self, period: dict) -> Optional[ForecastPoint]:
        """Parse a single forecast period from NOAA."""
        start_time = period.get("startTime")
        if not start_time:
            return None
        
        timestamp = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        
        # Extract wind data
        wind_speed_str = period.get("windSpeed", "0 mph")
        wind_direction_str = period.get("windDirection", "N")
        
        # Parse wind speed (e.g., "10 mph" or "5 to 10 mph")
        wind_speed = self._parse_wind_speed(wind_speed_str)
        wind_direction = self._cardinal_to_degrees(wind_direction_str)
        
        wind = WindData(
            speed=wind_speed,
            direction_degrees=wind_direction,
            gust=None,  # NOAA doesn't always provide gust
        )
        
        # Extract temperature
        temp_value = period.get("temperature")
        temp_unit = period.get("temperatureUnit", "F")
        
        # Convert F to C if needed
        if temp_unit == "F" and temp_value:
            temp_c = (temp_value - 32) * 5 / 9
        else:
            temp_c = temp_value
        
        # Weather description
        description = period.get("shortForecast", "Unknown")
        
        weather = WeatherData(
            description=description,
            temperature=temp_c,
            water_temperature=None,  # NOAA doesn't provide water temp here
        )
        
        # NOAA doesn't provide wave/swell data in the standard forecast
        # We'll use placeholder data - real implementation would query buoys
        waves = WaveData(height_min=0.0, height_max=0.0)
        swell = SwellData(height=0.0, period=0.0, direction_degrees=0.0)
        tide = TideData(height=0.0)
        
        return ForecastPoint(
            timestamp=timestamp,
            source=DataSource.NOAA,
            waves=waves,
            swell=swell,
            wind=wind,
            tide=tide,
            weather=weather,
        )
    
    def _parse_wind_speed(self, wind_str: str) -> float:
        """
        Parse NOAA wind speed string to km/h.
        
        Examples: "10 mph", "5 to 10 mph", "15 to 25 mph"
        """
        import re
        
        # Find all numbers
        numbers = re.findall(r'\d+', wind_str)
        if not numbers:
            return 0.0
        
        # Take the average if range, otherwise the single value
        values = [float(n) for n in numbers]
        avg_mph = sum(values) / len(values)
        
        # Convert mph to km/h
        return avg_mph * 1.60934
    
    def _cardinal_to_degrees(self, direction: str) -> float:
        """Convert cardinal direction to degrees."""
        directions = {
            "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5,
            "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
            "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5,
            "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5,
        }
        return directions.get(direction.upper(), 0.0)
    
    async def get_tide(
        self,
        lat: float,
        lon: float,
        date: Optional[datetime] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Get tide predictions from NOAA.
        
        Note: Full implementation would use NOAA CO-OPS API.
        For now, returns None as tide data requires station lookup.
        
        Args:
            lat: Latitude.
            lon: Longitude.
            date: Date for tide data.
            
        Returns:
            Tide data dictionary, or None.
        """
        # TODO: Implement NOAA CO-OPS tide predictions
        # https://tidesandcurrents.noaa.gov/api/
        self.log_info("NOAA tide data not yet implemented")
        return None
    
    async def health_check(self) -> bool:
        """Check if NOAA API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.WEATHER_API_BASE}/",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception:
            return False


# Convenience function
async def fetch_noaa_forecast(
    lat: float,
    lon: float,
    days: int = 5,
) -> Optional[ForecastResponse]:
    """
    Quick helper to fetch NOAA forecast.
    
    Args:
        lat: Latitude.
        lon: Longitude.
        days: Number of days.
        
    Returns:
        ForecastResponse if successful, None otherwise.
    """
    client = NOAAClient()
    return await client.get_forecast(lat, lon, days)
