# Tasks: Success Screenshot

**Input**: Design documents from `/specs/004-success-screenshot/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

*(No setup tasks required. Infrastructure already exists.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

*(No foundational changes required. `send_telegram_alert` already accepts `photo_path`.)*

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Task Completion Screenshot (Priority: P1) 🎯 MVP

**Goal**: Deliver a screenshot of the final browser screen to Telegram upon successful bot task completion.

**Independent Test**: Can be fully tested by running a dummy extraction and verifying that a success message with a photo arrives in Telegram.

### Implementation for User Story 1

- [X] T001 [US1] Inject screenshot capture logic before logout in `run_extract` in `c:\Users\Reckitt\Documents\Optimize\playwright_engine.py`
- [X] T002 [US1] Inject screenshot capture logic before logout in `run_sales_extract` in `c:\Users\Reckitt\Documents\Optimize\playwright_engine.py` (depends on T001)
- [X] T003 [US1] ⚠️ Reopened: Inject screenshot capture logic before logout in `run_execution` in `c:\Users\Reckitt\Documents\Optimize\playwright_engine.py` (depends on T002) *(reopened & completed — BUG-001: must navigate to List View and search first)*
- [X] T004 [US1] ⚠️ Reopened: Inject screenshot capture logic before logout in `run_execution_manual` in `c:\Users\Reckitt\Documents\Optimize\playwright_engine.py` (depends on T003) *(reopened & completed — BUG-001: must navigate to List View and search first)*
- [X] T005 [US1] Inject screenshot capture logic before logout in `run_mutasi_execution` in `c:\Users\Reckitt\Documents\Optimize\playwright_engine.py` (depends on T004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T006 Manual end-to-end testing of the full automation flow to ensure screenshots are delivered.

---

## Execution Wave DAG

- **Wave 1**: T001
- **Wave 2**: T002
- **Wave 3**: T003
- **Wave 4**: T004
- **Wave 5**: T005
- **Wave 6**: T006

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Parallel Opportunities

- The tasks are modifying the same file `playwright_engine.py` sequentially to avoid merge conflicts.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3: User Story 1
2. **STOP and VALIDATE**: Test User Story 1 independently
3. Deploy/demo if ready

---
**Bugfix**: 2026-07-04 — [BUG-001] Updated from bugfix patch.
