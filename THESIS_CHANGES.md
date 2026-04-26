# Thesis Text Change Checklist

Tracks every place in the thesis document that needs updating because of a
coding or data decision made during implementation.  Append new items here
whenever a coding choice diverges from what the thesis currently says.

**Status legend:** ☐ not done · ☑ done

---

## How to use this file

Each entry has:
- **Where** — chapter / section / paragraph so you can find it fast
- **Current text (paraphrase)** — what the thesis says right now
- **New text / action** — what it should say instead
- **Why** — the coding decision that triggered the change

---

## Chapter 3 — Methodology

### 3.3.3 — Forecast Data Agent / data sources

☐ **NOAA WaveWatch III removed**
- **Where:** Section 3.3.3, paragraph describing wave data sources
- **Current text:** mentions NOAA WaveWatch III hindcasts as the wave data source
- **New text:** Open-Meteo Marine API (`marine-api.open-meteo.com/v1/marine`) is used for all wave and swell variables (wave height, period, direction, swell height, swell period, swell direction, sea surface temperature) for all five spots. NOAA WW3 was evaluated and dropped — the Open-Meteo Marine hindcast provides comparable ERA5-backed reanalysis at the same resolution with a simpler REST interface and no authentication requirement.
- **Why:** During data source reconnaissance (2026-04-26) all five spots returned full 2-year coverage from Open-Meteo Marine. NOAA added complexity with no coverage benefit.
- **Evidence:** `ml/data/DATA_PROVENANCE.md`, `ml/data/collect.py`

---

☐ **Tide data limitation**
- **Where:** Section 3.3.3 or data appendix, wherever tide sources are described
- **Current text:** implies tide height is a populated feature
- **New text:** `tide_height_m` is not available from Open-Meteo. The column is left as NaN in the collected dataset and imputed to each spot's preferred tide midpoint (from `ml/data/spot_metadata.json`) during training. This is a known limitation: the model learns tidal effects from the Gaussian falloff encoded in the synthetic label, but cannot leverage real observed tide values at inference time. Noted as a future-work item.
- **Why:** Open-Meteo does not provide tide height data; no free alternative was available without additional API keys.
- **Evidence:** `ml/data/collect.py` line 121, `ml/data/DATA_PROVENANCE.md`

---

☐ **Timezone — all data is UTC, not local spot time**
- **Where:** Section 3.3.3 or data appendix, wherever the collected data is described
- **Current text:** may imply or state that timestamps reflect local spot time (given the five spots span five IANA timezones)
- **New text:** All hourly records in `historical.parquet` use UTC timestamps. Open-Meteo was queried with `timezone=UTC` for all five spots. Temporal features (`hour_sin`, `hour_cos`, `month_sin`, `month_cos`) are therefore encoded in UTC, not local surf time. This is a minor approximation: a dawn session at Pipeline (UTC−10) appears at 16:00 UTC, not 06:00 local. The effect is consistent across all spots and does not bias the comparison.
- **Why:** `ml/data/collect.py` uses `"timezone": "UTC"` in all API calls. IANA identifiers in the spot registry are metadata only; they are not applied to timestamps.
- **Evidence:** `ml/data/collect.py` line 106

---

### 3.3.5 — ML-Enhanced Scoring / model choice

☐ **XGBoost → scikit-learn HistGradientBoostingRegressor**
- **Where:** Section 3.3.5, "Features and model" paragraph — every mention of "XGBoost"
- **Current text:** "XGBoost regressor" / "XGBoost (Chen & Guestrin, 2016)"
- **New text:** "scikit-learn `HistGradientBoostingRegressor` (gradient boosted decision trees)" — cite scikit-learn paper (Pedregosa et al., 2011) instead of Chen & Guestrin. The algorithm is histogram-based GBDT, identical in design to XGBoost's default `tree_method='hist'`. The switch was made because XGBoost requires the OpenMP runtime (`libomp`) which is unavailable on the development machine; the scikit-learn implementation has no external runtime dependency and produces equivalent results.
- **Why:** `brew install libomp` blocked on work laptop; `/opt` not writable without admin. `HistGradientBoostingRegressor` + `shap.TreeExplainer` confirmed working.
- **Evidence:** confirmed in session 2026-04-26

---

☐ **Hyperparameter grid — update parameter names**
- **Where:** Section 3.3.5 or appendix, wherever the hyperparameter grid is listed
- **Current text:** lists XGBoost parameters: `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_weight`
- **New text:** HGBR parameter grid: `max_iter` (≡ n_estimators), `max_depth`, `learning_rate`, `min_samples_leaf` (≡ min_child_weight), `l2_regularization`. Remove `colsample_bytree` and `subsample` — HGBR uses histogram binning instead.
- **Why:** HGBR has a different hyperparameter API than XGBoost.
- **Evidence:** `ml/train.py` (after update)

---

### 3.5.1 — Internal Baseline Evaluation / acceptance thresholds

☐ **Fill in actual model metrics once training completes**
- **Where:** Section 3.5.1 and/or Chapter 4 results table — wherever "R² ≥ 0.75" and "classification accuracy ≥ 80 %" are stated as targets
- **Action:** Replace target values with actual values from `ml/models/model_metadata.json` once training runs. If actuals fall short, update the framing per the agreed fallback: "the ML model matches the rule-based system on two of three metric groups" (agreed with supervisor, see worklog 2026-04-22).
- **Why:** Results not yet known — placeholder targets in thesis need to become real numbers.
- **Evidence:** `ml/models/model_metadata.json` (after training)

---

### 3.5.2 — LLM Baseline / systems compared

☐ **Claude baseline — mark as optional or remove**
- **Where:** Section 3.5.2, the list of systems in the LLM baseline comparison
- **Current text:** lists three systems: SurfSense, GPT-4o, Claude
- **New text:** Two-system comparison: SurfSense vs GPT-4o. Claude baseline is noted as a planned extension; the `anthropic` Python package is not installed and no Anthropic API key is configured for Phase 1. If Claude runs are added later, update this.
- **Why:** Decision made 2026-04-22 — SurfSense + GPT-4o sufficient for thesis baseline. Claude is optional.
- **Evidence:** WORKLOG.md entry 2026-04-22

---

## Chapter 4 — Results

☐ **Scenario output excerpts** — write captions referencing snapshot files
- **Where:** Section 4.1 figures and listings
- **Action:** Every figure caption or code listing that shows scenario output must trace to a specific file under `scenarios/snapshots/` and `scenarios/results/`. Add filename + date of snapshot run in the caption.
- **Why:** Reproducibility requirement — Chapter 4 figures must be traceable to artifacts on disk.

---

☐ **Fill in all metric values** (after evaluation notebooks run)
- R² on test set
- MAE, RMSE on test set
- Classification accuracy and macro F1 on test set
- Spearman's ρ on test set
- Per-spot and per-season breakdowns
- LLM baseline five-dimension table
- **Where:** Chapter 4 tables and inline claims

---

## Appendix

☐ **Data provenance appendix** — copy from `ml/data/DATA_PROVENANCE.md`
- **Action:** The provenance file is written to be dropped directly into the thesis appendix. Copy it in and format it per the document style. Four sources: Open-Meteo Marine, Open-Meteo Archive (weather), tide (NaN / limitation), spot metadata.

---

☐ **Submission commit SHA** — add to appendix after final commit
- **Action:** After tagging `v1.0-submission`, record the git SHA in the thesis appendix reproducibility section.

---

*Append new items below as they arise. Do not delete items; mark them ☑ when done.*
