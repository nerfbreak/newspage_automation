# Tasks: Mobile-First Responsive Design

**Input**: Design documents from `/specs/017-mobile-responsive/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Verify `static/style.css` exists and is linked properly in all Streamlit entrypoints (e.g., `app.py`)
- [X] T002 Create stub for responsive utility functions in `utils.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Ensure custom CSS injection logic is centralized and working in `utils.py` (e.g. `inject_custom_css()`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Mobile UI Navigation and Interaction (Priority: P1) 🎯 MVP

**Goal**: As a mobile user, I want the application layout to dynamically adapt to my small screen size, so that I can view forms, data tables, and interact with buttons clearly without them overlapping, being cut off, or requiring horizontal scrolling to find key actions.

**Independent Test**: Can be fully tested by opening the application on a mobile device emulator (e.g., iPhone 13 or Pixel 5 viewport) and verifying that all forms and buttons are perfectly stacked, accessible, and not overlapping.

### Implementation for User Story 1

- [X] T004 [P] [US1] Add `@media (max-width: 768px)` rules in `static/style.css` forcing `.stColumn` and container classes to `width: 100% !important; flex: 1 1 100% !important;`
- [X] T005 [P] [US1] Adjust button widths and padding inside `@media` queries in `static/style.css` to ensure they are tappable and do not overlap
- [X] T006 [P] [US1] Ensure Streamlit deprecation compliance by removing `use_container_width=True` and replacing with `width='stretch'` in UI calls (e.g. `app.py`, `utils.py`)

**Bugfix**: 2026-07-06 - [BUG-001] No tasks reopened; T006 already covers the required removal of deprecated `use_container_width=True`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Wide Data Table Handling on Mobile (Priority: P2)

**Goal**: As a mobile user viewing reports or data grids, I want to be able to read the data comfortably without the table breaking the page layout or squishing columns to the point of unreadability.

**Independent Test**: Can be tested by loading a large dataset (e.g., 10+ columns) and viewing it on a mobile viewport to ensure the page layout remains intact.

### Implementation for User Story 2

- [X] T007 [US2] Implement a `render_responsive_dataframe(df)` helper function in `utils.py` that formats rows into stacked `st.container` cards for mobile
- [X] T008 [US2] Apply Neo-Brutalism CSS classes to the newly created stacked cards within `static/style.css` (maintaining borders and shadows)
- [X] T009 [US2] Update dataframe rendering calls in data-heavy modules (e.g. `app.py` or specific page files) to use `render_responsive_dataframe(df)` (depends on T007)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T010 [P] Test application comprehensively across varying viewports (320px, 480px, 768px), including portrait/landscape orientation changes and confirming any third-party embeds either resize correctly or are not present in this feature scope
- [X] T011 [P] Verify no existing locked business logic was affected by UI changes
- [X] T012 Run quickstart.md validation

### BUG-002 - Stock Mutation Group Containers

- [X] T013 [US1] Add source-level smoke coverage in `tests/smoke/test_neo_container_css_smoke.py` for the Stock Mutation uploader container and three mapping group containers; confirm the focused test fails before implementation
- [X] T014 [US1] Restore the upload group and dropdown/metric group containers in `pages/4_stock_mutation.py` without modifying upload parsing, session-state behavior, or automation logic (depends on T013)
- [X] T015 [US1] Run focused container smoke tests, Python compilation, and the full offline smoke suite (depends on T014)

**Bugfix**: 2026-07-10 - [BUG-002] Added T013-T015 to restore and verify Stock Mutation Neo-Brutalist group containers. No previously completed task was reopened because the regression was introduced after the original feature completed.

### BUG-003 - Stock Mutation Execution Alignment

- [X] T016 [US1] Add source-level smoke coverage in `tests/smoke/test_neo_container_css_smoke.py` for the page-scoped execution marker and equal desktop table heights; confirm the focused test fails before implementation.
- [X] T017 [US1] Add the zero-height execution marker in `pages/4_stock_mutation.py` and desktop-only 400px paired-table CSS in `static/style.css` without changing table data, progress updates, or automation logic (depends on T016).
- [X] T018 [US1] Run the focused smoke test, Python compilation, full offline smoke suite, and bugfix artifact consistency verification (depends on T017).

**Bugfix**: 2026-07-10 - [BUG-003] Added T016-T018 to align Stock Mutation execution tables and progress indicators on desktop while preserving mobile cards and frozen execution behavior.

### BUG-004 - Stock Mutation Upload Reset Runtime Error

- [x] T019 [US1] Add source-level regression coverage proving the delete button uses a reset callback and direct post-instantiation assignment to `st.session_state.mutasi_file_uploader` is absent; confirm the focused test fails before implementation.
- [x] T020 [US1] Implement a lifecycle-safe uploader reset callback that removes the uploader key and clears `mutasi_file_id` plus `mutasi_review_df`, then bind it through `on_click` without changing parsing or automation behavior (depends on T019).
- [x] T021 [US1] Run focused container/reset tests, Python compilation, full offline smoke tests, readiness audit, and BUG-004 artifact verification (depends on T020).

**Bugfix**: 2026-07-10 - [BUG-004] Added T019-T021 to eliminate the Streamlit widget-state mutation crash while preserving uploader and mutation behavior.

---

## Dependencies & Execution Order

### Execution Wave DAG

- **Wave 1 (Setup & Foundational)**: T001, T002, T003
- **Wave 2 (US1 & US2 Independent Logic)**: T004, T005, T006, T007, T008
- **Wave 3 (US2 Integration)**: T009 (Depends on T007)
- **Wave 4 (Polish)**: T010, T011, T012
- **Wave 5 (BUG-002)**: T013 -> T014 -> T015
- **Wave 6 (BUG-003)**: T016 -> T017 -> T018
- **Wave 7 (BUG-004)**: T019 -> T020 -> T021

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
