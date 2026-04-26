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
