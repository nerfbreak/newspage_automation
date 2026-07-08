# Tasks: Friendly Extraction Terminal Logs

**Input**: Design documents from `/specs/020-friendly-extract-logs/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/terminal-log-messages.md, quickstart.md

**Tests**: Focused smoke coverage is required by SC-004.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Confirm current extraction log locations and frozen boundaries.

- [X] T001 Inspect existing extraction log calls in `playwright_engine.py` for `run_extract()`, `run_sales_extract()`, and shared download helpers.
- [X] T002 Inspect existing terminal logger tests in `tests/smoke/` to match project smoke-test style.

---

## Phase 2: Foundational

**Purpose**: Add test scaffolding before changing wording.

- [X] T003 Create focused friendly extraction log smoke tests in `tests/smoke/test_friendly_extract_logs_smoke.py`.
- [X] T004 Run `python -m unittest tests.smoke.test_friendly_extract_logs_smoke` and confirm the new tests fail before implementation.

**Checkpoint**: Tests prove the current wording does not meet the friendly-log contract.

---

## Phase 3: User Story 1 - Understand Extraction Progress (Priority: P1)

**Goal**: Happy-path extraction logs clearly explain preparation, search/download, packaging, and completion.

**Independent Test**: Focused smoke tests detect friendly wording for representative happy-path extraction messages.

### Implementation for User Story 1

- [X] T005 [US1] Update inventory extraction happy-path log messages in `playwright_engine.py`.
- [X] T006 [US1] Update sales extraction happy-path log messages in `playwright_engine.py`.
- [X] T007 [US1] Update shared extraction download helper log messages in `playwright_engine.py`.
- [X] T008 [US1] Run `python -m unittest tests.smoke.test_friendly_extract_logs_smoke` and confirm friendly happy-path message tests pass.

**Checkpoint**: A user can identify the extraction phase from terminal logs.

---

## Phase 4: User Story 2 - Understand Recoverable Waits and Failures (Priority: P2)

**Goal**: Wait, no-data, and failure messages are understandable without exposing secrets or raw internals.

**Independent Test**: Focused smoke tests detect that representative changed messages avoid old jargon and unsafe wording.

### Implementation for User Story 2

- [X] T009 [US2] Update extraction wait and no-result/fallback messages in `playwright_engine.py` without changing control flow.
- [X] T010 [US2] Update focused smoke tests in `tests/smoke/test_friendly_extract_logs_smoke.py` for wait/failure wording expectations.
- [X] T011 [US2] Run `python -m unittest tests.smoke.test_friendly_extract_logs_smoke`.

**Checkpoint**: Wait and issue states tell the user what happened and what to expect.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Verify no behavior drift and update shared memory.

- [X] T012 Run `python -m unittest discover -s tests\smoke`.
- [X] T013 Run `python scripts\production_readiness_audit.py`.
- [X] T014 Update `.agents/CURRENT_HANDOFF.md` with the feature status and verification results.
- [X] T015 Append a concise summary to `.agents/MEMORY.md` under `Changelog & Decisions`.
- [X] T016 Review `git diff --check` and `git status --short --branch --untracked-files=all`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion.
- **US1 (Phase 3)**: Depends on failing focused tests from Phase 2.
- **US2 (Phase 4)**: Depends on US1 message mapping so wait/failure wording stays consistent.
- **Polish (Phase 5)**: Depends on US1 and US2 completion.

### User Story Dependencies

- **US1**: First because happy-path extraction progress is the core user value.
- **US2**: Follows US1 to apply the same wording style to waits and issues.

### Parallel Opportunities

- T001 and T002 can be reviewed independently.
- T005 and T006 can be edited independently if both respect shared helper wording from T007.
- T014 and T015 can be prepared after verification results are known.

## Implementation Strategy

### MVP First

1. Complete T001-T004.
2. Complete US1 (T005-T008).
3. Validate focused smoke tests.

### Full Delivery

1. Complete US2 (T009-T011).
2. Run full smoke and production readiness checks.
3. Update handoff and memory.

## Notes

- Do not modify selectors, waits, clicks, downloads, file parsing, Supabase logging,
  credentials, or session management.
- This feature is intentionally wording-only inside frozen extraction flows.
