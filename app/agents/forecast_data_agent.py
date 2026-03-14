"""
SurfSense Forecast Data Agent

Deterministic sub-agent that aggregates heterogeneous surf data
(wave forecasts, tide, wind, contextual info) into a unified
representation for the orchestrator.

Wraps existing forecasting clients, contextual providers, and spot database.
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from app.contextual import (
    AccessibilityProvider,
    ParkingProvider,
    ReviewsProvider,
    SafetyProvider,
)
from app.core.logger import LoggerMixin, get_logger
from app.forecasting.models import Coordinates, ForecastResponse
from app.forecasting.openmeteo_client import OpenMeteoClient
from app.forecasting.stormglass_client import StormglassClient, StormglassAPIError
from app.knowledge import get_spot_database

logger = get_logger(__name__)

# Fallback known spots (same as in forecast_integration.py)
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


class ForecastDataAgent(LoggerMixin):
    """Deterministic sub-agent for data aggregation.

    Exposes tools for the orchestrator to:
    - fetch_forecast: Get unified forecast data for a spot
    - fetch_contextual_info: Get parking, accessibility, reviews, safety
    - get_spot_metadata: Get static spot information
    """

    def __init__(self, settings):
        self._settings = settings
        self._forecast_cache: dict[str, dict] = {}
        self._cache_ttl = timedelta(hours=1)

        # Forecast API clients
        self._openmeteo_client = OpenMeteoClient()
        self._stormglass_client = StormglassClient()

        # Contextual providers
        self._parking = ParkingProvider()
        self._accessibility = AccessibilityProvider()
        self._reviews = ReviewsProvider()
        self._safety = SafetyProvider()

        # Spot database
        self._spot_db = get_spot_database()

    def _get_spot_coordinates(self, spot_name: str) -> Optional[Coordinates]:
        """Look up coordinates for a spot name."""
        coords = self._spot_db.get_coordinates(spot_name)
        if coords:
            return Coordinates(latitude=coords[0], longitude=coords[1])
        normalized = spot_name.lower().strip()
        return KNOWN_SPOTS.get(normalized)

    def _get_cached_forecast(self, spot_name: str) -> Optional[dict]:
        """Return cached forecast if still valid."""
        key = spot_name.lower().strip()
        if key not in self._forecast_cache:
            return None
        entry = self._forecast_cache[key]
        age = datetime.utcnow() - entry.get("_cached_at", datetime.min)
        if age > self._cache_ttl:
            del self._forecast_cache[key]
            return None
        return entry

    def _cache_forecast(self, spot_name: str, data: dict) -> None:
        """Cache a forecast result."""
        key = spot_name.lower().strip()
        data["_cached_at"] = datetime.utcnow()
        self._forecast_cache[key] = data

    def _forecast_to_dict(self, forecast: ForecastResponse) -> dict:
        """Convert ForecastResponse to a dict the orchestrator can consume."""
        return {
            "spot": forecast.spot.name,
            "coordinates": {
                "lat": forecast.spot.coordinates.latitude,
                "lon": forecast.spot.coordinates.longitude,
            },
            "source": forecast.source.value,
            "fetched_at": forecast.fetched_at.isoformat(),
            "forecast_count": len(forecast.forecasts),
            "forecasts": [
                {
                    "timestamp": f.timestamp.isoformat(),
                    "summary": f.summary(),
                    "waves": {
                        "min_m": f.waves.height_min if f.waves else None,
                        "max_m": f.waves.height_max if f.waves else None,
                        "avg_m": f.waves.height_avg if f.waves else None,
                    },
                    "swell": {
                        "height_m": f.swell.height if f.swell else None,
                        "period_s": f.swell.period if f.swell else None,
                        "direction": (
                            f.swell.direction.value
                            if f.swell and f.swell.direction
                            else None
                        ),
                    },
                    "wind": {
                        "speed_kph": f.wind.speed if f.wind else 0,
                        "direction": (
                            f.wind.direction.value
                            if f.wind and f.wind.direction
                            else None
                        ),
                        "is_offshore": f.is_offshore_wind,
                        "is_light": f.is_light_wind,
                    },
                }
                for f in forecast.forecasts
            ],
        }

    async def fetch_forecast(self, spot_name: str, days: int = 3) -> dict:
        """Fetch and unify forecast data for a spot.

        Args:
            spot_name: Name of the surf spot.
            days: Number of forecast days (1-7).

        Returns:
            Unified forecast dict with hourly data.
        """
        cached = self._get_cached_forecast(spot_name)
        if cached:
            return cached

        coordinates = self._get_spot_coordinates(spot_name)
        if not coordinates:
            return {
                "error": f"Unknown spot: '{spot_name}'. Use a known spot name.",
                "spot": spot_name,
            }

        lat = coordinates.latitude
        lon = coordinates.longitude

        # Try Stormglass first if configured
        if self._stormglass_client.is_configured:
            try:
                result = await self._stormglass_client.get_forecast(
                    latitude=lat, longitude=lon, spot_name=spot_name, days=days
                )
                data = self._forecast_to_dict(result)
                self._cache_forecast(spot_name, data)
                return data
            except StormglassAPIError:
                pass  # Fall through to Open-Meteo

        # Fallback / primary: Open-Meteo (free)
        try:
            result = await self._openmeteo_client.get_forecast(
                latitude=lat, longitude=lon, spot_name=spot_name, days=days
            )
            data = self._forecast_to_dict(result)
            self._cache_forecast(spot_name, data)
            return data
        except Exception as e:
            return {
                "error": str(e),
                "spot": spot_name,
                "message": "Unable to fetch forecast data",
            }

    async def fetch_contextual_info(self, spot_name: str) -> dict:
        """Aggregate contextual data from all providers.

        Args:
            spot_name: Name of the surf spot.

        Returns:
            Dict with parking, accessibility, reviews, and safety info.
        """
        parking = await self._parking.get_data(spot_name)
        access = await self._accessibility.get_data(spot_name)
        reviews = await self._reviews.get_data(spot_name)
        safety = await self._safety.get_data(spot_name)
        return {
            "spot_name": spot_name,
            "parking": parking.model_dump(),
            "accessibility": access.model_dump(),
            "reviews": reviews.model_dump(),
            "safety": safety.model_dump(),
        }

    async def get_spot_metadata(self, spot_name: str) -> dict:
        """Return static metadata for a surf spot.

        Args:
            spot_name: Name of the surf spot.

        Returns:
            Dict with coordinates, timezone, break type, etc.
        """
        # Try comprehensive database first
        spot = self._spot_db.get_spot(spot_name.lower())
        if not spot:
            matches = self._spot_db.search_by_name(spot_name)
            if matches:
                spot = matches[0]

        if spot:
            return {
                "name": spot.name,
                "coordinates": {
                    "lat": spot.location.latitude,
                    "lon": spot.location.longitude,
                },
                "timezone": spot.location.timezone,
                "break_type": spot.characteristics.break_type.value,
                "region": spot.location.region,
                "country": spot.location.country,
                "skill_levels": {
                    "minimum": spot.skill_levels.minimum.value,
                    "recommended": spot.skill_levels.recommended.value,
                },
                "hazards": spot.hazards,
                "description": spot.description,
            }

        # Fallback to KNOWN_SPOTS
        coords = self._get_spot_coordinates(spot_name)
        if coords:
            return {
                "name": spot_name,
                "coordinates": {
                    "lat": coords.latitude,
                    "lon": coords.longitude,
                },
                "timezone": "UTC",
                "break_type": "unknown",
            }

        return {"error": f"Spot '{spot_name}' not found in database."}

    @staticmethod
    def get_tool_definitions() -> list[dict]:
        """Return OpenAI function-calling schemas for all tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "fetch_forecast",
                    "description": (
                        "Fetch surf forecast data (waves, swell, wind, tide) "
                        "for a spot over N days. Returns hourly data normalised "
                        "to a unified schema."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {
                                "type": "string",
                                "description": "Name of the surf spot",
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to forecast (1-7)",
                                "default": 3,
                            },
                        },
                        "required": ["spot_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fetch_contextual_info",
                    "description": (
                        "Get parking, accessibility, reviews, and safety "
                        "information for a surf spot."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {
                                "type": "string",
                                "description": "Name of the surf spot",
                            },
                        },
                        "required": ["spot_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_spot_metadata",
                    "description": (
                        "Get static metadata for a surf spot: coordinates, "
                        "timezone, break type."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "spot_name": {
                                "type": "string",
                                "description": "Name of the surf spot",
                            },
                        },
                        "required": ["spot_name"],
                    },
                },
            },
        ]
