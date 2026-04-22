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
  - GPT-4o ❌ — requires AZURE_OPENAI_ENDPOINT env var (optional for Phase 1)
  - Claude ❌ — requires anthropic Python package (optional for Phase 1)
  - **Decision:** SurfSense is the primary system for thesis. LLM baselines are optional comparison context; not required to unblock Phase 1.

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
