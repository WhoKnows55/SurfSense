# Data Provenance

This document records the source, access date, license, and any substitution rationale for every external data source used in the SurfSense ML evaluation pipeline. It is intended to drop directly into the thesis data-provenance appendix.

---

## 1. Open-Meteo Marine API

**URL:** `https://marine-api.open-meteo.com/v1/marine`

**Variables retrieved:** `wave_height`, `wave_period`, `wave_direction`, `swell_wave_height`, `swell_wave_period`, `swell_wave_direction`, `wind_wave_height`, `wind_wave_period`

**Temporal resolution:** Hourly

**Spots covered:** Pipeline (Hawaii), Hossegor (France), Ericeira (Portugal), Jeffreys Bay (South Africa), Gold Coast (Australia)

**Date of access / verification:** 2026-04-26. A 7-day test request was made for each spot and returned 192 rows per spot with no errors.

**License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Open-Meteo is a free, open-source weather API. No API key required. Attribution required.

**Substitution note:** NOAA WaveWatch III (WW3) was the originally planned marine data source. It was dropped in favour of Open-Meteo Marine for the following reasons: (1) Open-Meteo provides a simpler REST interface with no authentication requirement, reducing pipeline complexity; (2) the free fair-use tier covers the full 2-year hindcast window needed for all five spots; (3) the marine hindcast is derived from ERA5-based reanalysis, which is the same underlying source as the NOAA WW3 global model at comparable resolution for open-ocean reef and point breaks. The substitution is documented here and referenced in Section 3.3.5 of the thesis.

---

## 2. Open-Meteo Archive API

**URL:** `https://archive-api.open-meteo.com/v1/archive`

**Variables retrieved:** `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`, `temperature_2m`

**Temporal resolution:** Hourly

**Spots covered:** Pipeline (Hawaii), Hossegor (France), Ericeira (Portugal), Jeffreys Bay (South Africa), Gold Coast (Australia)

**Date of access / verification:** 2026-04-26. A 7-day test request was made for each spot and returned 192 rows per spot with no errors.

**License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). No API key required. Attribution required.

**Notes:** Wind variables are taken at 10 m height above ground. This is a standard meteorological reference height and consistent with surf-forecast wind reporting conventions. ERA5 reanalysis underpins the archive; spatial resolution is ~9 km, which is sufficient for the regional wind patterns that determine offshore/onshore conditions at each spot.

---

## 3. Tide Data

**Source:** Not collected from an external API.

**Status:** `tide_height_m` is set to `NaN` for all rows in `ml/data/processed/historical.parquet`. During model training, missing tide values are imputed to the spot's preferred tidal midpoint as defined in `ml/data/spot_metadata.json`.

**Rationale:** Open-Meteo does not provide tidal predictions. Alternative sources (WorldTides, local hydrographic offices) require per-region API keys and non-uniform coverage across the five spots. Given that tide is a secondary modulator of surf quality compared to swell and wind, and given that the synthetic label formula (Section 2.2) uses a Gaussian falloff centred on the preferred tide band rather than a hard gate, imputation to the preferred midpoint introduces a known but bounded bias. This limitation is acknowledged in Section 3.3.5 and the thesis discussion.

---

## 4. Spot Physical Parameters

**Source:** `ml/data/spot_metadata.json`

**Contents:** Per-spot swell-facing direction (degrees), preferred tide band, wind speed ceiling (kph), break type, and IANA timezone identifier.

**Provenance:** Compiled from Surfline spot guides and mechanics articles (accessed 2026-04-22). See `ml/SPOT_RESEARCH_TRACKER.md` for per-spot source citations. Parameters ground the synthetic label formula (Section 2.2) and are version-controlled alongside the pipeline code to ensure reproducibility.

---

*Last updated: 2026-04-26*
