"""
Forecasting layer for SurfSense.

This module handles:
- External forecast API integration
- Local fallback forecasting models
- Unified forecast data schema
- Forecast service orchestration
"""

from app.forecasting.models import (
    Coordinates,
    DataSource,
    ForecastPoint,
    ForecastResponse,
    SpotMetadata,
    SwellData,
    SwellDirection,
    TideData,
    TideState,
    WaveData,
    WeatherData,
    WindData,
    WindDirection,
)

__all__ = [
    # Core forecast models
    "ForecastPoint",
    "ForecastResponse",
    # Component models
    "WaveData",
    "SwellData",
    "WindData",
    "TideData",
    "WeatherData",
    # Metadata
    "SpotMetadata",
    "Coordinates",
    "DataSource",
    # Enums
    "WindDirection",
    "SwellDirection",
    "TideState",
]
