"""
One-time script to fetch scenario snapshot files from Open-Meteo.

Run this to create or refresh snapshot JSON files for new spots defined in
SNAPSHOT_SPECS. Commit the output and do not re-run unless adding new scenarios.

Usage:
    python -m scenarios.generate_snapshots --list
    python -m scenarios.generate_snapshots --snapshot hossegor_5d
    python -m scenarios.generate_snapshots --all
    python -m scenarios.generate_snapshots --all --force
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

SNAPSHOTS_DIR = Path("scenarios/snapshots")

MARINE_URL  = "https://marine-api.open-meteo.com/v1/marine"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

MARINE_PARAMS = [
    "wave_height", "wave_direction", "wave_period",
    "swell_wave_height", "swell_wave_direction", "swell_wave_period",
    "swell_wave_peak_period",
]
WEATHER_PARAMS = [
    "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
    "temperature_2m",
]

# Spots to generate snapshots for. Only spots NOT already covered by existing
# snapshot files need entries here. Existing files are preserved by default.
SNAPSHOT_SPECS: dict[str, dict] = {
    "hossegor_5d": {
        "name": "Hossegor",
        "lat": 43.6676,
        "lon": -1.4412,
        "days": 5,
    },
    "jeffreys_bay_5d": {
        "name": "Jeffreys Bay",
        "lat": -34.0407,
        "lon": 24.9309,
        "days": 5,
    },
}

_COMPASS = [
    "N","NNE","NE","ENE","E","ESE","SE","SSE",
    "S","SSW","SW","WSW","W","WNW","NW","NNW",
]

def _deg_to_compass(deg: float) -> str:
    idx = round(deg / 22.5) % 16
    return _COMPASS[idx]


def _is_offshore(wind_dir_deg: float, swell_dir_deg: float) -> bool:
    """Simple offshore check: wind blowing away from the swell face (±45°)."""
    diff = (wind_dir_deg - swell_dir_deg + 180) % 360 - 180
    return abs(diff) > 90


async def _fetch_spot(spec: dict) -> dict:
    lat, lon = spec["lat"], spec["lon"]
    days = spec["days"]
    name = spec["name"]

    async with httpx.AsyncClient(timeout=20.0) as client:
        marine_resp, weather_resp = await asyncio.gather(
            client.get(MARINE_URL, params={
                "latitude": lat, "longitude": lon,
                "hourly": ",".join(MARINE_PARAMS),
                "forecast_days": days, "timezone": "UTC",
            }),
            client.get(WEATHER_URL, params={
                "latitude": lat, "longitude": lon,
                "hourly": ",".join(WEATHER_PARAMS),
                "forecast_days": days, "timezone": "UTC",
                "wind_speed_unit": "kmh",
            }),
        )

    if marine_resp.status_code != 200:
        raise RuntimeError(f"Marine API error {marine_resp.status_code}: {marine_resp.text}")
    if weather_resp.status_code != 200:
        raise RuntimeError(f"Weather API error {weather_resp.status_code}: {weather_resp.text}")

    marine  = marine_resp.json()["hourly"]
    weather = weather_resp.json()["hourly"]
    times   = marine["time"]

    def g(data: dict, key: str, i: int, default: float = 0.0) -> float:
        vals = data.get(key, [])
        v = vals[i] if i < len(vals) and vals[i] is not None else default
        return float(v)

    forecasts = []
    for i, ts in enumerate(times):
        wave_h   = g(marine,  "wave_height",            i)
        swell_h  = g(marine,  "swell_wave_height",      i, wave_h)
        swell_t  = g(marine,  "swell_wave_peak_period", i) or g(marine, "swell_wave_period", i)
        swell_d  = g(marine,  "swell_wave_direction",   i)
        wind_s   = g(weather, "wind_speed_10m",         i)
        wind_d   = g(weather, "wind_direction_10m",     i)

        swell_dir_str = _deg_to_compass(swell_d)
        wind_dir_str  = _deg_to_compass(wind_d)
        offshore      = _is_offshore(wind_d, swell_d)
        light         = wind_s < 15.0

        forecasts.append({
            "timestamp": ts + ":00",
            "summary": (
                f"{ts} UTC: Waves {round(wave_h*0.8,1)}-{round(wave_h*1.2,1)}m, "
                f"Swell {round(swell_t)}s from {swell_dir_str}, "
                f"Wind {round(wind_s)}km/h {wind_dir_str}"
            ),
            "waves": {
                "min_m": round(wave_h * 0.8, 2),
                "max_m": round(wave_h * 1.2, 2),
                "avg_m": round(wave_h, 2),
            },
            "swell": {
                "height_m":     round(swell_h, 2),
                "period_s":     round(swell_t, 2),
                "direction":    swell_dir_str,
                "direction_deg": round(swell_d, 1),
            },
            "wind": {
                "speed_kph":    round(wind_s, 1),
                "direction":    wind_dir_str,
                "direction_deg": round(wind_d, 1),
                "is_offshore":  offshore,
                "is_light":     light,
            },
        })

    return {
        "spot":        name,
        "coordinates": {"lat": lat, "lon": lon},
        "source":      "open_meteo",
        "fetched_at":  datetime.utcnow().isoformat(),
        "forecast_count": len(forecasts),
        "forecasts":   forecasts,
    }


async def generate(snapshot_id: str, force: bool = False) -> None:
    if snapshot_id not in SNAPSHOT_SPECS:
        print(f"  [skip] '{snapshot_id}' not in SNAPSHOT_SPECS")
        return

    out_path = SNAPSHOTS_DIR / f"{snapshot_id}.json"
    if out_path.exists() and not force:
        print(f"  [exists] {out_path}  (use --force to regenerate)")
        return

    spec = SNAPSHOT_SPECS[snapshot_id]
    print(f"  Fetching {spec['name']} ({spec['days']}d) …", end=" ", flush=True)
    try:
        data = await _fetch_spot(spec)
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(data, indent=2))
        print(f"done  ({data['forecast_count']} hours → {out_path})")
    except Exception as exc:
        print(f"ERROR: {exc}")


async def generate_all(force: bool = False) -> None:
    for sid in SNAPSHOT_SPECS:
        await generate(sid, force=force)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=str, default=None,
                        help="ID of a single snapshot to generate")
    parser.add_argument("--all", action="store_true",
                        help="Generate all snapshots defined in SNAPSHOT_SPECS")
    parser.add_argument("--list", action="store_true",
                        help="List defined snapshot specs and exit")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing snapshot files")
    args = parser.parse_args()

    if args.list:
        for sid, spec in SNAPSHOT_SPECS.items():
            exists = "✓" if (SNAPSHOTS_DIR / f"{sid}.json").exists() else "✗"
            print(f"  [{exists}] {sid:30s}  {spec['name']} ({spec['days']}d)")
        sys.exit(0)

    if args.snapshot:
        asyncio.run(generate(args.snapshot, force=args.force))
    elif args.all:
        asyncio.run(generate_all(force=args.force))
    else:
        parser.print_help()
