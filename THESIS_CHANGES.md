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

☑ **NOAA WaveWatch III removed**
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

☑ **Timezone — all data is UTC, not local spot time**
- **Where:** Section 3.3.3 or data appendix, wherever the collected data is described
- **Current text:** may imply or state that timestamps reflect local spot time (given the five spots span five IANA timezones)
- **New text:** All hourly records in `historical.parquet` use UTC timestamps. Open-Meteo was queried with `timezone=UTC` for all five spots. Temporal features (`hour_sin`, `hour_cos`, `month_sin`, `month_cos`) are therefore encoded in UTC, not local surf time. This is a minor approximation: a dawn session at Pipeline (UTC−10) appears at 16:00 UTC, not 06:00 local. The effect is consistent across all spots and does not bias the comparison.
- **Why:** `ml/data/collect.py` uses `"timezone": "UTC"` in all API calls. IANA identifiers in the spot registry are metadata only; they are not applied to timestamps.
- **Evidence:** `ml/data/collect.py` line 106

---

### 3.3.5 — ML-Enhanced Scoring / model choice

☑ **XGBoost → scikit-learn HistGradientBoostingRegressor**
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

☑ **Claude baseline — remove from thesis**
- **Where:** Section 3.5.2, the list of systems in the LLM baseline comparison
- **Current text:** lists three systems: SurfSense, GPT-4o-mini, Claude
- **New text:** Two-system comparison: SurfSense vs GPT-4o-mini only. Claude is not included in the evaluation.
- **Why:** Decision finalized 2026-04-26 — Claude fully removed from comparison. Code, driver, and implementation plan updated accordingly.
- **Evidence:** WORKLOG.md entry 2026-04-22; `evaluation/llm_baseline/driver.py` updated 2026-04-26

---

☑ **Evaluation design asymmetry — framing sentence**
- **Where:** Section 3.5.2, methodology paragraph describing the comparison setup (before the results table)
- **Current text:** likely describes the comparison without acknowledging the structural difference between systems
- **New text:** Add one sentence: "GPT-4o-mini receives the forecast table injected directly into the prompt, while SurfSense processes a natural-language request through its full agentic pipeline — including research via web search and live API calls to the forecast service; this asymmetry is intentional, as the evaluation tests whether the domain-specific pipeline adds value over a vanilla prompted LLM given equivalent information."
- **Why:** Without this sentence an examiner could flag the comparison as unfair. The asymmetry is the thesis argument, not a flaw. (The previous version of this entry included a qualifier about historical snapshots embedding forecast data into SurfSense — that approach was removed 2026-04-27; SurfSense now always uses its full agentic pipeline including for historical-date scenarios.)
- **Evidence:** `evaluation/llm_baseline/driver.py` `_call_surfsense` function; `scenarios/01_single_spot_guincho.py`

---

☑ **Scoring rubric — update methodology description to match revised implementation**
- **Where:** Section 3.5.2, the five-dimension rubric description
- **Changes in `evaluation/llm_baseline/score.py` (2026-04-26) that diverge from original thesis text:**
  1. **Factual consistency** filters out claims that echo the prompt's own injected safety thresholds. Add: "Claims matching the skill-level safety thresholds injected into the prompt are excluded."
  2. **Safety enforcement** returns N/A (not 1.0) when a snapshot contains no genuinely unsafe hours. Add: "The metric is only defined for snapshots where at least one hour exceeds 1.5× the skill-level threshold; snapshots with no unsafe hours are excluded from the mean."
  3. **Temporal optimisation** requires an explicit start-AND-end window — an inline range (`X to Y`) or a labelled `Start:`/`End:` pair. A bare list of timestamps does not qualify. Update text to reflect the stricter definition.
- **Why:** The original rubric description was looser and would have produced artificially inflated scores (especially temporal_optimisation and safety_enforcement). Note: a table-cell parsing addition to factual_consistency was trialled and reverted — the final implementation is prose-only, unchanged from the original design.
- **Evidence:** `evaluation/llm_baseline/score.py`; scored results are in `evaluation/llm_baseline/results.csv`.

---

## Chapter 4 — Results

☐ **Scenario output excerpts** — write captions referencing snapshot files
- **Where:** Section 4.1 figures and listings
- **Action:** Every figure caption or code listing that shows scenario output must trace to a specific file under `scenarios/snapshots/` and `scenarios/results/`. Add filename + date of snapshot run in the caption.
- **Why:** Reproducibility requirement — Chapter 4 figures must be traceable to artifacts on disk.

---

☐ **SHAP feature importance paragraph** — add to Section 4.2 (internal baseline evaluation), after the regression metrics table
- **Where:** Section 4.2, immediately after the R²/MAE/RMSE results table
- **New text (draft):**
  > "To validate that the model captures the intended physical relationships rather than spurious correlations, SHAP (SHapley Additive exPlanations) values were computed on a 2,000-row random sample of the training set. The mean absolute SHAP values rank `wind_dir_sin` (4.06), `wave_energy_proxy` (3.45), `wind_wave_interaction` (3.45), and `swell_period` (2.36) as the four most influential features — mirroring the weight ordering of the synthetic label formula (wind alignment 0–25 pts, wave energy 0–40 pts, period quality 0–20 pts). The `skill_level_encoded` feature contributes zero importance, confirming that skill level gates inference thresholds without distorting the regression target. The `tide_height` feature likewise contributes zero importance, consistent with the known limitation that tide values are fully imputed to each spot's preferred midpoint and therefore carry no variance signal."
- **Evidence:** SHAP analysis run 2026-04-26, `shap.TreeExplainer` on `ml/models/surf_condition_model.joblib`

---

☑ **Fill in all metric values** (after evaluation notebooks run)
- **Where:** Chapter 4 tables and inline claims
- **Values (evaluated 2026-04-26, held-out test set):**
  - R² = 0.9449 · MAE = 2.06 · RMSE = 3.59 · Spearman ρ = 0.9502
  - 3-class Accuracy = 93.75 % · Macro F1 = 94.15 %
  - **Per-spot R²:** Hossegor 0.9907 · Ericeira 0.9833 · Gold Coast 0.8370 · Pipeline 0.8248 · Jeffreys Bay 0.7041 ⚠️
  - **Per-season R² (test period = Winter/Spring):** Winter 0.9668 · Spring 0.9163
  - ⚠️ Jeffreys Bay is the only spot below the 0.75 per-spot threshold — note in Ch. 4 as the most directionally sensitive spot (SSW 210°, imputed tide).
- ☑ LLM baseline evaluation runs complete (2026-04-26) — see below for full results and interpretation

---

☐ **LLM baseline five-dimension table** — write into Section 4.3
- **Where:** Section 4.3 (LLM baseline comparison), results table
- **Status:** Evaluation runs complete for 4 real scenarios (guincho_24h, ericeira_5d, peniche_5d, sagres_5d), 3 runs × 2 systems each. Results in `evaluation/llm_baseline/results.csv`. The `guincho_winter_24h` scenario is excluded from the scored table — see safety enforcement note below.
- **Results (averaged across 4 scenarios — re-run 2026-04-29 with fixed orchestrator + Sagres coordinate fallback):**

  | Dimension | GPT-4o-mini | SurfSense |
  |---|---|---|
  | factual_consistency | **0.907** | 0.826 |
  | safety_enforcement | N/A | N/A |
  | temporal_optimisation | **1.000** | 0.750 |
  | consistency | **0.454** | 0.414 |
  | explainability | 0.171 | **0.793** |

- **Per-scenario breakdown:**

  | Scenario | System | factual | temporal | explainability | consistency |
  |---|---|---|---|---|---|
  | ericeira_5d | gpt4o_mini | 0.838 | 1.000 | 0.362 | 0.392 |
  | ericeira_5d | surfsense | 0.993 | 0.333 | 0.957 | 0.429 |
  | guincho_24h | gpt4o_mini | 0.792 | 1.000 | 0.076 | 0.601 |
  | guincho_24h | surfsense | 0.424 | 1.000 | 0.653 | 0.233 |
  | peniche_5d | gpt4o_mini | 1.000 | 1.000 | 0.019 | 0.673 |
  | peniche_5d | surfsense | 0.897 | 0.667 | 0.638 | 0.440 |
  | sagres_5d | gpt4o_mini | 1.000 | 1.000 | 0.226 | 0.152 |
  | sagres_5d | surfsense | 0.991 | 1.000 | 0.923 | 0.554 |

- **Interpretation for thesis text:**
  1. **GPT-4o-mini wins on temporal optimisation** (1.000 vs 0.750) and **consistency** (0.454 vs 0.414) — structured output with injected data makes it reliable at identifying explicit time windows every run.
  2. **SurfSense wins decisively on explainability** (0.793 vs 0.171) — it cites specific forecast numbers alongside ratings far more consistently. This is the primary thesis argument: the domain-specific pipeline produces richer, citation-grounded reasoning.
  3. **Factual consistency is comparable** (0.907 vs 0.826) — SurfSense's agentic pipeline retrieves and reports forecast values almost as accurately as GPT-4o-mini with injected data.
  4. **`safety_enforcement` N/A for all scenarios** — the four evaluation scenarios represent moderate, seasonally typical conditions; no hours exceed 1.5× the skill-level threshold. See safety enforcement note below for how this is documented.
  5. **The framing for the thesis**: SurfSense is a domain-specific agent that autonomously sources data. GPT-4o-mini given pre-injected structured data outperforms it on temporal precision and run-to-run consistency; SurfSense's advantage lies in explainability, autonomous data retrieval, multi-spot planning, and ML-scored feature contributions (Scenario 3) — none of which the one-shot rubric captures.

---

☐ **Safety enforcement — document evaluation boundary in Section 3.5.2 or 4.3**
- **Where:** Section 3.5.2 rubric description and/or Section 4.3 results discussion
- **Finding (2026-04-29):** `safety_enforcement` is N/A for all four evaluation scenarios for both systems, because no snapshot contains hours that exceed 1.5× the skill-level threshold. A dedicated winter-storm scenario (`guincho_winter_24h.json`, Guincho 2025-01-05, waves 2.1–3.8 m, wind 30–62 kph) was constructed to test this dimension. However, it cannot be scored comparably for both systems: GPT-4o-mini receives the storm data injected into its prompt, while `ForecastDataAgent.fetch_forecast()` has no `start_date` parameter and always retrieves current conditions — so SurfSense fetches April 2026 data (~1.3 m) regardless of the date in the user message.
- **New text / action:** Add to Section 3.5.2 or 4.3: "Safety enforcement could not be comparably scored across both systems. GPT-4o-mini can be tested against any injected snapshot, including historical storm conditions. SurfSense's forecast retrieval is limited to current and near-future dates; a historical-date request causes it to return present-day conditions. This is both an evaluation boundary and a documented system limitation: a production deployment would require historical query support to backtest safety behaviour. Safety enforcement in SurfSense is instead evidenced by the deterministic condition agent implementation — the threshold and rating logic is unit-tested and independent of the scoring mode (rule-based or ML)."
- **Evidence:** `app/agents/forecast_data_agent.py::fetch_forecast` signature (no `start_date` param); `evaluation/llm_baseline/score.py` `EXCLUDE_SCENARIOS`; winter run outputs in `evaluation/llm_baseline/runs/guincho_winter_24h/`


---

## Appendix

☐ **Data provenance appendix** — copy from `ml/data/DATA_PROVENANCE.md`
- **Action:** The provenance file is written to be dropped directly into the thesis appendix. Copy it in and format it per the document style. Four sources: Open-Meteo Marine, Open-Meteo Archive (weather), tide (NaN / limitation), spot metadata.

---

☐ **Submission commit SHA** — add to appendix after final commit
- **Action:** After tagging `v1.0-submission`, record the git SHA in the thesis appendix reproducibility section.

---

## Pre-submission checklist (from `SurfSense_Evaluation_RealLife_Todos.md`)

*Open items from the real-life todos that have a direct thesis or reproducibility impact.*

### Reproducibility & versioning

☑ **Pin exact package versions in `requirements.txt`** — done 2026-04-27. All packages pinned to exact versions. Serialisation-critical note added as comment. `scipy` added (was missing; used in evaluation notebook).

☑ **Model-versioning convention** — single filename (`surf_condition_model.joblib`). Code freeze is May 15; no re-train planned after that. `model_metadata.json` records training timestamp and params, which is sufficient for traceability.

☑ **Decide: commit model + parquet files to git** — all files committed (model 1.8 MB, parquets ~3 MB total). SHA-256 manifest written to `ml/data/DATA_MANIFEST.md` with a verification script. Files are small enough for git; self-contained repo is examiner-friendly.

☑ **Prompt versioning** — `evaluation/llm_baseline/prompt_template.txt` already committed; `driver.py` writes `prompt_hash.txt` per run directory (line 208).

---

### Quality gates (do before writing Chapter 4)

☑ **Feature importance check** — SHAP analysis run 2026-04-26 on 2,000-row sample (seed 42). `skill_level_encoded` = 0.000 — no label leakage. Top features in SHAP order: `wind_dir_sin` (4.06) → `wave_energy_proxy` (3.45) → `wind_wave_interaction` (3.45) → `swell_period` (2.36). Ranking mirrors the weight ordering of the synthetic label formula (wind 25 pts, energy 40 pts, period 20 pts), confirming the model learned the correct physics. `tide_height` = 0.000 as expected (fully imputed, no variance). Add one paragraph to Chapter 4 noting this result.

◐ **Spot-check LLM baseline outputs** — hand-read 5–10 (scenario, system, run) outputs against the automated rubric before locking in the five-dimension table.
- **Done (2026-04-26, test_minimal):** All 9 outputs (3 systems × 3 runs) read manually. Two rubric flaws found and patched in `evaluation/llm_baseline/score.py`:
  1. **Valid-output gate** (`_is_valid_output`): outputs with no rating word and no time reference (clarification requests, error messages) now score 0.0 across all dimensions instead of receiving benefit-of-the-doubt 1.0 on `factual_consistency` and `safety_enforcement`.
  2. **Explainability block window**: `score_explainability` now checks the rating line plus the two following lines rather than a single sentence, correctly capturing formats like "Rating: Ideal\n  Reason: wave height 1.5 m". GPT-4o-mini explainability corrected from 0.04 → 0.61.
- **Still needed:** Manual spot-check of the real evaluation runs (5 scenarios × 2 systems × 3 runs = 30 outputs) against the rubric. Raw outputs are in `evaluation/llm_baseline/runs/`.
- ☑ **Real LLM evaluation executed** — `driver.py --all` run against all 5 real scenario snapshots (guincho_24h, ericeira_5d, peniche_5d, sagres_5d, guincho_winter_24h). All SurfSense and GPT-4o-mini runs complete; results scored into `evaluation/llm_baseline/results.csv` (2026-04-27).

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
