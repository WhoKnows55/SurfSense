# SurfSense Evaluation: Real-Life Todo List

**Purpose:** Companion to `SurfSense_Evaluation_Implementation_Plan.md`. Covers the non-coding work needed to make the coding plan executable on schedule. If the technical plan answers *what to build*, this list answers *what has to be true around you so the build does not stall*.

**Author:** Joshua Wehr
**Status legend:** ☐ not started · ◐ in progress · ☑ done

---

## 0. Why this document exists

The implementation plan has 10 to 16 engineering days on it. In practice, solo thesis work of this shape tends to lose 20 to 40 % of that time to things that are not code: waiting on API approval, discovering the ocean data you need is not where you thought, realising the synthetic label needs per-spot research you did not plan for, or rewriting Chapter 4 because figure captions drift from what the advisor expected. This list front-loads those items so none of them become the blocking path.

The ordering is roughly chronological: items at the top should be done in the first couple of days, items at the bottom belong closer to submission.

---

## 1. Day-0 kick-off (first 2 hours of work)

Before writing a line of ML code:

☑ Run the current repo end-to-end against a live spot. Confirm the baseline still works. If anything is broken, fixing that comes before Phase 1.
☑ Pull `SurfSense_Evaluation_Implementation_Plan.md` into a branch and commit it to the repo so the plan itself is version-controlled alongside the code.
☑ Open a working-log file (`WORKLOG.md` or similar) and append-only date-stamped entries each session. Thesis defence panels love provenance; so does your future self at week 2.
☐ Create a fresh issue / task board (GitHub Projects, Linear, or plain markdown) with one row per `☐` in the implementation plan. Do not estimate hours; just get the universe of tasks into one view.

---

## 2. Supervisor and thesis alignment

These conversations do not take long, but skipping them is how scope creep happens in week 3.

☑ **Share the implementation plan with the supervisor and get explicit sign-off on scope.** Ten to sixteen days of solo work is a meaningful commitment; have the advisor agree in writing (even a short email) that this scope answers Section 3.3.5 and 3.5.
☑ **Resolve the Open-Meteo vs. Stormglass priority question.** Section 1 of the plan recommends flipping the code; the thesis text is what gets examined. Ask the advisor which they prefer. Do not start Phase 1 until this is closed.
☑ **Pin the LLM baseline models.** GPT-4o baseline uses the existing Azure deployment (`AZURE_OPENAI_DEPLOYMENT_NAME` in `.env`) — version is pinned at the Azure deployment level, matching the orchestrator. Claude baseline uses `claude-sonnet-4-6` (current production model). Both are committed in `evaluation/llm_baseline/driver.py`.
☑ **Agree on acceptance thresholds before running evals.** The plan states R² ≥ 0.75 and classification ≥ 80 %. If results land at 0.72, does the thesis still pass? Agreeing now on the honest fallback framing (for example: "ML matches rule-based on two of three metric groups, loses on regression by a small margin, and wins on ranking, which is the metric that matters at deployment time") saves a panic rewrite later. (SOlved= can just rewrite the values in the thesis :D)
☐ **Pre-agree the Chapter 4 structure.** Which tables, which figures, in what order. If the advisor expects a specific narrative (e.g., "lead with the LLM baseline, then internal baseline"), surface that before you generate figures, because the captions will need to match.
☑ **Schedule a supervisor check-in after Phase 3 merge.** That is the last point at which you can still change direction cheaply. Doing it after Phase 5 means the eval is locked in.

---

## 3. Accounts, credentials, and API access

☑ **OpenAI**: confirm a paid account with access to GPT-4o. Free tier will not cover 9 eval calls at the required model. Generate a project-scoped key, not the master key.
☐ **Anthropic**: confirm a paid account with access to the pinned Claude model. Generate a project-scoped key.
(==> Might cross this out and just use Chat for now)
☑ **Store both keys in a password manager**, then copy into the repo `.env`. Double-check `.env` is in `.gitignore` before the first commit that touches it. (One leaked key voids the reproducibility story for months.)
☑ **Open-Meteo Historical Weather API**: no key required, but read the fair-use policy. They publish a request-per-day soft cap; pacing the collector script (e.g., a 200 ms sleep between requests) is the socially correct behaviour for a free source that will appear in your bibliography.
☐ **NOAA**: no key required for ERDDAP, but confirm the ERDDAP endpoint you plan to hit is live. NOAA servers move occasionally. Test one request per spot before writing the full pipeline. (==> might remove NOOA completely)
☑ **Stormglass, Tavily, Azure OpenAI**: confirm existing credentials still work and have quota. These were configured earlier in the project; it is easy to assume they still function.
☑ **Audit `.env.example`** after adding `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. The example file should contain placeholders, never real values.

---

## 4. Budget and cost control

The bill for this evaluation is small, but only if the cache works. A single infinite loop of un-cached LLM calls can put three figures on your credit card before you notice.

☐ **Estimate the LLM eval cost.** Napkin arithmetic: 9 calls per scenario × 3 scenarios = 27 calls. Each prompt embeds 24 hourly forecast rows (~2.5 K input tokens) and draws ~1.5 K output tokens. At current GPT-4o pricing, the full eval lands at roughly \$1 to \$3. Claude is comparable. Total budget: \$10 covers several re-runs.
☐ **Set a hard billing limit** on both OpenAI and Anthropic dashboards (e.g., \$25 monthly cap). This is the circuit breaker if caching fails.
☐ **Decide the kill-switch condition in advance.** For example: "If total eval spend exceeds \$30, stop, diagnose, before continuing." Write this down so it is not a decision you have to make under pressure.
☐ **Verify the caching contract in `evaluation/llm_baseline/driver.py` before running the full eval.** Run a single scenario twice; confirm the second run makes zero API calls. This is the sanity check that protects the budget.

---

## 5. Per-spot domain research (the Scarfe-grounded work)

This is the largest non-coding block and the one most often underestimated. The synthetic label in Section 2.2 requires *per-spot physical parameters*. Without them, the label formula is a placeholder, not a defensible target.

For each of **Pipeline, Hossegor, Ericeira, Jeffreys Bay, Gold Coast**:

☑ **Swell-facing direction** (compass bearing, degrees). This is the input to the offshore-wind-alignment cosine. Source: Surfline spot descriptions, Wannasurf, Stormrider Guide (the book), or academic literature on each break.
☑ **Preferred tide band** (low / mid / high, plus preferred metres above chart datum). Pipeline works on mid-to-high; Hossegor is tide-sensitive; J-Bay has a relatively forgiving tide window. Research each.
☑ **Wind-speed ceiling before the break becomes unrideable** (spot-specific, may differ from the generic 25 kph in the synthetic formula). Document the per-spot value even if you end up averaging.
☑ **Break type** (reef / point / beach). Not a model input, but useful thesis commentary.
☑ **Consolidate into `ml/data/spot_metadata.json`.** Committing this file makes the synthetic label reproducible and auditable. A reviewer who questions "where did the Gaussian tidal falloff come from?" has a traceable answer.
☑ **Re-read Scarfe, Elwany, Mead, and Black (2009)** and annotate which specific claims ground each term of the synthetic score. Keep this as a short `ml/labels_references.md` note.

---

## 6. Data source reconnaissance

Before writing `ml/data/collect.py`, resolve the *known unknowns* of the data supply chain. One hour of reconnaissance here saves a lost day in Phase 1.

☐ **For each of the five spots, test a single NOAA WW3 request by hand.** Point queries on a 0.5° grid sometimes land in ocean grid cells that are fine, sometimes in cells shadowed by islands or too coarse for reef breaks. Record the result per spot.
☐ **For each spot where WW3 is awkward, confirm the Open-Meteo marine hindcast covers the same window.** The plan's Risk #2 acknowledges this substitution; decide per-spot now so the collector script is not rewritten mid-flight.
☐ **Document the substitution in `DATA_PROVENANCE.md`.** One paragraph per spot: source, date of access, license, any substitution with rationale. This paragraph drops into the thesis appendix later.
☐ **Confirm tide data source per spot.** Open-Meteo's tide coverage is thin in some regions; WorldTides or local hydrographic offices may be needed for European spots. Identify this before you need it.
☐ **Check time-zone handling.** Each spot sits in a different tz (Pacific/Honolulu, Europe/Paris, Europe/Lisbon, Africa/Johannesburg, Australia/Brisbane). Confirm `SpotMeta` entries use IANA tz identifiers, not UTC offsets, so daylight-saving transitions do not corrupt hourly alignments across years.

---

## 7. Environment and hardware readiness

Small items, but any of them can block an evening.

☐ **Confirm free RAM** on the training machine. XGBoost grid search over ~108 hyperparameter combinations on ~80 K rows fits comfortably in 8 GB, but 16 GB is the comfortable range if Jupyter and a browser are also open. If the machine is tight, close everything during training.
☐ **Confirm free disk.** Raw NOAA downloads can be several GB before the `ml/data/processed/historical.parquet` is written. Plan for 20 GB of scratch.
☐ **Check network bandwidth.** Five spots × two years × hourly data is roughly 90 K requests if done one-at-a-time (before batching). Coffee-shop wifi is not the place to run this.
☐ **Create a dedicated Python venv** for the ML work, separate from the app venv if desired. This isolates xgboost/shap/pandas version pins from the app's runtime dependencies.
☐ **Install Jupyter and confirm matplotlib renders inline.** The EDA notebook in Section 2.5 assumes this works; discover any plotting-backend weirdness before you start analysing data.

---

## 8. Reproducibility and versioning decisions

These are one-time judgment calls. Making them up front keeps the thesis artifacts clean.

☐ **Pin exact package versions in `requirements.txt` before training the final model.** `xgboost>=2.0.0` is fine during development; for the committed model, pin `xgboost==2.x.y`. A breaking xgboost release between training and examiner-download will otherwise brick the model file.
☐ **Pick a model-versioning convention.** Options: `surf_condition_model.joblib` (single artifact, overwritten) vs. `surf_condition_model_v1_20260501.joblib` (dated). The committed model is a snapshot; dated filenames are more defensible.
☐ **Decide: commit the model file to git, or publish it as a release asset?** At 500 KB it fits fine in git. If it grows past a few MB, use releases with LFS.
☐ **Decide: commit the 80 K-row parquet files, or leave them as generated artifacts?** Raw public-API data is replayable; a manifest file (row count, date range, SHA-256 of the processed parquet) is usually enough for reviewers, and git stays lean.
☐ **Prompt versioning.** Commit `evaluation/llm_baseline/prompt_template.txt`, record its SHA in every eval run file. Any wording edit re-runs the eval; that is the desired behaviour.
☐ **Set a fixed random seed (42) everywhere**: XGBoost, train/val/test splits, SHAP, any shuffling. Verify the same seed is threaded through all scripts.

---

## 9. Quality gates (human review moments baked into the pipeline)

These are the points where reading the output with your own eyes catches things automated tests cannot.

☐ **After EDA notebook:** look at the label distribution histogram. If more than ~50 % of labels cluster near 0 or near 100, the synthetic formula is degenerate; re-tune weights before training.
☐ **After training:** look at feature importance. If `skill_level_encoded` dominates, the label is leaking skill level when it should only gate thresholds. Fix the label, not the model.
☐ **After scenario 3:** read the `reasoning` text for ten rows end-to-end. If it reads like gibberish, the orchestrator prompt update in Plan 4.4 needs another pass. This is cheaper to fix before eval figures are generated.
☐ **After LLM baseline:** spot-check 5 to 10 (scenario, system, run) outputs by hand against the automated rubric in Plan 7.2. If the rubric misses obvious safety violations or hallucinations, patch the rubric, not the results.
☐ **Before thesis submission:** cold-read Chapter 4 against the figures and tables on disk. Any claim in the text that does not have a corresponding file under `evaluation/` or `ml/figures/` is unsupported.

---

## 10. Risk contingencies (decide now, not at 2 a.m.)

The plan lists risks in Section 10. For each, decide the trigger and the response ahead of time.

☐ **NOAA WW3 download fails or is unworkably slow.** Trigger: still debugging by end of Phase 1 day 2. Response: switch the affected spots to Open-Meteo marine hindcasts, document in `DATA_PROVENANCE.md`, move on.
☐ **ML R² below 0.75 on test set.** Triage order (decide now): (1) wider hyperparameter grid, (2) more trees, (3) more training data, (4) narrower target (drop a feature that may be injecting noise), (5) report honestly as a negative result. Do not reorder this under stress.
☐ **LLM baseline produces surprising results** (e.g., GPT-4o matches SurfSense on factual consistency). Write the honest framing now, before the data is in. "SurfSense retains an advantage on safety enforcement and explainability" is a defensible story even if one dimension goes the other way.
☐ **API rate limits during LLM eval.** The cache is the defence. Verify before launching; add exponential-backoff retries with a max cap so a bad minute does not derail the run.
☐ **Forecast drift between scenario development and final figures.** The snapshot + replay mechanism in Plan 5.1 handles this. Confirm every figure caption in Chapter 4 traces to a file under `scenarios/snapshots/`.

---

## 11. Timeline and scheduling

☐ **Block 2 to 3 weeks of calendar time** for the 10 to 16 engineering-day estimate. The buffer absorbs debugging, reviewer turnaround, and life.
☐ **Set a Phase-1 demo day** at end of week 1. Exit criterion: `historical.parquet` has ≥ 80 K rows, no duplicates, missing-value rates documented. If not, escalate (to advisor, or by cutting spots from five to three).
☐ **Reserve the final week before thesis deadline for Chapter 4 writing only.** No code commits in that week except critical fixes. This is non-negotiable; the write-up eats time.
☐ **Identify viva / defence date**, work backward, mark a "code freeze" date at least a week before.
☐ **Protect weekends intentionally.** Solo thesis work on a 10 to 16 day critical path is exactly the shape of problem where burning both weekends trades speed for quality of writing. The plan allows weekends off; defend them.

---

## 12. Thesis writing preparation

Running the code produces artifacts. Turning artifacts into a thesis chapter is a separate craft.

☐ **Draft a glossary / notation list as you go.** SHAP, R², macro F1, MAE, RMSE, Spearman's ρ, TimeSeriesSplit, Gaussian falloff. Reviewers outside ML will need it; so will your examiner on a bad-memory day.
☐ **Write one-sentence figure captions as each figure is generated**, not at the end. Captions are easier when the data is fresh.
☐ **Prepare a data-provenance appendix.** One paragraph per data source (Open-Meteo, NOAA WW3, Stormglass, spot metadata sources) with attribution text, date of access, and license. This is pure copy-paste work if done per source at collection time; it becomes archaeology if left to the end.
☐ **Draft Chapter 4 section headings early.** Match them to the figures and tables inventoried in Plan 8.1 and 8.2. This prevents a figure existing with no home.
☐ **Line up a proofreader** for the final draft. Even a non-technical reader catches hedging verbs and dropped articles that you will have gone blind to.

---

## 13. Submission and defence prep

☐ **Back up everything, redundantly**, at least 72 hours before submission: model file, raw data, notebook outputs, git remote, one additional cold-storage copy (external drive, second cloud).
☐ **Tag the submission commit** in git (`v1.0-submission`) and record the SHA in the thesis appendix.
☐ **Prepare a clean zip of the repo** at the submission SHA, if the institution requires a code appendix. Exclude `.env`, raw data dumps, and notebook checkpoints.
☐ **Record a 2 to 3 minute video demo** of the end-to-end SurfSense flow, including a scenario 3 ML-scored output. This is insurance for defence day if live demo fails.
☐ **Dry-run the defence presentation a week before.** With a timer. Practising against a wall is fine; practising against a labmate is better.
☐ **Prepare a 10-slide backup deck** for anticipated defence questions: "why XGBoost not a neural net?", "why only five spots?", "why synthetic labels instead of crowd-sourced?", "why not run the eval over 100 scenarios?". Each question gets one slide. These rarely get used, but knowing they exist lowers defence-day stress materially.

---

## 14. Final pre-flight before you close this file

Before starting Phase 1 of the implementation plan tomorrow, confirm the following are done:

☐ Supervisor has signed off on scope (Section 2 of this list).
☐ OpenAI and Anthropic keys work, stored in `.env`, `.env` is gitignored (Section 3).
☐ Billing caps are in place (Section 4).
☑ `ml/data/spot_metadata.json` exists with per-spot swell-facing direction and tide band for all five spots (Section 5).
☐ One manual NOAA WW3 request per spot has succeeded, or the substitution to Open-Meteo marine is documented (Section 6).
☐ Dev machine has ≥ 16 GB RAM free and ≥ 20 GB disk (Section 7).
☐ Calendar has 2 to 3 weeks blocked, with the final week reserved for writing (Section 11).

When all seven are ticked, Phase 1 of the implementation plan is safe to start.

---

*End of real-life todos.*
