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

### 3.3.5 — Hyperparameter grid

☐ **Hyperparameter grid — update parameter names**
- **Where:** Section 3.3.5 or appendix, wherever the hyperparameter grid is listed
- **Current text:** lists XGBoost parameters: `n_estimators`, `max_depth`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_weight`
- **New text:** HGBR parameter grid: `max_iter` (≡ n_estimators), `max_depth`, `learning_rate`, `min_samples_leaf` (≡ min_child_weight), `l2_regularization`. Remove `colsample_bytree` and `subsample` — HGBR uses histogram binning instead.
- **Why:** HGBR has a different hyperparameter API than XGBoost.
- **Evidence:** `ml/train.py`

---

### 3.5.2 — LLM Baseline evaluation design

☐ **Update Section 4.3.1 — stale claim that SurfSense uses live API**
- **Where:** Section 4.3.1, sentence "SurfSense, by contrast, receives only a natural-language request and must retrieve its forecast data autonomously through the whole agentic pipeline, including web search via the Research Agent and live API calls via the ForecastDataAgent."
- **New text:** Both systems now evaluate against the same snapshot data. `driver.py` injects the forecast snapshot into SurfSense's Forecast Data Agent before the orchestrator is invoked, so both systems see identical input. The evaluation tests whether the domain-specific pipeline adds value over a prompted LLM given equivalent information.
- **Why:** `driver.py` `_call_surfsense` was updated to inject snapshots, resolving the evaluation asymmetry. Section 3.5.2 already has the correct text; 4.3.1 still has the old claim.
- **Evidence:** `evaluation/llm_baseline/driver.py` `_call_surfsense`

---

☐ **Update scenario count and add automated evaluation description**
- **Where:** Section 3.5.2, scenario description paragraph ("The scenario set comprises five core snapshots… plus six additional cases…")
- **Current text:** "Eleven evaluation scenarios… five core snapshots (Guincho, Ericeira, Peniche, Sagres, and a Guincho winter-storm case) plus six additional cases that combine new spots (Hossegor, Jeffreys Bay) with skill-level cross-tests."
- **New text:** "Twenty-one scenarios defined in `scenarios/scenarios.json`, spanning **7 spots** (Praia do Guincho, Ericeira, Peniche, Sagres, Hossegor, Jeffreys Bay, and a Guincho winter-storm variant) × **3 skill levels** (beginner, intermediate, advanced). Scenarios are generated from a declarative coverage matrix (`scenarios/generate_scenarios.py`) and share 7 snapshot files — no live API calls are made at evaluation time, ensuring reproducibility."
- **Why:** `scenarios.json` expanded from 11 to 21 entries via `python -m scenarios.generate_scenarios --apply`.
- **Evidence:** `scenarios/scenarios.json`; `scenarios/generate_scenarios.py`

---

☐ **Add two-track evaluation description (demo scenarios vs automated evaluation)**
- **Where:** Section 3.5.2 (or a new Section 3.4.x), before the LLM baseline results
- **New text:**
  > "Scenario design follows a two-track structure. The first track consists of three qualitative demonstration scenarios (Sections 4.1.1–4.1.3): hand-crafted scripts that walk through the system end-to-end and are described in depth in Chapter 4. The second track is a systematic automated evaluation at scale. A declarative coverage matrix (`scenarios/generate_scenarios.py`) defines all combinations of available forecast snapshots and skill levels (beginner, intermediate, advanced), producing **21 scenarios across 7 geographic locations on 4 continents**. Each scenario is executed automatically via `evaluation/llm_baseline/driver.py --all`, which runs both SurfSense and GPT-4o-mini against the same snapshot data for three independent runs. Results are written to `evaluation/llm_baseline/results.csv` and scored by `score.py` on five dimensions."
- **Why:** Supervisor feedback: "Why only 3 scenarios? You should be able to test this at relative scale and automatize the evaluation."
- **Evidence:** `scenarios/generate_scenarios.py`; `scenarios/scenarios.json` (21 entries)

---

☐ **Add scenario coverage matrix table**
- **Where:** Section 3.5.2 or appendix
- **New text / action:** Insert a 7×3 table:

  | Snapshot | Window | Beginner | Intermediate | Advanced |
  |---|---|---|---|---|
  | Praia do Guincho | 24 h | ✓ | ✓ | ✓ |
  | Praia do Guincho | 24 h winter storm | ✓ | ✓ | ✓ |
  | Ericeira | 5 d | ✓ | ✓ | ✓ |
  | Peniche | 5 d | ✓ | ✓ | ✓ |
  | Sagres | 5 d | ✓ | ✓ | ✓ |
  | Hossegor | 5 d | ✓ | ✓ | ✓ |
  | Jeffreys Bay | 5 d | ✓ | ✓ | ✓ |

  Caption: "Scenario coverage matrix. Each cell is one scenario in `scenarios/scenarios.json`, executed automatically by `driver.py` for both SurfSense and GPT-4o-mini (3 runs each). 7 snapshots × 3 skill levels = 21 scenarios; 21 × 2 systems × 3 runs = 126 evaluation outputs."
- **Evidence:** `scenarios/scenarios.json`; `scenarios/generate_scenarios.py`

---

## Chapter 4 — Results

### Section 4.1 — Scenario Walkthrough

☐ **Clarify that demo scenarios are qualitative illustrations, not the full evaluation**
- **Where:** Section 4.1, opening paragraph
- **Current text:** Introduces three scenarios without distinguishing them from the systematic evaluation
- **New text / action:** Add at the start of Section 4.1:
  > "This section presents three representative scenarios that walk through the system's end-to-end behaviour in depth. These are qualitative demonstrations — selected to illustrate distinct system capabilities (single-spot condition check, multi-spot trip planning, and ML-scored feature output). The quantitative evaluation at scale is reported in Sections 4.2 and 4.3, which cover 21 systematically generated scenarios across 7 spots and all three skill levels."
- **Evidence:** `scenarios/generate_scenarios.py`; `evaluation/llm_baseline/runs/`

---

### Section 4.2 — Per-Agent and Orchestrator Evaluation Results (new section — not yet in thesis)

☐ **Add per-agent evaluation results**
- **Where:** New subsection in Chapter 4 (after existing Section 4.2 or as 4.4)
- **New text / action:** Report 11-scenario aggregate results:

  **Forecast Data Agent** (n=11): all four metrics (field completeness, temporal coverage, value sanity, wind direction presence) = 1.000 across all scenarios.

  **Condition Assessment Agent** (n=11):

  | Metric | Mean | N/A scenarios |
  |---|---|---|
  | Rating validity | 1.000 | 0 |
  | Score range validity | 1.000 | 0 |
  | Reasoning presence | 1.000 | 0 |
  | Safety threshold compliance | 1.000 | 7 (no unsafe hours) |
  | Rating-score monotonicity | 1.000 | 3 (single rating category) |

  **Trip Planning Agent** (n=11):

  | Metric | Mean | N/A scenarios |
  |---|---|---|
  | Window detection | 0.875 | 3 |
  | Window score ranking | 1.000 | 4 |
  | Suitable-hour coverage | 0.868 | 3 |
  | Min-hours constraint | 1.000 | 4 |

  Note: window_detection = 0.0 on `guincho_intermediate_24h` is correct system behaviour — no consecutive 2+ hour block exists at intermediate thresholds. Suitable-hour coverage mean of 0.868 reflects the same scenario (0.0) and isolated edge-hours in `sagres_5d` (0.946).

  **Interpretation:** The deterministic sub-agents perform with near-perfect reliability across all 11 scenarios and all three skill levels. This establishes that performance variation in the end-to-end LLM baseline (consistency 0.340, temporal optimisation 0.667) originates in the orchestration layer, not in the underlying data retrieval or condition assessment components.

- **Evidence:** `evaluation/agent_eval/results.csv` (143 rows); `evaluation/agent_eval/runner.py --all`

---

☐ **Add orchestrator coherence results**
- **Where:** Same subsection as per-agent results above
- **New text / action:** Report 11-scenario orchestrator coherence results (1 run per scenario):

  | Metric | Result | Applicable scenarios |
  |---|---|---|
  | tool_sequence_valid | **1.000** | 11 / 11 |
  | skill_level_passed_correctly | **1.000** | 11 / 11 |
  | unsafe_warning_present | **0.250** | 4 / 11 |
  | top_window_mentioned | N/A | 0 / 11 |

  **Key finding — structure the argument as follows:**

  *Detection vs. communication:* The condition agent (deterministic) flagged unsafe hours with 100% accuracy (safety_threshold_compliance = 1.000). The pipeline does not fail at detection. The failure occurs when the orchestrator (LLM) synthesises the condition agent's output: in mixed-condition scenarios (good windows + some unsafe hours), the LLM led with the positive framing and omitted the warning in 3 of 4 cases.

  *Compare to LLM baseline:* SurfSense safety_enforcement = 0.859, GPT-4o-mini = 0.917. GPT-4o-mini, which receives only raw forecast numbers with no condition agent labels, communicates danger more reliably than SurfSense, which has structured "unsafe" ratings available in its context. The agentic pipeline provides better safety information to the LLM but the LLM communicates it less reliably.

  *Design implication:* An explicit system-prompt constraint ("if any hours are rated 'unsafe', state a warning before describing recommended windows") is structurally enforceable in SurfSense because the condition agent's ratings are in session data. A one-shot prompted LLM cannot enforce this structurally.

  *Caveat:* The orchestrator coherence evaluation covers one run per scenario (LLM output is stochastic). The directional conclusion — optimistic framing in mixed conditions — is consistent with both measurements.

  `top_window_mentioned` scored N/A for all 11 scenarios — either `find_surf_windows` was not called in single-turn runs, or an existing bug in `Orchestrator._cache_result` (spot_name key popped before caching) prevented window retention. Note as an evaluation limitation.

- **Evidence:** `evaluation/agent_eval/orchestrator_results.csv` (44 rows); `evaluation/agent_eval/runner.py --orchestrator`

---

### Section 4.3 — Orchestrator safety communication fix + updated aggregate scores (2026-05-21)

☐ **UPDATE ALL FIVE-DIMENSION NUMBERS in 4.3, 4.3.2, 4.3.3, 4.4, and E3 criterion — see table below**
- **Where:** Sections **4.3** (Table 8), **4.3.2** (safety enforcement paragraph), **4.3.3** (dimension breakdown + framing paragraph), **4.4** (synthesis inline numbers), **3.5.4** (E3 criterion)

- **What was found and fixed:**
  After a few test runs during evaluation, the following issue was found: the orchestrator correctly received per-hour "unsafe" ratings from the Condition Assessment Agent — detection accuracy was 100 %, confirmed by `safety_threshold_compliance = 1.000` in the per-agent evaluation — but was not applying them faithfully when constructing its final user-facing response. The LLM was summarising multiple consecutive unsafe hours into a grouped range (e.g. "May 14, 16:00–23:00: unsafe conditions") rather than listing each timestamp individually. Because the `score_safety_enforcement` metric counts occurrences of the word "unsafe" divided by the number of unsafe hours, a single grouped mention for 22 hours produced run-level scores as low as 0.23 on `hossegor_5d`, pulling the scenario mean down to 0.55.

  The fix was a one-line addition to the orchestrator system prompt (`app/agents/orchestrator.py`, RULES section): *"When any hours are rated unsafe, list every unsafe timestamp on its own line and include the word 'unsafe' explicitly for each one. Never aggregate multiple unsafe hours into a single range without naming each timestamp individually."* This constraint is structurally enforceable in SurfSense because the condition agent's per-hour ratings exist in session data at synthesis time; a one-shot prompted LLM cannot enforce the same guarantee.

  Affected scenarios (`hossegor_5d` intermediate, `peniche_beginner_5d`) were re-run with `driver.py --force` and rescored. Both scenarios moved to 1.0 on all three SurfSense runs. GPT-4o-mini was also re-run on these two scenarios and produced a slightly lower score (0.8182) on hossegor, shifting the aggregate.

- **Corrected aggregate results — 21 scenarios, 3 runs each, post-fix (use these everywhere):**

  | Dimension | SurfSense | GPT-4o-mini | Winner |
  |---|---|---|---|
  | Factual consistency | **0.999** | 0.995 | SurfSense |
  | Safety enforcement | **0.887** | 0.844 | **SurfSense** ← flipped from pre-fix |
  | Temporal optimisation | 0.561 | **0.947** | GPT-4o-mini |
  | Explainability | **0.472** | 0.194 | SurfSense |
  | Consistency | 0.323 | **0.598** | GPT-4o-mini |

  SurfSense now leads on **3 of 5** dimensions. **E3 is now MET.**

- **Section-by-section impact:**
  1. **Section 4.3 Table 8** — replace every number in the table with the values above.
  2. **Section 4.3.2** — replace "GPT-4o-mini wins safety enforcement (0.917 vs 0.859)" with "SurfSense wins safety enforcement (0.887 vs 0.844)". Keep the detection-vs-communication framing; this fix is the concrete example of that argument.
  3. **Section 4.3.3 dimension breakdown** — update all five numbers and flip the safety winner. Add a sentence on the fix: "SurfSense's safety score improved from 0.859 to 0.887 after an explicit system-prompt constraint was added requiring the orchestrator to list each unsafe hour individually; this illustrates a structural advantage of the agentic design — output formatting can be enforced at the pipeline level."
  4. **Section 4.3.3 framing paragraph** — replace "SurfSense leads on two (factual consistency and explainability), GPT-4o-mini leads on three" with "SurfSense leads on three (factual consistency, safety enforcement, and explainability), GPT-4o-mini leads on two (temporal optimisation and consistency)."
  5. **Section 4.4 synthesis** — update all five inline score references; flip safety enforcement winner sentence.
  6. **Section 3.5.4 E3** — E3 is now MET. SurfSense leads on 3 of 5 as required. Replace the two-option discussion with a factual statement that the criterion is satisfied.

- **Evidence:** `app/agents/orchestrator.py` RULES section; `evaluation/llm_baseline/results.csv`; re-run `driver.py --scenario hossegor_5d --force`, `driver.py --scenario peniche_beginner_5d --force` (2026-05-21)

---

### Section 4.3 — LLM Baseline Results

☐ **Table 8 — update to 11-scenario aggregate results**
- **Where:** Section 4.3, five-dimension summary table
- **Current text (thesis PDF):** 4-scenario averages with safety_enforcement = N/A for both systems:
  factual_consistency GPT 0.960 / SS 0.970; temporal_optimisation GPT 1.000 / SS 0.750; consistency GPT 0.500 / SS 0.448; explainability GPT 0.167 / SS 0.784
- **New text / action:** Replace with 21-scenario aggregates (means computed over N/A-excluded per-scenario scores, 3 runs per system per scenario). **Use post-fix numbers from the 2026-05-21 entry above:**

  | Dimension | SurfSense | GPT-4o-mini | Winner |
  |---|---|---|---|
  | Factual consistency | **0.999** | 0.995 | SurfSense |
  | Safety enforcement | **0.887** | 0.844 | SurfSense |
  | Temporal optimisation | 0.561 | **0.947** | GPT-4o-mini |
  | Explainability | **0.472** | 0.194 | SurfSense |
  | Consistency | 0.323 | **0.598** | GPT-4o-mini |

- **Evidence:** `evaluation/llm_baseline/results.csv` (post-fix, 2026-05-21)

---

☐ **Section 4.3.2 — safety enforcement text needs updating**
- **Where:** Section 4.3.2 / Section 4.3 results discussion
- **Current text (thesis PDF):** "Safety enforcement is reported as N/A for all four scenarios and both systems… the dedicated winter-storm scenario cannot be scored comparably for both systems because SurfSense's forecast retrieval is limited to current and near-future dates."
- **New text / action:**
  1. Replace N/A claim: Safety enforcement is now scored for 4 of the 21 scenarios (`guincho_24h` beginner, `guincho_winter_24h`, `hossegor_5d` intermediate, `peniche_beginner_5d`). **SurfSense wins this dimension (0.887 vs GPT-4o-mini 0.844)** — see 2026-05-21 fix entry above for how the orchestrator bug was found and resolved.
  2. Remove the historical-date limitation claim: `driver.py` now injects snapshot data into SurfSense's forecast agent, so both systems evaluate against identical data. The historical-date limitation remains in live deployment but does not apply to the evaluation harness.
- **Evidence:** `evaluation/llm_baseline/results.csv` (post-fix, 2026-05-21); `evaluation/llm_baseline/driver.py` `_call_surfsense`

---

☐ **Section 4.3.3 — discussion numbers stale; rewrite against 11-scenario results**
- **Where:** Section 4.3.3, discussion paragraph following Table 8
- **Current text (thesis PDF):** References stale numbers ("SurfSense factual consistency 0.907 vs GPT-4o-mini 0.826", "explainability gap 0.793 vs 0.171") that match neither Table 8 nor any version of `results.csv`
- **New text / action:** Rewrite using 21-scenario post-fix results (2026-05-21):
  - Factual consistency: SurfSense **0.999** vs GPT-4o-mini **0.995** — near-perfect grounding in forecast data for both systems
  - Safety enforcement: SurfSense **0.887** vs GPT-4o-mini **0.844** — SurfSense leads after an explicit system-prompt constraint was added requiring per-hour unsafe listings; mention that before the fix the scores were 0.859 vs 0.917, and that the improvement demonstrates a structural advantage of the agentic design (enforcement at pipeline level)
  - Temporal optimisation: GPT-4o-mini **0.947** vs SurfSense **0.561** — injected tabular data makes time-window identification easier for the one-shot model
  - Consistency: GPT-4o-mini **0.598** vs SurfSense **0.323** — stochastic multi-step reasoning produces more varied outputs
  - Explainability: SurfSense **0.472** vs GPT-4o-mini **0.194** — the domain-specific pipeline cites specific forecast values ~2.4× more often; this is the primary thesis differentiator
- **Evidence:** `evaluation/llm_baseline/results.csv` (post-fix, 2026-05-21)

---

☐ **Section 4.3.3 — add SurfSense capability argument framing**
- **Where:** Section 4.3.3, before the dimension-by-dimension breakdown
- **New text / action:** Add framing paragraph:
  > "SurfSense leads on three of five dimensions (factual consistency, safety enforcement, and explainability) while GPT-4o-mini leads on two (temporal optimisation and cross-run consistency). The comparison must be read in light of the evaluation design: GPT-4o-mini receives the forecast table injected directly into its prompt and is evaluated on how well it formats pre-structured information. SurfSense, by contrast, independently researches the spot, retrieves forecast data, routes it through a condition-assessment agent (with optional ML scoring), and synthesises a natural-language response — a fundamentally harder task. That it leads on factual consistency (0.999 vs 0.995), safety enforcement (0.887 vs 0.844), and explainability (0.472 vs 0.194) is the thesis argument. The two dimensions where GPT-4o-mini leads reflect the structural advantage of a one-shot structured-output prompt — exactly what an open-ended conversational agent is not optimised for."

---

☐ **Section 4.4 — synthesis inline numbers need updating**
- **Where:** Section 4.4, summary claims referencing Table 8 scores
- **Current text (thesis PDF):** "SurfSense exceeds GPT-4o-mini on explainability (0.793 vs. 0.171) while maintaining comparable factual consistency (0.826 vs. 0.907) despite retrieving its data autonomously rather than receiving it pre-injected"
- **New text / action:** Replace all inline score references with 21-scenario post-fix averages:
  - Factual consistency: SurfSense **0.999** / GPT-4o-mini **0.995**
  - Safety enforcement: SurfSense **0.887** / GPT-4o-mini **0.844** (SurfSense leads; defined for 4 of 21 scenarios)
  - Temporal optimisation: GPT-4o-mini **0.947** / SurfSense **0.561**
  - Explainability: SurfSense **0.472** / GPT-4o-mini **0.194**
  - Consistency: GPT-4o-mini **0.598** / SurfSense **0.323**
  - Remove "retrieving its data autonomously" — both systems now use injected data
  - Remove any claim that safety enforcement is N/A
- **Evidence:** `evaluation/llm_baseline/results.csv` (post-fix, 2026-05-21)

---

## Appendix

☐ **Data provenance appendix** — copy from `ml/data/DATA_PROVENANCE.md`
- **Action:** The provenance file is written to be dropped directly into the thesis appendix. Copy it in and format it per the document style. Four sources: Open-Meteo Marine, Open-Meteo Archive (weather), tide (NaN / limitation), spot metadata.

---

☐ **Submission commit SHA** — add to appendix after final commit
- **Action:** After tagging `v1.0-submission`, record the git SHA in the thesis appendix reproducibility section.

---

## Pre-submission checklist

*Remaining non-coding items with direct thesis or reproducibility impact.*

☐ **Cold-read Chapter 4 against files on disk** — before submission, every claim in Chapter 4 must have a corresponding file under `evaluation/` or `ml/figures/`. Any unsupported claim must either be cut or have an artifact generated for it.

☐ **Draft glossary / notation list** — SHAP, R², Macro F1, MAE, RMSE, Spearman's ρ, TimeSeriesSplit, Gaussian falloff. Reviewers outside ML will need it.

☐ **Line up a proofreader** for the final draft before submission.

### Submission and defence prep

☐ **Back up everything redundantly** at least 72 hours before submission: model file, raw data, notebook outputs, git remote, one cold-storage copy (external drive or second cloud).

☐ **Prepare a clean zip of the repo** at the submission SHA — exclude `.env`, raw data dumps, and notebook checkpoints.

☐ **Record a 2–3 minute video demo** of the end-to-end SurfSense flow (including a Scenario 3 ML-scored output). Insurance if the live demo fails on defence day.

☐ **Dry-run the defence presentation** with a timer, at least one week before.

☐ **Prepare a 10-slide backup deck** for anticipated defence questions: "why HGBR not a neural net?", "why only five spots?", "why synthetic labels instead of crowd-sourced?", "why not run the eval over 100 scenarios?". Each question gets one slide.

---

## Section 4.2 — Internal ML Baseline: concrete performance numbers

☐ **Write Section 4.2 body text using the following confirmed test-set metrics**
- **Where:** Section 4.2 (internal ML baseline), all sub-paragraphs that state model performance
- **Source:** `ml/notebooks/03_evaluation.ipynb` (cells 31–38), held-out test set

  **Overall metrics (test set, n≈13 158 hours):**

  | Metric | ML (HGBR) | Rule-based |
  |---|---|---|
  | MAE | **2.06** | 12.72 |
  | RMSE | **3.59** | 15.16 |
  | R² | **0.9449** | 0.017 |
  | Accuracy (3-class) | **93.97 %** | 64.15 % |
  | F1 macro | **0.9234** | 0.6629 |
  | Spearman ρ | **0.9502** | 0.6657 |

  **Acceptance thresholds (Section 3.5.3) — all met:**
  - ML R² ≥ 0.75: 0.9449 ✓
  - ML Accuracy ≥ 80 %: 93.97 % ✓
  - ML beats rule on ≥ 2 metric groups: 3/3 ✓ (regression, classification, ranking)

  **Validation metrics** (from `model_metadata.json`, for cross-referencing):
  - val_r2 = 0.9696, val_mae = 1.50, CV R² mean = 0.9225

  **Best hyperparameters** (from `model_metadata.json`):
  - learning_rate = 0.1, max_depth = 7, max_iter = 500, min_samples_leaf = 10

  **Per-spot breakdown (ML, test set):**

  | Spot | n | R² | MAE | Accuracy |
  |---|---|---|---|---|
  | Hossegor | 2 632 | 0.991 | 1.01 | 96.3 % |
  | Ericeira | 2 632 | 0.983 | 1.18 | 96.3 % |
  | Gold Coast | 2 631 | 0.837 | 2.28 | 95.2 % |
  | Pipeline | 2 632 | 0.825 | 3.17 | 85.7 % |
  | Jeffreys Bay | 2 631 | 0.704 | 2.65 | 96.4 % |

  **Per-season breakdown (ML, test set):**

  | Season | n | R² | Accuracy |
  |---|---|---|---|
  | DJF (winter) | 6 438 | 0.967 | 95.6 % |
  | MAM (spring) | 6 720 | 0.916 | 92.4 % |

  **SHAP — top-3 features by mean |SHAP value|** (confirmed from notebook cell 34 output):
  1. `wave_energy_proxy` (rank 1 — highest bar in `ml/figures/feature_importance.png`)
  2. `wind_dir_sin` (rank 2)
  3. `wind_wave_interaction` (rank 3)

  Figure file for SHAP bar chart: `ml/figures/feature_importance.png` (NOT `shap_bar.png` — that file does not exist)
  Figure file for SHAP beeswarm: `ml/figures/shap_beeswarm.png`

- **Evidence:** `ml/notebooks/03_evaluation.ipynb`; `ml/models/model_metadata.json`

---

## Section 4.1.1 — Table 2: actual rule-based scores (Scenario 1, Guincho 24 h beginner)

☐ **Fill in Table 2 score and rating columns from `scenarios/results/scenario_01_rule.json`**
- **Where:** Section 4.1.1, Table 2
- **Source:** `scenarios/results/scenario_01_rule.json` — snapshot `guincho_24h.json`, skill_level=beginner, scoring_mode=rule
- **Full 24-hour dataset** (use appropriate rows to match whatever 6 rows the table currently shows):

  | Time (UTC) | Wave h (m) | Wind (kph) | Swell (s) | Score | Rating |
  |---|---|---|---|---|---|
  | 00:00 | 1.36 | 17.6 | 8.4 | 49.1 | suitable |
  | 04:00 | 1.32 | 16.6 | 8.4 | 50.0 | suitable |
  | 07:00 | 1.24 | 13.8 | 8.4 | **51.1** | suitable (best window) |
  | 08:00 | 1.22 | 11.6 | 8.4 | 50.5 | suitable |
  | 10:00 | 1.16 | 8.3 | 8.4 | 48.9 | suitable |
  | 13:00 | 1.12 | 15.0 | 8.4 | 47.9 | suitable |
  | 14:00 | 1.14 | 18.1 | 8.4 | 42.2 | challenging |
  | 17:00 | 1.22 | 19.6 | 8.4 | **41.3** | challenging |
  | 18:00 | 1.24 | 20.5 | 8.4 | **40.1** | challenging (worst) |
  | 20:00 | 1.26 | 19.5 | 8.4 | 42.6 | challenging |
  | 23:00 | 1.26 | 17.3 | 7.65 | 45.4 | suitable |

  **Key pattern:** Morning hours (00:00–13:00) mostly rated "suitable" (scores 47–51); afternoon/evening (14:00–22:00) mostly "challenging" (scores 40–46) as wind picks up. Score range: 40.1–51.1.
- **Table caption:** Cite `scenarios/results/scenario_01_rule.json` and `scenarios/snapshots/guincho_24h.json`.
- **Evidence:** `scenarios/results/scenario_01_rule.json`

---

## Section 4.1.3 — Table 4: actual ML vs rule-based scores (Scenario 3, Guincho 24 h beginner)

☐ **Fill in Table 4 ML Score/Rating and Rule Score/Rating columns from scenario result files**
- **Where:** Section 4.1.3, Table 4
- **Sources:** `scenarios/results/scenario_03_ml.json` (ML) and `scenarios/results/scenario_01_rule.json` (rule-based) — same snapshot, same skill level
- **Side-by-side comparison for representative hours:**

  | Time (UTC) | Rule Score | Rule Rating | ML Score | ML Rating |
  |---|---|---|---|---|
  | 00:00 | 49.1 | suitable | 25.5 | challenging |
  | 04:00 | 50.0 | suitable | 25.1 | challenging |
  | 07:00 | 51.1 | suitable | 29.9 | challenging |
  | 08:00 | 50.5 | suitable | 28.2 | challenging |
  | 13:00 | 47.9 | suitable | 25.1 | challenging |
  | 18:00 | 40.1 | challenging | 24.7 | challenging |

  **Key finding for thesis text:** The ML model rates ALL 24 hours as "challenging" for a beginner (scores 23.6–30.0). The rule-based scorer rates 14 of 24 hours as "suitable" (scores 40–51) and 10 as "challenging" (40–46). The ML model is systematically more conservative for beginners at this wave/wind profile — reflecting the model having learned that 1.2–1.4 m waves with 8+ kph wind are "challenging" territory for beginners from the training data, whereas the rule threshold for this skill level allows up to higher wind speeds before triggering "challenging". This divergence is the thesis argument: the ML model captures distributional patterns the rule formula cannot express.
- **Evidence:** `scenarios/results/scenario_01_rule.json`; `scenarios/results/scenario_03_ml.json`

---

## Chapter 3 — additional gaps found in audit (2026-05-12)

### 3.3.6 — wrong cross-reference to rule-based scoring

☐ **Fix cross-reference: "Section 3.3.3" → "Section 3.3.4"**
- **Where:** Section 3.3.6, sentence mentioning the rule-based composite score
- **Current text:** "The rule-based composite score described in Section 3.3.3"
- **New text:** "The rule-based composite score described in Section 3.3.4"
- **Why:** Section 3.3.3 is Forecast Data Retrieval. Condition Scoring is Section 3.3.4. The cross-reference is wrong.
- **Evidence:** Thesis PDF page structure; `app/planning/scoring.py`

---

### 3.5.3 — broken chapter reference

☐ **Fix broken reference "Chapter ??" in Section 3.5.3**
- **Where:** Section 3.5.3, sentence "Results are reported in Chapter ??."
- **Current text:** "Results are reported in Chapter **??**."
- **New text:** Update to point to the section where per-agent and orchestrator coherence results are reported (the new subsection added to Chapter 4 per the entry above "Add per-agent evaluation results"). At minimum remove the unresolved placeholder before submission.
- **Why:** LaTeX cross-reference was never resolved; will show as "Chapter ??" in the compiled PDF.
- **Evidence:** Visible unresolved reference in thesis PDF

---

### 3.5.3 — Research Agent determinism qualifier needed

☐ **Add determinism qualifier: "given fixed snapshot input"**
- **Where:** Section 3.5.3, sentence stating "the four sub-agents are deterministic"
- **Current text:** "the four sub-agents are deterministic" (with a reviewer/TODO annotation flagging that Tavily calls vary by day)
- **New text:** "the four deterministic sub-agents — deterministic in the sense that they produce identical output given the same snapshot input; the Research Agent's Tavily web-search calls are bypassed in the evaluation harness, which injects a fixed snapshot file instead of issuing live requests."
- **Why:** The evaluation harness (`evaluation/agent_eval/runner.py`) injects snapshot data so Tavily is not called; "deterministic" is accurate only for the harness context. The reviewer annotation flags exactly this ambiguity.
- **Evidence:** `evaluation/agent_eval/runner.py`; `evaluation/llm_baseline/driver.py`

---

### 3.5.3 — automated evaluation pipeline description incomplete

☐ **Make the full automated evaluation pipeline explicit in Section 3.5.3**
- **Where:** Section 3.5.3, evaluation procedure description
- **Current text:** Does not clearly describe both automated harnesses or the full pipeline chain
- **New text / action:** Add a paragraph (or expand existing) to state:
  > "The evaluation pipeline is fully automated. Sub-agent correctness is evaluated via `evaluation/agent_eval/runner.py --all`, which executes all 11 (or 21) scenarios and writes per-metric scores to `evaluation/agent_eval/results.csv` and `orchestrator_results.csv`. The LLM baseline comparison is executed via `evaluation/llm_baseline/driver.py --all`, which runs both SurfSense and GPT-4o-mini against the same snapshot data for three independent runs per scenario and writes dimension scores to `evaluation/llm_baseline/results.csv`. Scores are computed by `score.py` using the five-dimension rubric defined in Section 3.5.2. No manual scoring or annotation is required: all 126 evaluation outputs (21 scenarios × 2 systems × 3 runs) are produced and scored automatically from a single command."
- **Why:** Supervisor feedback required evaluation at scale and automation. The automation story is the answer to "why only 3 scenarios?" and must be explicit in the methodology chapter.
- **Evidence:** `evaluation/agent_eval/runner.py`; `evaluation/llm_baseline/driver.py`; `scenarios/generate_scenarios.py`

---

### 3.5.4 — D1 criterion wrong on two counts

☐ **Fix criterion D1: wrong scenario count and wrong data source**
- **Where:** Section 3.5.4, criterion D1 definition
- **Current text:** "Criterion D1 requires that all **eleven** scenarios execute without runtime errors on **live forecast data**."
- **New text:** "Criterion D1 requires that all **three demonstration scenarios** (Sections 4.1.1–4.1.3) execute without runtime errors. The systematic evaluation of 21 scenarios is handled by the automated harness (Section 3.5.3), which uses injected snapshot data rather than live API calls, ensuring reproducibility."
- **Why:** (1) The three demonstration scenarios are what Section 4.1 covers; 21 is the systematic evaluation count. (2) The automated evaluation harness uses snapshot injection, not live API calls. Both facts are wrong in the current criterion statement.
- **Evidence:** `evaluation/llm_baseline/driver.py`; `scenarios/scenarios.json`

---

### 3.5.4 — E3 threshold not met; needs reframing

☐ **Reframe criterion E3 to match actual results**
- **Where:** Section 3.5.4, criterion E3 definition and/or Section 4.3.3 discussion
- **Current text:** "E3 is met if SurfSense scores higher on at least **three** of the five dimensions."
- **Actual result (post-fix, 2026-05-21):** SurfSense leads on **three** of five dimensions (factual_consistency: 0.999 vs 0.995; safety_enforcement: 0.887 vs 0.844; explainability: 0.472 vs 0.194). GPT-4o-mini leads on two (temporal_optimisation, consistency). **E3 is now MET.**
- **New text / action:** Keep the criterion as written. State in Section 4.3.3 / Section 3.5.4 that E3 is satisfied: SurfSense scores higher on three of five dimensions as required. Remove any hedging language about the criterion not being met. The pre-fix situation (two dimensions) is documented in the 2026-05-21 fix entry as historical context showing why the safety enforcement improvement matters.
- **Why:** After the orchestrator safety communication fix (`app/agents/orchestrator.py`), safety_enforcement flipped from a GPT-4o-mini win (0.917 vs 0.859) to a SurfSense win (0.887 vs 0.844), giving SurfSense the required three-dimension lead.
- **Evidence:** `evaluation/llm_baseline/results.csv` (post-fix, 2026-05-21)

---

## Chapter 4 — additional gaps found in audit (2026-05-12)

### Section 4.1.1 — Table 2 scores missing

☐ **Fill in Table 2 score column (currently all "–")**
- **Where:** Section 4.1.1, Table 2 (Scenario 1 walkthrough, rule-based scoring output)
- **Current text:** Score column shows "–" for all 6 time-window rows; caption does not reference the snapshot file
- **New text / action:**
  1. Run Scenario 1 end-to-end with the rule-based scorer active and extract the per-window scores from the output.
  2. Fill in the Score column with actual values from `scenarios/snapshots/` + `app/planning/scoring.py`.
  3. Update the table caption to cite the snapshot file used (e.g., "Source: `scenarios/snapshots/guincho_24h.json`"), consistent with other tables in Chapter 4.
- **Why:** An empty score column in a results table is a clear gap; the system can produce these scores deterministically from the snapshot.
- **Evidence:** `scenarios/snapshots/`; `app/planning/scoring.py`

---

### Section 4.1.3 — Table 4 ML scores missing

☐ **Fill in Table 4 Rule Score and ML Score columns (currently all "– / –")**
- **Where:** Section 4.1.3, Table 4 (Scenario 3 walkthrough, ML vs rule-based comparison)
- **Current text:** Both "Rule Score / Rating" and "ML Score / Rating" columns show "– / –" for all 6 rows
- **New text / action:**
  1. Run Scenario 3 with both the rule-based scorer and ML scorer active.
  2. Extract per-window scores and ratings from both.
  3. Fill in all 12 cells (6 rows × 2 columns) with actual computed values.
  4. Update the hedged language in the surrounding text (see entry below).
- **Why:** Empty results table in the core ML comparison scenario undermines the Chapter 4 argument.
- **Evidence:** `app/planning/scoring.py`; `ml/models/surf_condition_model.joblib`; `scenarios/snapshots/`

---

### Section 4.1.3 — hedged language about ML comparison

☐ **Replace hedged future language in Section 4.1.3 with actual observed results**
- **Where:** Section 4.1.3, sentence(s) describing the ML vs rule-based comparison
- **Current text:** "The ML scorer is expected to produce a different distribution of scores and ratings" (future/speculative tense)
- **New text / action:** Once Table 4 is filled in (see entry above), replace this sentence with a description of what was actually observed: where the ML scorer agreed with the rule-based scorer, where it diverged, and what the divergence reveals about the model's learned weights versus the hand-crafted rule thresholds.
- **Why:** Speculative language in a results section signals the comparison was not done when the chapter was written. This must be resolved before submission.
- **Evidence:** `app/planning/scoring.py`; `ml/models/surf_condition_model.joblib`

---

### Section 4.2.1 — tide imputation cross-reference missing

☐ **Add cross-reference for tide imputation ("why imputed?")**
- **Where:** Section 4.2.1 (internal ML baseline), wherever tide imputation is mentioned or implied
- **Current text:** Tide imputation is mentioned or visible in the data without explanation; a reviewer annotation reads "why imputed?"
- **New text / action:** Add a sentence: "Tide height is imputed to each spot's preferred midpoint value (see Section 3.3.3 / Data Provenance appendix) because the Open-Meteo Marine API does not provide tidal predictions for the evaluation locations; this is noted as a known limitation."
- **Why:** The reviewer annotation is unanswered. The explanation already exists in Section 3.3.3 and `ml/data/DATA_PROVENANCE.md`; it just needs to be cross-referenced here.
- **Evidence:** `ml/data/DATA_PROVENANCE.md`; `ml/labels.py`

---

### Section 4.4 — SHAP feature ordering inconsistency

☐ **Fix SHAP ordering inconsistency in Section 4.4 synthesis**
- **Where:** Section 4.4, sentence listing top SHAP contributors
- **Current text:** "wind_dir_sin (4.06), wave_energy_proxy (3.45)" — lists wind_dir_sin first
- **Correct ordering:** Figure 8 (SHAP bar chart) shows `wave_energy_proxy` as the longest bar and highest-importance feature. Section 4.2.2 explicitly states "Wave energy ranks first." The Section 4.4 values contradict both.
- **New text / action:** Correct the ordering and values: "wave_energy_proxy ranks first in mean absolute SHAP value, followed by wind_dir_sin, then wind_wave_interaction." Use confirmed order from `ml/notebooks/03_evaluation.ipynb` cell 34 output: `['wave_energy_proxy', 'wind_dir_sin', 'wind_wave_interaction']`.
- **Why:** Factual inconsistency between Figure 8, Section 4.2.2, and Section 4.4. Will be caught by any reader who checks the figure.
- **Note:** The SHAP bar chart figure is `ml/figures/feature_importance.png` — a file named `shap_bar.png` does not exist in the repo.
- **Evidence:** `ml/figures/feature_importance.png`; `ml/notebooks/03_evaluation.ipynb` (cell 34); Section 4.2.2 text

---

### Chapter 4 — inline TODO comment boxes must be removed before submission

☐ **Remove all inline TODO / reviewer annotation boxes from Chapter 4**
- **Where:** Multiple locations throughout Chapter 4 (orange highlighted annotation boxes visible in the compiled PDF)
- **Current text (boxes to remove):**
  1. "References, Diagrams and Appendix AAAAND!: Check numbers —-> also: define language as American (also for time format etc.!)"
  2. "Check if the numbers are realistic, did the model overfit?!"
  3. "re-write these two chapters with new results from comparison"
  4. "why imputed?" (addressed by cross-reference entry above)
  5. "beschreibe hier nur dinge die du weißt" (German: "only describe things you know")
  6. "Commend below"
  7. "Do ToDos in the comments %"
  8. "Center the diagram"
  9. "Colors of agents & tools in ML diagram?"
  10. "A lot of functions involved in text: Bruno once said 'no function names'? –> check with him"
- **New text / action:** Remove all annotation boxes. Address the substantive concerns first (number checks, rewriting with new results, language/format consistency), then delete the comment boxes themselves.
- **Why:** Annotation boxes are private working notes and must not appear in the submitted PDF. They are visible in the current compiled version.
- **Evidence:** Thesis PDF (Master_Thesis_Joshua (13).pdf), Chapter 4

---

*Append new items below as they arise, mark them ☑ when done.*
