# Implementation Plan: Friendly Extraction Terminal Logs

**Branch**: `020-friendly-extract-logs` | **Date**: 2026-07-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/020-friendly-extract-logs/spec.md`

**Note**: This plan is filled for the `/speckit-plan` workflow.

## Table of Contents

- [Summary](#summary)
- [Technical Context](#technical-context)
- [Constitution Check](#constitution-check)
- [Project Structure](#project-structure)
- [Complexity Tracking](#complexity-tracking)

## Summary

Improve user-facing terminal log wording for extraction flows so operations users
can understand what the bot is doing during inventory and sales extraction. The
implementation will keep the existing terminal renderer and Playwright flow intact,
changing only selected log message text and adding focused smoke coverage for the
friendly wording.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Streamlit, Playwright, Pandas, Supabase client, standard
library `unittest`

**Storage**: Existing Streamlit session state for extraction outputs and existing
Supabase extraction logs. No schema changes.

**Testing**: Python `unittest` smoke suite under `tests/smoke`

**Target Platform**: Windows local development and Streamlit Cloud deployment

**Project Type**: Streamlit web app with Playwright browser automation

**Performance Goals**: No measurable runtime impact. Log wording changes must not
add waits, new browser actions, or extra network/database operations.

**Constraints**: Do not change Playwright selectors, portal navigation behavior,
download behavior, generated files, Supabase logging, credentials, or session
management. Preserve Neo-Brutalist UI and current terminal rendering.

**Scale/Scope**: User-visible extraction terminal messages for inventory and sales
extraction, plus shared download/helper messages used by those flows.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I - Feature Freeze**: PASS with unlock caution. Extraction modules
  are frozen; this plan limits changes to user-facing log text and smoke coverage.
  No selectors, transaction behavior, credentials, or data outputs may change.
- **Principle II - Security-First Credential Handling & Session Protection**:
  PASS. Messages must not expose credentials, cookies, secrets, raw stack traces,
  or unsafe user data.
- **Principle III - Selector Integrity**: PASS. No selector changes are planned.
- **Principle IV - UI Consistency**: PASS. Terminal renderer and styling remain
  unchanged.
- **Principle V - Session & Logging Integrity**: PASS. Supabase execution logs and
  Streamlit session state behavior remain unchanged.
- **Principle XI - Mobile-First Responsive Design**: PASS. Log text must remain
  concise enough for terminal display on smaller screens.
- **Principle XII - Minimal & Clean Dependency Architecture**: PASS. No new
  dependency is required.

Post-design re-check: PASS. Research and design artifacts keep the change scoped
to wording-only updates plus tests.

## Project Structure

### Documentation (this feature)

```text
specs/020-friendly-extract-logs/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── terminal-log-messages.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
playwright_engine.py
tests/smoke/test_friendly_extract_logs_smoke.py
.agents/MEMORY.md
.agents/CURRENT_HANDOFF.md
```

**Structure Decision**: Keep the change inside the existing extraction automation
boundary. `playwright_engine.py` owns the user-visible automation log messages;
`utils.py` terminal rendering remains unchanged because the request is language
clarity, not visual redesign.

## Complexity Tracking

No constitution violations or exceptional complexity are required.
