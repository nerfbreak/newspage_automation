# Tasks: Add file uploader to manual entry

**Input**: Design documents from /specs/005-manual-entry-uploader/

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Update pages/5_manual_entry.py to import pandas and io

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Ensure state variables for uploaded file data exist in pages/5_manual_entry.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload File and Map Columns (Priority: P1) 🎯 MVP

**Goal**: As a user on the Manual Entry page, I want to optionally upload a data file (Excel/CSV) so that I can automatically populate the entry table without typing everything manually.

**Independent Test**: Can be fully tested by uploading a sample file and verifying that the data maps correctly to the target columns before submission.

### Implementation for User Story 1

- [X] T003 [US1] Add st.file_uploader component to pages/5_manual_entry.py (depends on T002)
- [X] T004 [US1] Implement file parsing logic (pd.read_csv, pd.read_excel) in pages/5_manual_entry.py (depends on T003)
- [X] T005 [US1] Render parsed data preview via st.dataframe in pages/5_manual_entry.py (depends on T004)
- [X] T006 [US1] Add UI dropdowns (st.selectbox) for mapping PAC, CAR, and EA to uploaded columns in pages/5_manual_entry.py (depends on T005)
- [X] T007 [US1] Implement data extraction and injection logic using the mapped columns in pages/5_manual_entry.py (depends on T006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T008 [P] Apply Neo-Brutalist styling classes to any new buttons or elements if needed in pages/5_manual_entry.py

---

## Execution Wave DAG

- **Wave 1**: T001
- **Wave 2**: T002 (depends on T001)
- **Wave 3**: T003 (depends on T002)
- **Wave 4**: T004 (depends on T003)
- **Wave 5**: T005 (depends on T004)
- **Wave 6**: T006 (depends on T005)
- **Wave 7**: T007 (depends on T006)
- **Wave 8**: T008 (depends on T007)

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Implementation Strategy

#### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready
