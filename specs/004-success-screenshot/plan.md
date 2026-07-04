# Implementation Plan: Success Screenshot

**Branch**: `004-success-screenshot` | **Date**: 2026-07-04 | **Spec**: [spec.md](file:///c:/Users/Reckitt/Documents/Optimize/specs/004-success-screenshot/spec.md)
**Input**: Feature specification from `/specs/004-success-screenshot/spec.md`

## Table of Contents

- [Summary](#summary)
- [Technical Context](#technical-context)
- [Constitution Check](#constitution-check)
- [Project Structure](#project-structure)
- [Complexity Tracking](#complexity-tracking)

## Summary

Add a feature to capture a screenshot of the browser right before the logout sequence upon successful task completion, and pass this screenshot to the Telegram alert callback. This requires surgical modifications to `playwright_engine.py` across extraction and execution workflows.
*(BUG-001)*: For execution workflows, the bot will specifically navigate to the list view, filter by today's date, and search to ensure the screenshot captures the actual transaction record.

## Technical Context

**Language/Version**: Python 3.x
**Primary Dependencies**: Streamlit, Playwright
**Storage**: N/A (Local filesystem for temporary screenshots)
**Testing**: Manual End-to-End
**Target Platform**: Windows / Streamlit Deployment
**Project Type**: Automation Bot
**Performance Goals**: N/A
**Constraints**: Must not add significant overhead to successful task completion (< 3s).
**Scale/Scope**: Impacts all Playwright automation functions in `playwright_engine.py`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Feature Freeze — Verified Logic Is Sacred**: PASS. Modifying `playwright_engine.py` requires explicit user authorization. The user has provided the unlock password ("Dama") in the current session, so we are authorized to proceed.
- **II. Security-First Credential Handling**: PASS. No credentials exposed or modified.
- **III. Selector Integrity — No Guessing Allowed**: PASS. No new selectors required.
- **IV. UI Consistency — Flat & Premium Design**: PASS. No UI changes.
- **V. Session & Logging Integrity**: PASS. Existing logging remains unaffected.

## Project Structure

### Documentation (this feature)

```text
specs/004-success-screenshot/
├── plan.md              # This file
├── research.md          # Minimal - no external unknowns
├── data-model.md        # N/A
├── quickstart.md        # N/A
└── tasks.md             # To be generated
```

### Source Code (repository root)

```text
app.py
pages/
utils.py
playwright_engine.py      # Modified to inject screenshot logic
data_processor.py
database.py
```

**Structure Decision**: Using existing single-project structure. Modifications are contained entirely within `playwright_engine.py`.

## Complexity Tracking

None.

---
**Bugfix**: 2026-07-04 — [BUG-001] Updated from bugfix patch.
