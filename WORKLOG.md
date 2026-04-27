# SurfSense Work Log

Append-only session log. Each entry: date, summary of work done, decisions made, blockers.

---

## 2026-04-22

- Created WORKLOG.md for tracking session-by-session progress.
- Project status: ML integration underway — `app/ml/` added, `app/planning/scoring.py` added, evaluation scaffolding in `evaluation/` and `tests/`.
- Pending work referenced in `SurfSense_Evaluation_RealLife_Todos.md`: real-life evaluation todos, ML baseline comparison, condition agent improvements.
- **Decision — LLM baseline GPT model:** Updated `evaluation/llm_baseline/driver.py` to use the existing Azure OpenAI deployment (`AZURE_OPENAI_*` env vars) for the GPT-4o baseline instead of a plain OpenAI API call. Rationale: the deployment is already configured and version-pinned at the Azure level, matching what the orchestrator uses, so no second API key or separate model string is needed. Todo item "Pin the LLM baseline models" marked done.

---

## 2026-04-22 (continued)

### Section 4: Budget & Cost Control — COMPLETE

- User has university Azure OpenAI account with built-in limits; no additional billing caps needed.
- Kill-switch threshold: inherent in Azure quota.
- **Caching verification:** ✅ PASSED. Ran LLM baseline driver twice on test snapshot:
  - Run 1 (--force): 3 SurfSense calls executed and cached
  - Run 2 (no --force): All [skip] — zero API calls made. Cache working correctly.
- **LLM baseline output status:**
  - SurfSense ✅ — working (uses university Azure account)
  - GPT-4o ✅ — **now working** (added `load_dotenv()` to driver)
  - Claude ❌ — requires anthropic Python package (optional for Phase 1)
  - **Decision:** SurfSense + GPT-4o sufficient for thesis baseline comparison. Claude is optional.

### Config & Integration Fixes

- Fixed settings validation errors: Added `extra="ignore"` to nested settings classes (AzureOpenAISettings, LLMSettings, TavilySettings, ForecastAPISettings, LoggingSettings).
- Fixed `get_llm_provider` import errors in scenario scripts (01, 02, 03) and driver.py — changed to `LLMService.from_settings()`.
- Added `chat_with_tools()` method to LLMService for Orchestrator compatibility.
- Created minimal test snapshot for verification.
- Committed all fixes.

### Pre-Flight Checklist Status (Section 14)

- ✅ Supervisor scope sign-off
- ✅ API keys (Azure OpenAI working)
- ✅ Billing limits (university Azure account)
- ✅ spot_metadata.json with per-spot data
- ⏳ NOAA WW3 testing / Open-Meteo substitution (Section 6)
- ⏳ Dev machine specs verification (Section 7)
- ⏳ Calendar blocking (Section 11)

---

## 2026-04-24

### Chapter 4 Structure — CONFIRMED

- **Decision — Chapter 4 narrative order:** Confirmed with Prof. Jardim. Structure follows general-to-specific:
  1. Scenario walkthroughs (all three, as defined in Section 3.4) — shows the agentic system as a whole.
  2. Internal baseline comparison (ML vs. rule-based) — component performance.
  3. LLM baseline comparison (SurfSense vs. GPT-4o) — component performance.
- All three scenarios included; no cuts. Figures and captions must follow this sequence.
- Todo item "Pre-agree Chapter 4 structure" marked ☑ in `SurfSense_Evaluation_RealLife_Todos.md`.

### Spot Metadata — COMPLETE

- Filled in Gold Coast swell direction (55°–200°, NE to S, estimated from eastern Australian coast geography) in `ml/data/spot_metadata.json`.
- All items in `ml/SPOT_RESEARCH_TRACKER.md` checked off (commit + advisor review still pending).
- Section 5 items and Section 14 pre-flight gate marked ☑ in todos.

---

## 2026-04-26

### Section 6 — Data Source Reconnaissance — COMPLETE

- **Decision — NOAA WW3 dropped.** Open-Meteo Marine API used for all five spots instead. Rationale: simpler REST interface, no auth required, ERA5-backed reanalysis at comparable resolution for open-ocean breaks, full 2-year hindcast coverage confirmed.
- **API verification:** Ran a 7-day test request (marine + weather) for all five spots. All 10 requests returned 192 rows with no errors. Confirmed 2026-04-26.
- **Tide data:** `tide_height_m` left as NaN, imputed to spot preferred midpoint during training. Known limitation documented.
- Created `ml/data/DATA_PROVENANCE.md` covering all four data sources (Open-Meteo Marine, Open-Meteo Archive, tide data, spot metadata). Ready for thesis appendix.
- Sections 6 and 7 pre-flight gates in Section 14 marked ☑.

### Section 7 — Hardware — COMPLETE

- MacBook Pro confirmed sufficient for RAM, disk, and network. No constraints identified.

### Section 11 — Calendar — COMPLETE

- Results chapter (Chapter 4) deadline: 2026-05-22
- Full thesis submission deadline: 2026-07-15
- Available thesis days: Mon, Fri, Sat, Sun (Tue–Thu reserved for company work)
- Coding window: 2026-04-27 (Mon) – 2026-05-15 (Fri) = 10 engineering days
- Code freeze: 2026-05-15 (end of day Friday)
- Writing days: Sat May 16, Sun May 17, Mon May 18, Fri May 22 (4 days for Chapter 4)
- Phase 1 demo day target: Fri May 2 or Mon May 4
- Both weekends (May 2–3, May 9–10) are coding days — no slack
- Section 11 and Section 14 calendar pre-flight gate marked ☑ in todos.

### Pre-Flight Checklist — ALL 7 GATES CLEARED ✓

All items in Section 14 of `SurfSense_Evaluation_RealLife_Todos.md` are now ☑. Phase 1 of the implementation plan is clear to start 2026-04-27.

---

## 2026-04-26 (continued — Phase 1 start)

### Phase 1.1 — Historical Data Collection — COMPLETE

- Completed and ran `ml/data/collect.py` (full 2-year collection, all five spots):
  - Added `sea_surface_temperature` → `water_temp_c` to marine variable list
  - Added 200 ms pacing sleep between marine and weather API requests (fair-use compliance)
  - Added `--force` flag to bypass cached raw files for re-runs
  - Added missing-value summary to end of run output
- **Result:** 87,720 rows in `ml/data/processed/historical.parquet` (17,544 per spot), date range 2024-04-25 → 2026-04-25
- Missing values: `water_temp_c` 1.8% (sparse SST cells in Open-Meteo marine), `tide_height_m` 100% (expected — known limitation, NaN by design)
- Phase 1 demo-day acceptance gate cleared: ≥ 80 K rows ✓, no duplicates on `(spot_id, timestamp)` ✓

### Phase 1 — Label and Split Verification

- Label distribution verified on 500-row sample: min=19.4, max=85.4, mean=37.7, std=13.2. Non-degenerate (82.6% in 20–50 range; no clustering near 0 or 100). EDA quality gate passed.
- Temporal splits verified: train 61,403 rows (Apr 24–Sep 25) / val 13,159 (Sep 25–Jan 26) / test 13,158 (Jan 26–Apr 26) — 70/15/15 ✓

### Blocker Resolved — XGBoost → HistGradientBoostingRegressor

- **Blocker:** `import xgboost` fails at runtime — `libomp.dylib` not found. `brew install libomp` is blocked (work laptop, `/opt` is root-owned, no package manager available). LightGBM has the same dependency.
- **Decision:** Switched ML model to `sklearn.ensemble.HistGradientBoostingRegressor`.
  - Same algorithm class: histogram-based gradient boosted decision trees (identical to XGBoost's default `tree_method='hist'`)
  - `shap.TreeExplainer` confirmed working with HGBR (verified in session)
  - No external runtime dependency — works immediately with the existing venv
  - `surf_model.py` required no changes — it is model-agnostic (loads via joblib, calls `.predict()`)
- **Code changes:**
  - `ml/train.py`: replaced `XGBRegressor` import with `HistGradientBoostingRegressor`; updated `PARAM_GRID` (max_iter / max_depth / learning_rate / min_samples_leaf — 81 combos vs. 324 previously); updated `DEFAULT_PARAMS`
  - `requirements.txt`: removed `xgboost>=2.0.0`
- **Thesis impact:** `THESIS_CHANGES.md` created to track all thesis text changes required. Items logged: NOAA removal, tide limitation, XGBoost→HGBR switch, hyperparameter grid rename, Claude baseline optional, LLM comparison two-system only.

### Next

- Run `python -m ml.train --no-search` (first training pass, ~1 min)
- Verify val R² ≥ 0.75; if so, proceed to runtime integration check (condition_agent.py ML mode + config flag)
- Then run all three scenarios to produce Chapter 4.1 artifacts

---

## 2026-04-26 (continued — model evaluation, LLM baseline, bug fixes)

### Model Training — COMPLETE (run earlier this session)

- `python -m ml.train` completed with full grid search (81 combinations, 5-fold TimeSeriesSplit).
- Best params: `learning_rate=0.1, max_depth=7, max_iter=500, min_samples_leaf=10`
- CV R² = 0.9225 → Val R² = 0.9696 (Val MAE = 1.50, RMSE = 2.50)
- Artifacts written: `ml/models/surf_condition_model.joblib`, `ml/models/imputer.joblib`, `ml/models/model_metadata.json`

### Model Evaluation on Held-Out Test Set

- Evaluated `surf_condition_model.joblib` against the held-out test set (15 %, chronologically most recent, Jan–Apr 2026).
- **Test set metrics:**
  - R² = 0.9449 (thesis target ≥ 0.75 ✅)
  - MAE = 2.06, RMSE = 3.59 (on 0–100 scale)
  - Spearman ρ = 0.9502 (p ≈ 0)
  - 3-class Accuracy = 93.75 % (thesis target ≥ 80 % ✅)
  - 3-class Macro F1 = 94.15 %
- **Per-spot test R²:** Hossegor 0.9907 · Ericeira 0.9833 · Gold Coast 0.8370 · Pipeline 0.8248 · Jeffreys Bay 0.7041 ⚠️ (only spot below 0.75 per-spot)
- **Per-season test R²:** Winter 0.9668 · Spring 0.9163 (test period only covers these two seasons)
- Both thesis acceptance thresholds met. High R² is expected (labels are a deterministic synthetic function of input features) — framing note added to `THESIS_CHANGES.md`.
- `THESIS_CHANGES.md` updated: "Fill in actual model metrics" and "Fill in all metric values" items marked ☑.

### SHAP Feature Importance Check — PASSED

- `shap.TreeExplainer` run on 2,000-row random sample (seed 42) of training set.
- `skill_level_encoded` = 0.000 — no label leakage. Quality gate passed.
- Top SHAP features: `wind_dir_sin` (4.06) → `wave_energy_proxy` (3.45) → `wind_wave_interaction` (3.45) → `swell_period` (2.36). Ranking mirrors synthetic label weight order (wind 25 pts, energy 40 pts, period 20 pts).
- `tide_height` and `tide_is_rising` = 0.000 — expected (fully imputed, no variance).
- Draft SHAP paragraph for Section 4.2 added to `THESIS_CHANGES.md`.

### SurfSense_Evaluation_RealLife_Todos.md — open items captured in THESIS_CHANGES.md

- All remaining ☐ items from `SurfSense_Evaluation_RealLife_Todos.md` with thesis impact added to the "Pre-submission checklist" section of `THESIS_CHANGES.md`. Grouped into: reproducibility & versioning, quality gates, thesis writing tasks, submission and defence prep.

### score.py Rubric — Two Fixes

- **Fix 1 — Valid-output gate (`_is_valid_output`):** Outputs with no rating word (`ideal/suitable/challenging/unsafe`) and no time reference now score 0.0 across all per-run dimensions instead of benefit-of-the-doubt 1.0. Catches clarification requests and error messages.
- **Fix 2 — Explainability block window:** `score_explainability` now checks the rating line plus the two following lines (a 3-line block) rather than a single sentence. Captures formats like "Rating: Ideal\n  Reason: wave height 1.5 m". GPT-4o explainability corrected from 0.04 → 0.61 on test_minimal.
- `python-Levenshtein` installed (was missing from venv, required by `score.py`).
- Spot-check of test_minimal (9 outputs) documented in both `THESIS_CHANGES.md` and `SurfSense_Evaluation_RealLife_Todos.md`.

### research_agent.py — Two Fixes

- **Fix 1 — Query terms:** Changed Tavily search query from `"{query} surf spot conditions break type hazards location coordinates"` to `"{query} surf spot latitude longitude coordinates location break type hazards"`. Including "latitude longitude" in the query causes Tavily to return results that explicitly state coordinates.
- **Fix 2 — Regex coordinate fallback:** Added `_LAT_RE` / `_LON_RE` regex patterns. In `_extract_spot_info`, if the LLM returns null for lat/lon, the raw Tavily result text is scanned with regex as a fallback. Fixes "Could not determine spot coordinates" errors for spots where the LLM fails to extract coordinates from valid search results (reproduced with Sagres Tonel).

### Scenario Scripts — All Three Scenarios Run

- **Scenario 1** (`01_single_spot_guincho.py`): ran successfully after research_agent fix. Wrote `scenarios/snapshots/guincho_24h.json` (24-hour forecast, Praia do Guincho, beginner) and `scenarios/results/scenario_01_rule.json`.
- **Scenario 2** (`02_multi_spot_trip.py`): two bugs fixed before running:
  - `plan_itinerary` call had stale `spot_names=` kwarg — removed (method signature takes `spots_data` dict with names as keys).
  - `spots_data` dict was missing `coordinates` key — added from research data so `plan_itinerary` travel-penalty calculation can use Haversine distances.
  - Wrote `scenarios/snapshots/{ericeira_5d,peniche_5d,sagres_5d}.json` and `scenarios/results/scenario_02_rule.json` (3-spot, 5-day itinerary).
- **Scenario 3** (`03_guincho_ml.py`): ran cleanly, reused `guincho_24h.json` snapshot. Wrote `scenarios/results/scenario_03_ml.json` (ML-scored assessments with feature contributions).

### orchestrator.py — find_surf_windows Mismatch Fixed

- **Bug:** LLM calls `find_surf_windows(spot_name=…, min_hours=…)`. Orchestrator's `_enrich_args` injected `assessments` from session data but left `spot_name` in the args dict. `find_surf_windows(assessments, min_hours)` does not accept `spot_name` → `TypeError` in some SurfSense runs during LLM baseline evaluation.
- **Fix:** Added `args.pop("spot_name", None)` after the assessments injection in `_enrich_args`.

### LLM Baseline Evaluation — COMPLETE

- `driver.py --all` run against all 4 real scenario snapshots (guincho_24h, ericeira_5d, peniche_5d, sagres_5d) + test_minimal. Claude errors with auth error (no API key — expected). All SurfSense and GPT-4o runs completed.
- Re-run with `--force` after `find_surf_windows` fix to give SurfSense clean runs.
- **Final results (averaged across 4 real scenarios, post-fix):**

  | Dimension | GPT-4o | SurfSense |
  |---|---|---|
  | safety_enforcement | **1.000** | 0.417 |
  | temporal_optimisation | **1.000** | 0.417 |
  | consistency | **0.704** | 0.230 |
  | factual_consistency | **0.405** | 0.347 |
  | explainability | 0.126 | **0.201** |

- Key finding: GPT-4o wins on structured-output metrics (data injected directly); SurfSense wins on explainability. SurfSense consistency is low (0.23) because each run takes a different agentic tool-call path. Sagres scored 0.0 for SurfSense — orchestrator could not resolve the spot in one-shot format.
- Full interpretation (6 points) and per-scenario breakdown added to `THESIS_CHANGES.md`.
- Evaluation design asymmetry note added to `THESIS_CHANGES.md` Section 3.5.2: the comparison is intentionally asymmetric (GPT-4o gets data injected; SurfSense fetches it agentically) and needs one framing sentence in the thesis to pre-empt examiner questions.

### score.py Rubric — Revision 2 (2026-04-26)

Four additional fixes on top of the valid-output gate and explainability block window from earlier this session:

- **Fix 3 — Markdown table claim extraction (`_extract_table_claims`):** `score_factual_consistency` previously only parsed prose claims (`1.5 m`, `12 kph`). GPT-4o outputs data in markdown tables whose cells have no unit suffix, so the old scorer evaluated almost entirely on the prose paragraph at the end — which often echoed the prompt's injected thresholds. New `_extract_table_claims` reads column headers for units (`Wave Height (m)`, `Wind Speed (kph)`) and extracts numeric cells from data rows. `swell.height_m` also added to `_forecast_numbers` (was missing).
- **Fix 4 — Threshold-echo filter (`_is_threshold_echo`):** `score_factual_consistency` now strips claims that match the safety thresholds injected into the prompt itself (e.g. 3.75 m / 30 kph for intermediate). Echoing the prompt's own numbers is not a factual claim about the forecast and was artificially inflating GPT-4o's factual score.
- **Fix 5 — `score_safety_enforcement` returns `None` for N/A cases:** Previously returned `1.0` when the snapshot contained no genuinely unsafe hours, which trivially passed any output. Now returns `None` (rendered as "N/A" in CSV). `_safe_mean` helper added to exclude `None` from cross-scenario means. `_format_score` helper added for consistent CSV rendering.
- **Fix 6 — Strict window requirement in `score_temporal_optimisation`:** Previously returned `1.0` for any output containing two or more timestamps (e.g., a copied forecast table). Now requires either an inline range (`X to Y`, `X - Y`, `X–Y`) or a labelled pair (`Start: …` / `End: …` within 5 lines). A bare timestamp list no longer qualifies.
- **`score_all` now takes `skill_level` parameter** and passes it through to the per-dimension scorers.
- **Results.csv should be regenerated** after these rubric changes — run `python -m evaluation.llm_baseline.score` to update.

### Files Changed This Session

| File | Change |
|---|---|
| `app/agents/research_agent.py` | Tavily query fix + regex lat/lon fallback |
| `app/agents/orchestrator.py` | `find_surf_windows` `spot_name` kwarg stripped in `_enrich_args` |
| `evaluation/llm_baseline/score.py` | Rubric revision: markdown table claims, threshold-echo filter, None safety, strict window, skill_level param |
| `scenarios/02_multi_spot_trip.py` | Removed stale `spot_names` kwarg; added `coordinates` to spot data |
| `scenarios/snapshots/guincho_24h.json` | Created (Scenario 1 output) |
| `scenarios/snapshots/ericeira_5d.json` | Created (Scenario 2 output) |
| `scenarios/snapshots/peniche_5d.json` | Created (Scenario 2 output) |
| `scenarios/snapshots/sagres_5d.json` | Created (Scenario 2 output) |
| `scenarios/results/scenario_01_rule.json` | Created |
| `scenarios/results/scenario_02_rule.json` | Created |
| `scenarios/results/scenario_03_ml.json` | Created |
| `evaluation/llm_baseline/runs/` | All SurfSense + GPT-4o run outputs (4 scenarios × 2 systems × 3 runs) |
| `evaluation/llm_baseline/results.csv` | Final scored results |
| `ml/models/surf_condition_model.joblib` | Trained HGBR model |
| `ml/models/imputer.joblib` | Fitted SimpleImputer |
| `ml/models/model_metadata.json` | Training metrics and best params |
| `THESIS_CHANGES.md` | Major updates throughout — metrics, SHAP, LLM results, todos |
| `SurfSense_Evaluation_RealLife_Todos.md` | Spot-check item updated to ◐ |
| `WORKLOG.md` | This entry |

---

## 2026-04-27

### Phase 1.2.5 — EDA Notebook — COMPLETE

- Created `ml/notebooks/01_eda.ipynb` per Phase 1.2.5 spec.
- All acceptance criteria met:
  - ≥ 80 K rows verified (87,720) ✅
  - Missing-value audit: `tide_height_m` 100 % (expected), `water_temp_c` 1.78 % ✅
  - Per-spot (balanced, 17,544 each) and per-season counts documented ✅
  - Label distribution: mean 37 ± 13, no extremes — formula not degenerate ✅
  - Feature distributions, correlation heatmap, target-vs-feature scatter (top 6) ✅
  - All figures saved to `ml/figures/eda/` ✅
  - Each figure has a short prose explanation in the notebook ✅
- Implementation plan Section 2.5 and RealLife Todos Section 7 Jupyter item marked ☑.

### Chapter 4 — Where to find what (writing reference)

When writing Chapter 4, pull content from these locations in order:

**4.1 — Scenario walkthroughs (agentic system as a whole)**
- Scenario 1 (single spot, 24h): `scenarios/results/scenario_01_rule.json`, snapshot `scenarios/snapshots/guincho_24h.json`
- Scenario 2 (multi-spot, 5-day trip): `scenarios/results/scenario_02_rule.json`, snapshots `ericeira_5d / peniche_5d / sagres_5d`
- Scenario 3 (ML-scored): `scenarios/results/scenario_03_ml.json`, reuses `guincho_24h.json` snapshot
- Raw LLM run outputs: `evaluation/llm_baseline/runs/` (per scenario / system / run)

**4.2 — Internal baseline comparison (ML vs. rule-based)**
- Model metrics: `ml/models/model_metadata.json` (R², MAE, RMSE, Spearman ρ, accuracy, F1, per-spot and per-season breakdown)
- SHAP importance paragraph: drafted in `THESIS_CHANGES.md` (search "SHAP paragraph")
- EDA figures for data description: `ml/figures/eda/` — use `label_distribution.png` and `feature_distributions.png`

**4.3 — LLM baseline comparison (SurfSense vs. GPT-4o)**
- Final scored table: `evaluation/llm_baseline/results.csv`
- EDA visuals of those results: `evaluation/llm_baseline/eda.ipynb` (figures inline)
- Interpretation and framing: `THESIS_CHANGES.md` (search "LLM baseline results interpretation")
- Evaluation design asymmetry note (GPT-4o data injected vs. SurfSense agentic): `THESIS_CHANGES.md` Section 3.5.2

**Supporting references throughout Chapter 4**
- `THESIS_CHANGES.md` — all metric fill-ins, framing notes, and open writing tasks collected here
- `SurfSense_Evaluation_RealLife_Todos.md` Section 9 — quality gate results (spot-check findings)
- `ml/data/DATA_PROVENANCE.md` — data source attribution for any methodology callbacks


---

### 2026-04-27

**LLM baseline evaluation — real scenarios scored, safety enforcement fixed.**

- Generated `ml/data/processed/train.parquet`, `val.parquet`, `test.parquet` via `python -m ml.splits`.
- Created and executed `ml/notebooks/03_evaluation.ipynb` — produced all 11 `ml/figures/*.png` and `evaluation/baseline_vs_ml.csv`. ML wins on all three metric groups (R²=0.9449, Accuracy=0.9397, Spearman=0.9502).
- Scored all real LLM baseline scenarios into `evaluation/llm_baseline/results.csv` (guincho_24h, ericeira_5d, peniche_5d, sagres_5d).
- Found bug: `_load_snapshot` in `score.py` matched `guincho_winter_24h.json` when resolving `guincho_24h` due to prefix match. Fixed to prefer exact stem match first.
- **Winter safety scenario:** The original snapshots contain no unsafe hours for beginners, making `safety_enforcement` N/A across all scenarios. Fetched Open-Meteo historical data for Guincho on 2025-01-05 (Atlantic winter storm: waves 2.4–3.8m, wind 25–43 kph — all 24 hours unsafe for beginners). Saved as `scenarios/snapshots/guincho_winter_24h.json`.
- Modified `driver.py::_call_surfsense` to: (1) embed forecast table for historical snapshots so the orchestrator does not ask for dates; (2) include the date range from snapshot timestamps for live snapshots.
- Re-ran driver on `guincho_winter_24h` with `--force`. SurfSense scored **1.0** safety enforcement (24/24 unsafe hours flagged), GPT-4o scored **0.63**.
- Updated `evaluation/llm_baseline/results.csv` with winter scenario (60 rows total across 5 real scenarios).

## 2026-04-27
- Repo cleanup: removed all stale / superseded files.
- Deleted `DEPRECATED_github_issues.md` (referenced old Phi-3 architecture, never relevant to current build).
- Deleted `app/forecasting/noaa_client.py` and `TestNOAAConnection` from `tests/test_api_connections.py` — NOAA WW3 was already a closed decision; file was dead code.
- Deleted all `evaluation/llm_baseline/runs/*/claude/` directories — Claude was dropped from the LLM comparison (two-system evaluation: SurfSense vs GPT-4o only).
- Deleted `evaluation/llm_baseline/runs/test_minimal/` and `scenarios/snapshots/test_minimal.json` — development/smoke-test artifacts, not real evaluation scenarios. Removed corresponding rows from `results.csv`.
- Deleted `ml/notebooks/03_evaluation_executed.ipynb` — redundant executed copy of `03_evaluation.ipynb`; clean version is authoritative.

## 2026-04-27 (continued — reproducibility housekeeping)

- Confirmed prerequisite fix (Section 1 of implementation plan) was already done: `forecast_data_agent.py` already tries Open-Meteo first, Stormglass as fallback. Two path-coverage tests already in `test_forecast_data_agent.py` (both passing). Marked ☑ in plan.
- Confirmed `evaluation/llm_baseline/prompt_template.txt` already committed and SHA already written per run via `driver.py:208`. Prompt versioning item marked ☑.
- Pinned all packages to exact versions in `requirements.txt` (2026-04-27). Added `scipy==1.16.3` (was missing; used in `03_evaluation.ipynb`). Added serialisation-critical comment for `scikit-learn` and `joblib`.
- **Decision — model versioning:** Single filename `surf_condition_model.joblib`. Code freeze May 15; no re-train planned. `model_metadata.json` records training timestamp, params, and CV scores — sufficient traceability.
- **Decision — data/model files in git:** All committed. Model 1.8 MB, parquets ~3 MB total — well within git limits. SHA-256 manifest written to `ml/data/DATA_MANIFEST.md` with row counts and a verification script.
- All four reproducibility checklist items marked ☑ in `THESIS_CHANGES.md` and `SurfSense_Evaluation_RealLife_Todos.md`.
- 128/128 tests passing.
