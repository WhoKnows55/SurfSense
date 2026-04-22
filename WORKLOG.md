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

### Section 5: Per-Spot Domain Research — COMPLETED

- Completed domain research for all 5 spots (Pipeline, Hossegor, Ericeira, Jeffreys Bay, Gold Coast).
- Documented swell-facing direction, preferred tide band, wind-speed ceiling, and break type for each.
- Created `ml/SPOT_RESEARCH_TRACKER.md` as structured research log with per-spot sourcing (Surfline, mechanics articles).
- Consolidated findings into `ml/data/spot_metadata.json` with full metadata, sources, and reproducibility notes.
- Committed both files with audit trail.
- **Flagged issue:** Gold Coast swell direction and tide band incomplete in Surfline surfaced content. Recommend: (1) deeper Surfline search, or (2) field research at target spots. Not a blocker for Phase 1, but should mention to advisor.
- **Pre-flight checklist status:** 4 of 7 pre-flight items now ✅ (supervisor sign-off, API keys, spot_metadata.json). Remaining: billing caps, NOAA WW3 testing, dev machine specs, calendar blocking.
