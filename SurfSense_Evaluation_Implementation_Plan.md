# SurfSense: Implementation Plan to Reach the Methodology State

**Author:** Joshua Wehr
**Scope:** Close the gap between the current repository and Sections 3.3.5, 3.4, and 3.5 of the thesis so that the evaluation described in Chapter 3 can actually be executed and reported in Chapter 4.
**Status legend:** ☐ not started · ◐ partial · ☑ done

---

## 0. Context and Critical Path

The repository currently implements Sections 3.3.1 through 3.3.4 of the methodology: orchestrator, research agent, forecast data agent (Open-Meteo + Stormglass), rule-based condition assessment, and Haversine-based trip planning. What is missing is everything in Section 3.3.5 (ML-Enhanced Scoring) plus the two evaluation harnesses described in Sections 3.5.1 and 3.5.2, plus the scripted demonstration scenarios in Section 3.4.

The dependency order that minimises rework:

```
Phase 1 (data + labels + features)
        │
        ▼
Phase 2 (model training)
        │
        ▼
Phase 3 (runtime integration, SHAP surfacing, config flag)
        │
        ├─────────────► Phase 4 (scripted demonstration scenarios)
        │                                │
        ▼                                ▼
Phase 5 (internal baseline eval)   Phase 6 (LLM baseline eval)
        │                                │
        └────────────────┬───────────────┘
                         ▼
                Phase 7 (Chapter 4 figures and tables)
```

Phases 1, 2, 3 are the blocking path for Scenario 3 and for both evaluation tracks. Phases 4, 5, 6 can be parallelised once Phase 3 is merged. Phase 7 is a write-up phase over artifacts produced earlier.

---

## 1. One Prerequisite Fix (Consistency with Thesis Text)

☐ **Reconcile Stormglass vs. Open-Meteo priority.** Section 3.3.3 of the thesis states Open-Meteo is the default and Stormglass is the fallback. The current `app/agents/forecast_data_agent.py::fetch_forecast` tries Stormglass first when its key is configured and only falls through to Open-Meteo on `StormglassAPIError`. Either flip the order in code, or adjust the thesis sentence. Recommendation: flip the code, because Open-Meteo is keyless and cheaper, and the thesis already commits to it as the default.

Acceptance: with both keys configured, a forecast call hits Open-Meteo first; a forced Open-Meteo failure falls through to Stormglass; both paths covered by a test.

---

## 2. Phase 1: ML Foundations (Data, Labels, Features)

Thesis anchor: Section 3.3.5, "Training data" and "Features and model" paragraphs.

### 2.1 Historical data pipeline

☐ Create `ml/data/collect.py` that downloads hourly records for at least five geographically diverse spots: Pipeline (Hawaii), Hossegor (France), Ericeira (Portugal), Jeffreys Bay (South Africa), Gold Coast (Australia). The methodology names exactly these.

Sources, per the thesis:

* **Open-Meteo Historical Weather API** for wind, weather, tide. Free, no key, covers back to 1940.
* **NOAA WaveWatch III hindcasts** for wave height, period, direction. Free bulk download, global coverage.

Tasks:

1. Define a `SpotMeta` registry with lat/lon/timezone/name for the five spots.
2. Pull at least two years of hourly data per spot. Two years gives enough temporal range that the last three months (test set) still have roughly the same seasonal distribution as training.
3. Write raw results to `ml/data/raw/{spot_id}_{source}_{yyyymm}.parquet`. Parquet over CSV because the data is tabular, numeric, and large enough that CSV load times become annoying.
4. Merge wave (NOAA) and weather (Open-Meteo) on `timestamp + spot_id`, producing `ml/data/processed/historical.parquet` with the schema below.

**Target row schema (per hour, per spot):**

```
spot_id, timestamp, lat, lon,
wave_height_m, wave_period_s, wave_direction_deg,
swell_height_m, swell_period_s, swell_direction_deg,
wind_speed_kph, wind_gust_kph, wind_direction_deg,
tide_height_m,
water_temp_c, air_temp_c
```

Acceptance:

* `≥ 80,000` rows in `historical.parquet` across the five spots combined.
* No duplicates on `(spot_id, timestamp)`.
* Missing-value rate per column documented in the EDA notebook.
* Script is idempotent (running twice does not double-count).

### 2.2 Synthetic label generator (independent of the rule-based heuristic)

☐ Create `ml/labels.py` containing a `compute_synthetic_score(row)` function that returns a 0–100 quality score derived from coastal-physics rules, not from the `ConditionAssessor` heuristic.

This matters because Section 3.5.1 explicitly warns: "The XGBoost model therefore learns to approximate the heuristic, not an independent surfability measure." If the label is the same formula the baseline uses, R² will trivially approach 1.0 and the comparison becomes meaningless. The Scarfe et al. (2009) paper you already cite as domain background is the correct anchor.

Recommended labelling rule (physics-grounded, different structure from the rule-based formula):

1. **Wave energy:** `E ∝ swell_height² × swell_period`, normalised to a 0–40 subscore.
2. **Offshore-wind alignment:** cosine of the angle between wind direction and the inverse of the swell-facing coast (spot-specific), scaled to 0–25, penalised for wind speed above 25 kph.
3. **Tidal suitability:** per-spot preferred tide band; Gaussian falloff from the preferred tide height to 0–15.
4. **Period quality:** monotonic reward for `swell_period ≥ 10 s`, maxing at 14 s, worth 0–20.
5. Sum, clip to `[0, 100]`.

The weights above are deliberately different from the `40/30/20/10` weighting in the rule-based scorer, so the ML model has a real target to learn that the heuristic cannot perfectly reproduce.

Acceptance:

* Function is pure, deterministic, documented with references to the physical relationships.
* Label distribution histogram shown in EDA notebook (avoid a degenerate target concentrated at 0 or 100).
* Labels computed and stored as an extra column `surf_quality_score` in `ml/data/processed/historical.parquet`.

### 2.3 Shared feature extractor

☐ Create `app/ml/feature_extractor.py` with a `ForecastPointFeatureExtractor` class that produces the same feature vector from (a) a historical dataframe row at training time and (b) a live `ForecastPoint` at inference time. This is the "train/serve consistency contract" the methodology talks about.

Feature list, approximately 28 features:

```
wave_height_min, wave_height_max, wave_height_avg,
swell_height, swell_period,
swell_dir_sin, swell_dir_cos,
wind_speed, wind_gust,
wind_dir_sin, wind_dir_cos,
is_offshore, is_light_wind,
tide_height, tide_is_rising,
wave_energy_proxy,        # swell_height² × swell_period
wind_wave_interaction,    # wind_speed × cos(wind_dir - swell_dir)
swell_wind_ratio,         # swell_period / max(wind_speed, 1)
hour_sin, hour_cos,
month_sin, month_cos,
day_of_week,
water_temp, air_temp,
skill_level_encoded       # 0=beginner, 1=intermediate, 2=advanced, 3=expert
```

Tasks:

1. Define the feature list once as a module-level constant, so training and inference cannot silently drift.
2. Implement `transform_row(pd.Series) -> np.ndarray` for training.
3. Implement `transform_point(ForecastPoint, skill_level: str) -> np.ndarray` for inference.
4. Write a contract test that feeds synthetic data through both paths and asserts vector equality.
5. Handle missing values: median imputation for numeric, 0 for binary flags, with the imputer fit on training data only and persisted alongside the model.

Acceptance:

* Single source of truth for the feature list.
* `tests/test_feature_extractor.py` verifies both code paths produce identical vectors on the same logical input.
* No feature computed in training is absent at inference, and vice versa.

### 2.4 Temporal train/val/test split

☐ Implement the 70/15/15 split in `ml/splits.py`, split by time rather than at random. Test set = most recent three months across all spots. Validation = the three months before that. Training = everything prior.

Acceptance:

* `train.parquet`, `val.parquet`, `test.parquet` in `ml/data/processed/`.
* No timestamp appears in more than one split.
* Per-spot coverage reported in the EDA notebook.

### 2.5 EDA notebook

☐ `ml/notebooks/01_eda.ipynb`: distribution plots per feature, correlation heatmap, target-vs-feature scatter for top candidates, missing-value matrix, per-spot and per-season sample counts.

Acceptance: notebook runs top-to-bottom with fixed seed, writes figures to `ml/figures/eda/`.

---

## 3. Phase 2: Model Training

Thesis anchor: Section 3.3.5, "Features and model" paragraph.

### 3.1 Training script

☐ Create `ml/train.py` and `ml/notebooks/02_training.ipynb` implementing:

1. **Model:** XGBoost regressor (primary). LightGBM as a smoke-comparison is optional; the thesis commits to XGBoost.
2. **Cross-validation:** 5-fold, `TimeSeriesSplit` (time-aware, not random).
3. **Hyperparameter grid:**

   ```python
   {
     "n_estimators": [100, 300, 500],
     "max_depth": [4, 6, 8],
     "learning_rate": [0.01, 0.05, 0.1],
     "subsample": [0.8, 1.0],
     "colsample_bytree": [0.8, 1.0],
     "min_child_weight": [1, 3, 5],
   }
   ```
4. **Fixed seed** (42) for reproducibility.
5. **Serialisation:** `ml/models/surf_condition_model.joblib` plus `ml/models/model_metadata.json` containing hyperparameters, CV scores, training timestamp, dataset hash, feature list, and imputer state.

### 3.2 Dependencies

☐ Add to `requirements.txt`:

```
xgboost>=2.0.0
scikit-learn>=1.3.0
shap>=0.44.0
joblib>=1.3.0
pandas>=2.1.0
pyarrow>=14.0.0        # parquet
matplotlib>=3.8.0
seaborn>=0.13.0
jupyter>=1.0.0
```

Acceptance:

* `make install` still succeeds on a clean venv.
* `python -m ml.train` produces the serialised model and a `train_report.json` with CV metrics.
* Model R² on the validation set is reported (target per 3.5.3: ≥ 0.75 on test; val should be at least that).

### 3.3 SHAP precomputation helper

☐ Add a `ml/explain.py` with `explain(model, X) -> shap_values` wrapping `shap.TreeExplainer`. Tree-based SHAP is exact and runs in milliseconds, so it can be called at inference time without caching. The methodology explicitly requires per-prediction feature contributions, not post-hoc approximations.

---

## 4. Phase 3: Runtime Integration

Thesis anchor: Section 3.3.5 "Explainability" and "machine-learning component replaces the rule-based composite score."

### 4.1 SurfConditionModel inference wrapper

☐ Create `app/ml/surf_model.py`:

```python
class SurfConditionModel:
    def __init__(self, model_path: str): ...
    def predict(self, forecast: ForecastPoint, skill_level: str) -> float: ...
    def predict_batch(self, forecasts: list[ForecastPoint], skill_level: str) -> list[float]: ...
    def get_feature_contributions(self, forecast: ForecastPoint, skill_level: str) -> dict[str, float]: ...
```

Loads the model and imputer on instantiation, logs `model_version` from metadata on startup.

### 4.2 Config flag

☐ Extend `config/settings.py` with:

```python
class ScoringSettings(BaseModel):
    mode: Literal["rule", "ml"] = "rule"
    model_path: str = "ml/models/surf_condition_model.joblib"
```

Expose as `SCORING_MODE` and `ML_MODEL_PATH` env vars in `.env.example`.

### 4.3 Refactor ConditionAssessmentAgent

☐ Change `app/agents/condition_agent.py::assess_conditions` so that:

1. The four-category rating mapping, the 1.5× unsafe cutoff, the `safety_warnings` list, and the `reasoning` text **remain deterministic**. The thesis is explicit about this: "All safety logic, including threshold enforcement, rating derivation, and warning generation, remains deterministic."
2. Only the 0–100 score is delegated:

   ```python
   if self._mode == "ml":
       score = self._model.predict(forecast_point, skill_level)
       contributions = self._model.get_feature_contributions(forecast_point, skill_level)
   else:
       score = _rule_based_score(forecast_point, thresholds)  # existing formula
       contributions = None
   ```
3. Attach `contributions` to each per-hour assessment dict when present.

Acceptance:

* Existing rule-based unit tests still pass with `SCORING_MODE=rule`.
* A new `tests/test_condition_agent_ml.py` verifies: model loads, per-hour output includes `feature_contributions`, ratings still follow the 70/45/1.5× rules regardless of scoring mode.

### 4.4 Surface SHAP to the orchestrator

☐ Update the orchestrator system prompt in `app/agents/orchestrator.py` to include a rule like:

> When an assessment includes `feature_contributions`, identify the top positive and top negative contributor and mention them in plain language (e.g., "long swell period was the main positive factor; onshore wind reduced the score"). Do not list raw SHAP values.

Success criterion 4 in 3.5.3 ("every ML-scored prediction includes SHAP-derived feature contributions") is satisfied by 4.3; this step makes them user-visible.

---

## 5. Phase 4: Scripted Demonstration Scenarios

Thesis anchor: Section 3.4. The three scenarios described there need to be reproducible, pinned to specific forecast snapshots so that Chapter 4 figures do not drift with real weather.

### 5.1 Forecast snapshotting

☐ Extend `ForecastDataAgent.fetch_forecast` with an optional `snapshot_path` parameter. When set, the agent writes the normalised forecast dict to disk before returning. When the path exists, the agent reads from it instead of calling the API. This turns scenario runs into deterministic, replayable artifacts.

### 5.2 Three scenario scripts

☐ Create `scenarios/01_single_spot_guincho.py`

* Inputs: spot = Praia do Guincho, skill = beginner, horizon = 24 h, scoring = rule.
* Flow: `research_spot` → `fetch_forecast(snapshot_path="scenarios/snapshots/guincho_24h.json")` → `assess_conditions`.
* Output: `scenarios/results/scenario_01_rule.json` with the 24 hourly records.

☐ Create `scenarios/02_multi_spot_trip.py`

* Inputs: spots = Ericeira, Peniche/Supertubos, Sagres/Tonel; skill = intermediate; horizon = 5 days; scoring = rule.
* Flow: research each spot, fetch forecasts (snapshotted), assess, `plan_itinerary`.
* Output: `scenarios/results/scenario_02_rule.json` with itinerary plus per-spot window lists.

☐ Create `scenarios/03_guincho_ml.py`

* Inputs: identical to Scenario 1 but `SCORING_MODE=ml`. Reuses `scenarios/snapshots/guincho_24h.json` so inputs are byte-identical.
* Output: `scenarios/results/scenario_03_ml.json`, each record including `feature_contributions`.

Acceptance per 3.4:

* All three scripts exit 0 on live forecast data.
* Output JSON conforms to the documented schema (timestamp, score, rating, reasoning, warnings).
* Scenario 3 records contain non-empty `feature_contributions`.

---

## 6. Phase 5: Internal Baseline Evaluation (3.5.1)

Thesis anchor: Section 3.5.1, "regression, classification, ranking" blocks plus per-spot and per-season breakdowns.

### 6.1 Evaluation notebook

☐ `ml/notebooks/03_evaluation.ipynb` implementing:

1. Load `test.parquet`.
2. Compute **rule-based scores** by running the existing scoring formula row-by-row. Factor the formula out of `ConditionAssessmentAgent` into `app/planning/scoring.py::rule_based_score(...)` so it can be imported without dragging the whole agent stack.
3. Compute **ML scores** via `SurfConditionModel.predict_batch`.
4. Compute the three metric groups against the synthetic target:

   | Group          | Metrics                                         |
   | -------------- | ----------------------------------------------- |
   | Regression     | MAE, RMSE, R²                                   |
   | Classification | Accuracy, macro F1 over the four rating classes |
   | Ranking        | Spearman's ρ                                    |
5. Per-spot and per-season breakdowns of all three groups.
6. Confusion matrix (predicted vs. labelled rating), applied to both systems.
7. SHAP summary (beeswarm) and top-3 dependence plots on the trained model.

### 6.2 Output artifacts

☐ Write the following to disk:

* `evaluation/baseline_vs_ml.csv`: one row per (metric, system, split-slice).
* `ml/figures/{feature_importance,shap_beeswarm,shap_dep_1..3,confusion_rule,confusion_ml,scatter_pred_actual,per_spot_accuracy,per_season_accuracy,score_distribution}.png` at 300 DPI.

Acceptance per 3.5.3:

* ML R² ≥ 0.75 on the test set.
* ML classification accuracy ≥ 80%.
* ML beats rule-based on at least two of the three metric groups.

If any of these fail, the thesis discussion in Chapter 4 has to explain why. With the independent synthetic label from 2.2, failure would most likely come from underfitting (more trees or deeper trees) or insufficient data coverage per spot; both are diagnosable from the per-spot breakdown.

---

## 7. Phase 6: LLM Baseline Comparison (3.5.2)

Thesis anchor: Section 3.5.2, five dimensions: factual consistency, safety enforcement, temporal optimisation, consistency across runs, explainability.

### 7.1 Driver

☐ Create `evaluation/llm_baseline/driver.py` that:

1. Loads a scenario snapshot (`scenarios/snapshots/*.json`) plus the scenario's skill level and user request text.
2. Formats a plain-text prompt embedding the full forecast table (ASCII, hourly rows) plus the request ("You are helping an intermediate surfer pick the best window at Praia do Guincho over the next 24 hours. List each hour's rating and explain your reasoning.").
3. Sends the prompt to two systems, three times each:

   * **SurfSense** via `Orchestrator.process(...)`.
   * **ChatGPT** via `openai.ChatCompletion` (GPT-4o, temperature 0.7 to match SurfSense).
4. Persists six outputs per scenario at `evaluation/llm_baseline/runs/{scenario}/{system}_{run_idx}.txt`.

### 7.2 Scoring rubric

☐ Create `evaluation/llm_baseline/score.py` implementing the five dimensions of 3.5.2:

1. **Factual consistency.** Parse numerical claims from the output (regex over `\d+(\.\d+)?\s*(m|ft|kph|km/h|s)`), match to the corresponding forecast value by timestamp, flag any claim off by more than 10 %. Also check that any rating word (`ideal|suitable|challenging|unsafe`) is consistent with the thresholds given the claimed numbers.
2. **Safety enforcement.** For every hour in the snapshot where `wave_height > 1.5 × threshold` or `wind_speed > 1.5 × threshold`, verify the output contains an `unsafe` flag for that hour (or warns about it explicitly). Binary per hour.
3. **Temporal optimisation.** Boolean: does the output contain at least one time window with explicit start/end? For Scenario 2, additionally: does it mention inter-spot travel times?
4. **Consistency.** Compute a normalised edit distance between the three runs per system. Report mean pairwise similarity.
5. **Explainability.** Count the proportion of rating statements that reference at least one specific numerical forecast value from the snapshot.

Each dimension yields a scalar per (scenario, system). Aggregate to a table.

### 7.3 Output

☐ `evaluation/llm_baseline/results.csv`: columns `scenario, system, dimension, score, run_1, run_2, run_3`.

Acceptance per 3.5.3:

* SurfSense has higher factual consistency than both LLM baselines across all three scenarios.
* SurfSense has complete (100 %) safety enforcement across all three scenarios.

The thesis is explicit that this is a descriptive evaluation, not a controlled experiment, so no statistical inference is required.

### 7.4 Extra dependencies

(`openai` is already present. No additional dependencies required — Claude is not part of the comparison.)

☐ Extend `config/settings.py` with optional `OPENAI_API_KEY` field, and mirror into `.env.example`.

---

## 8. Phase 7: Chapter 4 Reporting

At this point, every figure and table that Chapter 4 needs should exist on disk. The writing phase is then a matter of narrating them.

### 8.1 Figures inventory (already produced by earlier phases)

* `ml/figures/feature_importance.png`
* `ml/figures/shap_beeswarm.png`
* `ml/figures/shap_dep_{1,2,3}.png`
* `ml/figures/confusion_{rule,ml}.png`
* `ml/figures/scatter_pred_actual.png`
* `ml/figures/per_spot_accuracy.png`
* `ml/figures/per_season_accuracy.png`
* `ml/figures/score_distribution.png`

### 8.2 Tables inventory

* `evaluation/baseline_vs_ml.csv` → thesis Table in 4.x comparing rule-based vs. ML across the three metric groups, plus breakdowns.
* `evaluation/llm_baseline/results.csv` → thesis Table in 4.x for the five-dimension LLM comparison, one row per (scenario, system) pair.

### 8.3 Scenario outputs

* `scenarios/results/scenario_{01,02,03}_*.json` → referenced directly in 4.x, with short excerpts formatted as code listings or tables.

---

## 9. Test and Tooling Updates

☐ `tests/test_feature_extractor.py`: train/serve consistency contract.
☐ `tests/test_condition_agent_ml.py`: mode switching, SHAP attachment, rating logic unchanged.
☐ `tests/test_synthetic_labels.py`: label function is pure, bounded 0–100, non-degenerate distribution on a sample.
☐ `tests/test_snapshot_replay.py`: fetching with `snapshot_path` produces identical dicts on replay.
☐ Extend `make` targets: `make train`, `make eval-ml`, `make eval-llm`, `make scenarios`, `make figures`.

---

## 10. Open Risks and Mitigations

1. **Synthetic label risk.** If the ML label is too close to the rule-based formula, the comparison is uninteresting. Mitigation: label uses a different structural form (multiplicative wave energy, Gaussian tidal falloff, spot-specific offshore direction) and different weightings from the rule-based scorer. Keep the two formulations in separate modules.
2. **NOAA WaveWatch III download size and complexity.** WW3 GRIB files are large and not all spots sit cleanly on the grid. Mitigation: use the NOAA ERDDAP interface where available for point queries, or fall back to Open-Meteo marine hindcasts (`wave_height`, `wave_period` variables) for spots where WW3 is awkward; document the substitution in the thesis data-provenance note.
3. **API quota during LLM baseline runs.** Three runs × three systems × three scenarios is tractable, but rate limits and cost still apply. Mitigation: cache every LLM response to disk immediately; never re-query if a run file exists unless explicitly `--force`.
4. **ChatGPT prompt sensitivity.** Small wording changes can shift the comparison. Mitigation: write the prompt once, version it in `evaluation/llm_baseline/prompt_template.txt`, and reference the hash of the prompt in every output file.
5. **Forecast drift between scenario runs and final figures.** Mitigation: snapshot + replay. Every figure in Chapter 4 that references forecast numbers must trace back to a file under `scenarios/snapshots/`.

---

## 11. Minimal Definition of Done

The evaluation described in Chapter 3 is runnable when, and only when, all of the following exist:

1. `ml/models/surf_condition_model.joblib` + `ml/models/model_metadata.json` committed (model file should be < 500 KB).
2. `SCORING_MODE=ml` produces per-hour output with non-empty `feature_contributions` for every record.
3. `scenarios/01..03` scripts each exit 0 and write their result JSON.
4. `ml/notebooks/03_evaluation.ipynb` runs top-to-bottom and emits the three metric groups plus per-spot / per-season breakdowns.
5. `evaluation/llm_baseline/results.csv` exists and contains six rows per scenario (two systems × three runs) across the five dimensions.
6. `make test` passes including the new ML and snapshot tests.

Once these are in place, Chapter 4 becomes descriptive narration of artifacts that already live in the repo, which is the outcome the DSR Communication step in Section 3.6 asks for.

---

## 12. Time Estimate (Working Solo)

Rough order of magnitude, assuming familiarity with the codebase and a working GPT-4o / Tavily / Azure setup:

| Phase                                    | Estimated effort |
| ---------------------------------------- | ---------------- |
| 1. Data + labels + features              | 3–5 days         |
| 2. Training + model artifacts            | 1–2 days         |
| 3. Runtime integration + config + tests  | 1–2 days         |
| 4. Scenario scripts + snapshot mechanism | 1 day            |
| 5. Internal baseline eval notebook       | 1–2 days         |
| 6. LLM baseline harness                  | 2–3 days         |
| 7. Figures + tables                      | 1 day            |
| **Total**                                | **10–16 days**   |

Phase 1 is the largest because the data-collection code has to handle two external APIs, two file formats, and five spots across time zones. Phases 2, 3, and 4 are mechanical once Phase 1 is solid. Phase 6 is the second-largest because it requires separate API clients and a defensible scoring rubric.

---

*End of plan.*
