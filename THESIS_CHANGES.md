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

☑ **Fill in actual model metrics once training completes**
- **Where:** Section 3.5.1 and/or Chapter 4 results table — wherever "R² ≥ 0.75" and "classification accuracy ≥ 80 %" are stated as targets
- **New text:** Both thesis acceptance thresholds are met. Replace placeholder targets with actual values:
  - R² = **0.9449** (target ≥ 0.75 ✅)
  - MAE = **2.06 pts** (0–100 scale)
  - RMSE = **3.59 pts**
  - Spearman ρ = **0.9502** (p ≈ 0)
  - 3-class Accuracy = **93.75 %** (target ≥ 80 % ✅)
  - 3-class Macro F1 = **94.15 %**
  - CV R² (5-fold) = 0.9225 → Val R² = 0.9696 → Test R² = 0.9449 (healthy generalisation gap)
  - Best params: `learning_rate=0.1, max_depth=7, max_iter=500, min_samples_leaf=10`
  - Training timestamp: 2026-04-26T18:16:43 UTC
- **Framing note:** R² near 1.0 is expected because labels are a deterministic synthetic function of the input features. State this explicitly: "the figure of merit is the generalisation gap and cross-spot consistency, not the absolute magnitude."
- **Evidence:** `ml/models/model_metadata.json` (written 2026-04-26)

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

☑ **Fill in all metric values** (after evaluation notebooks run)
- **Where:** Chapter 4 tables and inline claims
- **Values (evaluated 2026-04-26, held-out test set):**
  - R² = 0.9449 · MAE = 2.06 · RMSE = 3.59 · Spearman ρ = 0.9502
  - 3-class Accuracy = 93.75 % · Macro F1 = 94.15 %
  - **Per-spot R²:** Hossegor 0.9907 · Ericeira 0.9833 · Gold Coast 0.8370 · Pipeline 0.8248 · Jeffreys Bay 0.7041 ⚠️
  - **Per-season R² (test period = Winter/Spring):** Winter 0.9668 · Spring 0.9163
  - ⚠️ Jeffreys Bay is the only spot below the 0.75 per-spot threshold — note in Ch. 4 as the most directionally sensitive spot (SSW 210°, imputed tide).
- ☐ LLM baseline five-dimension table — still pending (GPT-4o baseline runs complete; table not yet written into thesis)

---

## Appendix

☐ **Data provenance appendix** — copy from `ml/data/DATA_PROVENANCE.md`
- **Action:** The provenance file is written to be dropped directly into the thesis appendix. Copy it in and format it per the document style. Four sources: Open-Meteo Marine, Open-Meteo Archive (weather), tide (NaN / limitation), spot metadata.

---

☐ **Submission commit SHA** — add to appendix after final commit
- **Action:** After tagging `v1.0-submission`, record the git SHA in the thesis appendix reproducibility section.

---

---

## Pre-submission checklist (from `SurfSense_Evaluation_RealLife_Todos.md`)

*Open items from the real-life todos that have a direct thesis or reproducibility impact.*

### Reproducibility & versioning

☐ **Pin exact package versions in `requirements.txt`** before the final training run — pin `scikit-learn`, `shap`, `joblib`, `pandas`, `pyarrow` to exact versions. A breaking sklearn release between training and examiner-download will break the model file.

☐ **Model-versioning convention** — decide: `surf_condition_model.joblib` (single overwritten file) vs. `surf_condition_model_v1_20260501.joblib` (dated). Dated is more defensible for examiners.

☐ **Decide: commit model + parquet files to git or use release assets / manifest?** Model is ~500 KB (fine in git). Parquet files are ~80 K rows — a SHA-256 manifest is usually enough for reviewers; keeps git lean.

☐ **Prompt versioning** — commit `evaluation/llm_baseline/prompt_template.txt`, record its SHA in every eval run file. Any wording edit re-runs the eval; this makes that traceable.

---

### Quality gates (do before writing Chapter 4)

☑ **Feature importance check** — SHAP analysis run 2026-04-26 on 2,000-row sample (seed 42). `skill_level_encoded` = 0.000 — no label leakage. Top features in SHAP order: `wind_dir_sin` (4.06) → `wave_energy_proxy` (3.45) → `wind_wave_interaction` (3.45) → `swell_period` (2.36). Ranking mirrors the weight ordering of the synthetic label formula (wind 25 pts, energy 40 pts, period 20 pts), confirming the model learned the correct physics. `tide_height` = 0.000 as expected (fully imputed, no variance). Add one paragraph to Chapter 4 noting this result.

☐ **Spot-check LLM baseline outputs** — hand-read 5–10 (scenario, system, run) outputs against the automated rubric before locking in the five-dimension table. If the rubric misses obvious safety violations or hallucinations, patch the rubric before the results go into the thesis.

☐ **Cold-read Chapter 4 against files on disk** — before submission, every claim in Chapter 4 must have a corresponding file under `evaluation/` or `ml/figures/`. Any unsupported claim must either be cut or have an artifact generated for it.

---

### Thesis writing tasks

☐ **Draft a glossary / notation list** — SHAP, R², Macro F1, MAE, RMSE, Spearman's ρ, TimeSeriesSplit, Gaussian falloff. Reviewers outside ML will need it; so will the examiner.

☐ **Write figure captions as each figure is generated**, not at the end. One sentence, references the artifact file + date.

☐ **Draft Chapter 4 section headings early** — match them to the figures and tables inventoried in the implementation plan so no figure ends up without a home.

☐ **Line up a proofreader** for the final draft before submission.

---

### Submission and defence prep

☐ **Back up everything redundantly** at least 72 hours before submission: model file, raw data, notebook outputs, git remote, one cold-storage copy (external drive or second cloud).

☐ **Prepare a clean zip of the repo** at the submission SHA — exclude `.env`, raw data dumps, and notebook checkpoints.

☐ **Record a 2–3 minute video demo** of the end-to-end SurfSense flow (including a Scenario 3 ML-scored output). Insurance if the live demo fails on defence day.

☐ **Dry-run the defence presentation** with a timer, at least one week before.

☐ **Prepare a 10-slide backup deck** for anticipated defence questions: "why HGBR not a neural net?", "why only five spots?", "why synthetic labels instead of crowd-sourced?", "why not run the eval over 100 scenarios?". Each question gets one slide.

---

*Append new items below as they arise. Do not delete items; mark them ☑ when done.*
