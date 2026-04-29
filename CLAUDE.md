# SurfSense — Claude Instructions

## Project in one sentence
SurfSense is a multi-agent surf-condition advisor built for a master's thesis. The code is both the deliverable **and** the evidence base for Chapter 4. Every engineering decision must be traceable to a thesis section.

---

## Tracking files — read these first on every session

These four files are the ground truth for what has been done and what still needs to happen. Always read whichever ones are relevant before starting work. Never skip them.

### 1. `WORKLOG.md` — session log (append-only)
**Purpose:** Provenance record. Panels and supervisors use this to reconstruct decisions.
**When to write:**
- At the end of every working session, add a dated entry (`## YYYY-MM-DD`) summarising what was done, any decisions made, and any blockers.
- When a decision changes something in the thesis text, also reference the relevant `THESIS_CHANGES.md` item.
- Never edit past entries. Append only.

**Format:**
```
## YYYY-MM-DD
- bullet: what was done
- **Decision — topic:** what was decided and why
```

### 2. `THESIS_CHANGES.md` — the most important file in the project
**Purpose:** Every place in the thesis document that must be updated because of a coding or data decision. This is what Joshua writes into the actual thesis Word/LaTeX document.

**Status legend:** `☐` not done · `☑` done

**When to write:**
- Whenever a coding or data choice diverges from what the thesis currently says, add a new entry immediately. Do not wait.
- Each entry has four fields: **Where** (chapter/section), **Current text (paraphrase)**, **New text / action**, **Why**.
- When the thesis document has been updated, mark the item `☑`.

**When to read:**
- Before starting any work in `ml/`, `evaluation/`, or `app/agents/` — to avoid re-introducing something the thesis has already been updated away from.
- Before writing any thesis text — to pick up the correct values.

### 3. `SurfSense_Evaluation_Implementation_Plan.md` — technical checklist
**Purpose:** The engineering roadmap. Each item is a concrete coding task with acceptance criteria.

**Status legend:** `☐` not started · `◐` partial · `☑` done

**When to write:**
- Mark items `☑` immediately when done. Do not batch.
- If a task is partially done, mark `◐` and add a note on what remains.
- If a task is abandoned or superseded, add a strikethrough note and explain why.

**When to read:**
- At session start, to pick the next unblocked `☐` item.
- Before touching `ml/`, `evaluation/`, or `scenarios/` code — to confirm which phase is active.

### 4. `SurfSense_Evaluation_RealLife_Todos.md` — non-coding checklist
**Purpose:** Credentials, supervisor sign-offs, reproducibility decisions, environment checks — all the things that block the coding plan from the outside.

**Status legend:** `☐` not started · `◐` in progress · `☑` done

**When to write:**
- Mark items `☑` as they are confirmed. Add a parenthetical with the date.
- If a decision is made here, also log it in `WORKLOG.md`.

**When to read:**
- At session start, to check whether any blockers have been resolved or newly appeared.

---

## Secondary reference files (read-only for most sessions)

| File | What it is | When to read |
|------|-----------|--------------|
| `SurfSense_Implementation_Plan.md` | Original architectural plan (written before ML work). Describes the agentic architecture, agent tools, and orchestrator design. | When touching `app/` code and needing to understand the intended architecture. |
| `ml/SPOT_RESEARCH_TRACKER.md` | Per-spot physical parameters (swell direction, tide band, wind ceiling). | When touching `ml/labels.py` or `data/spots.json`. |
| `ml/labels_references.md` | Academic sources grounding the synthetic label formula. | When writing or modifying the label function, or when drafting thesis commentary on label design. |
| `ml/data/DATA_PROVENANCE.md` | Data source decisions (Open-Meteo Marine over NOAA, UTC timestamps, tide NaN handling). | When touching `ml/data/` or writing Section 3.3.3 / appendix text. |

---

## Directory map — what lives where

```
app/                    # Runtime agentic system
  agents/               # orchestrator, research, forecast, condition, trip planning agents
  planning/             # scoring.py (rule-based + ML scoring)
config/                 # settings.py — Pydantic settings loaded from .env
data/                   # spots.json — spot registry
evaluation/             # evaluation harnesses
  llm_baseline/         # driver.py (runs SurfSense + GPT-4o-mini), score.py (5-dimension rubric), results.csv
ml/                     # everything ML
  data/                 # collect.py, historical.parquet, spot_metadata.json, DATA_PROVENANCE.md
  models/               # surf_condition_model.joblib, model_metadata.json
  figures/              # training plots and SHAP plots (generated, not hand-edited)
  notebooks/            # 01_eda.ipynb — EDA only; not for training code
  train.py              # model training entry point
  labels.py             # synthetic label formula
  splits.py             # train/val/test split logic
scenarios/              # scripted demonstration scripts (01, 02, 03) + snapshots/
tests/                  # pytest test suite
```

---

## Thesis chapter map — where code decisions land

| Code area | Thesis section |
|-----------|----------------|
| `app/agents/forecast_data_agent.py` | 3.3.3 — Forecast Data Agent / data sources |
| `ml/data/collect.py`, `historical.parquet` | 3.3.5 — Training data; Appendix — Data provenance |
| `ml/labels.py` | 3.3.5 — Synthetic label formula |
| `ml/train.py`, `ml/models/` | 3.3.5 — Model choice and hyperparameters |
| `evaluation/llm_baseline/score.py` | 3.5.2 — Five-dimension scoring rubric |
| `evaluation/llm_baseline/results.csv` | 4.3 — LLM baseline results table |
| `scenarios/` | 3.4 — Demonstration scenarios; 4.1 — Scenario walkthroughs |
| SHAP figures in `ml/figures/` | 4.2 — Internal baseline, SHAP paragraph |

**Rule:** whenever a file in the left column changes in a way that diverges from what the thesis currently says, add an entry to `THESIS_CHANGES.md` in the same session.

---

## Key decisions already made (do not reopen)

- **Wave data:** Open-Meteo Marine API for all five spots. NOAA WW3 dropped entirely.
- **LLM comparison:** SurfSense vs GPT-4o-mini only. Claude dropped from evaluation.
- **ML model:** `HistGradientBoostingRegressor` (sklearn). XGBoost dropped (libomp unavailable).
- **Tide data:** `tide_height_m` = NaN throughout; imputed to per-spot preferred midpoint at training time. Documented as a known limitation.
- **Timestamps:** all UTC. IANA timezone identifiers in `spots.json` are metadata only.
- **Azure OpenAI:** university deployment. All LLM calls (orchestrator + GPT-4o-mini baseline) go through the same `AZURE_OPENAI_*` env vars.
- **Random seed:** 42 everywhere in `ml/`.
- **Chapter 4 structure:** (1) scenario walkthroughs, (2) internal baseline (ML vs rule-based), (3) LLM baseline. Confirmed with Prof. Jardim.

---

## Open items that still need to happen (as of 2026-04-27)

These are unresolved `☐` items across the checklists. Do not mark them done here — mark them in the source file.

**In `THESIS_CHANGES.md` (thesis document edits still pending):**
- 3.3.3 — Remove NOAA WW3, add Open-Meteo Marine description
- 3.3.3 — Tide limitation paragraph
- 3.3.3 — UTC timestamps clarification
- 3.3.5 — Replace XGBoost references with HGBR everywhere
- 3.3.5 — Update hyperparameter grid parameter names to HGBR API
- 3.5.2 — Add evaluation design asymmetry framing sentence (GPT-4o-mini gets injected data; SurfSense does live API calls)
- 3.5.2 — Update scoring rubric description to match revised `score.py`
- 3.5.2 — Remove Claude from systems compared; two-system comparison only
- 4.1 — Figure captions tracing to `scenarios/snapshots/` files
- 4.2 — SHAP paragraph (draft text is already written in `THESIS_CHANGES.md` — copy it in)
- 4.3 — LLM baseline five-dimension table (results are in `THESIS_CHANGES.md` — copy them in)
- Appendix — Data provenance (copy from `ml/data/DATA_PROVENANCE.md`)
- Appendix — Submission commit SHA (after tagging `v1.0-submission`)

**In `SurfSense_Evaluation_RealLife_Todos.md` (reproducibility):**
- Pin exact package versions in `requirements.txt` before final training run
- Pick model-versioning convention (single file vs. dated)
- Decide: commit model + parquet files to git, or release assets / manifest
- Prompt versioning: commit `evaluation/llm_baseline/prompt_template.txt`

---

## Coding conventions

- Python package: single `.venv` at repo root. All ML and app dependencies share it.
- Settings: loaded via `config/settings.py` (Pydantic). Secrets in `.env` (never committed).
- Tests: `pytest` from repo root. Snapshot-replay tests use files under `scenarios/snapshots/`.
- No comments unless the why is non-obvious. No docstrings unless the function is a public API boundary.

---

## Before finishing any session

1. Update `WORKLOG.md` with what was done and any decisions made.
2. If any code change diverges from the thesis: add an entry to `THESIS_CHANGES.md`.
3. If a checklist item is now complete: mark it `☑` in the relevant plan file.
