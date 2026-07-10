# Tasks: Neo-Brutalist Section Headers

**Input**: Design documents from `/specs/029-neo-brutalist-section-headers/`

## Phase 1: Setup & Groundwork
- [x] T001 [P] Identify all `st.subheader` calls in target pages and determine alignment.

## Phase 2: Implementation
- [x] T002 [US1] Replace headers in `pages/4_stock_mutation.py`.
- [x] T003 [US1] Replace headers in `pages/5_clearance_stock.py`.
- [x] T004 [US1] Replace headers in `pages/6_initial_stock.py`.

- [x] T008 [US2/BUG-006] Replace `<h3>` and `---` with Neo-Brutalist elements in `pages/3_promotion_comparison.py`.
- [x] T005 [P] Run Python compilation on modified files.
- [x] T006 [P] Add smoke tests verifying that standard `st.subheader` calls are absent in target files and replaced with `.section-header-underline`.
- [x] T007 [P] Run full smoke test suite and readiness audit.
