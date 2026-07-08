# Tasks: Session Invalidation on Password Rotation

**Input**: Design documents from `/specs/019-session-invalidation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/remembered-session.md, quickstart.md

**Tests**: Required for this authentication/security feature.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel once dependencies are satisfied
- **[Story]**: User story label from spec.md
- Every task includes exact file paths and explicit dependencies when applicable

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare additive schema docs and inspect current auth boundaries.

- [X] T001 Confirm current auth cookie and password lookup behavior in `app.py` and `database.py`
- [X] T002 Add password/session metadata migration notes to `docs/database_migrations.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add reusable session-version helpers before changing app login flow.

**CRITICAL**: No user story work can start until these helpers exist.

- [X] T003 [P] Add user session metadata helpers in `database.py`
- [X] T004 [P] Add encrypted remembered-session payload helpers in `database.py`
- [X] T005 Add smoke tests for session metadata and payload helpers in `tests/smoke/test_auth_session_smoke.py` (depends on T003, T004)

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Revoke Old Persistent Sessions (Priority: P1) MVP

**Goal**: Remembered sessions created before password rotation are rejected.

**Independent Test**: A stale remembered-session payload with an old version fails validation and does not grant access.

### Tests for User Story 1

- [X] T006 [P] [US1] Add stale remembered-session rejection tests in `tests/smoke/test_auth_session_smoke.py` (depends on T005)
- [X] T007 [P] [US1] Add legacy username-only cookie rejection test in `tests/smoke/test_auth_session_smoke.py` (depends on T005)

### Implementation for User Story 1

- [X] T008 [US1] Update auto-login gate in `app.py` to validate remembered-session payload against current user metadata (depends on T006, T007)
- [X] T009 [US1] Clear invalid/stale cookies and fail closed in `app.py` without exposing raw cookie details (depends on T008)

**Checkpoint**: Old remembered sessions no longer bypass password rotation.

---

## Phase 4: User Story 2 - Preserve Valid User Convenience (Priority: P2)

**Goal**: Valid remembered sessions still work when the user's credential state has not changed.

**Independent Test**: A remembered-session payload with a matching current version validates successfully.

### Tests for User Story 2

- [X] T010 [P] [US2] Add valid remembered-session acceptance tests in `tests/smoke/test_auth_session_smoke.py` (depends on T005)
- [X] T011 [P] [US2] Add successful password login metadata bootstrap tests in `tests/smoke/test_auth_session_smoke.py` (depends on T005)

### Implementation for User Story 2

- [X] T012 [US2] Update successful login flow in `app.py` to ensure current session metadata before setting the cookie (depends on T010, T011)
- [X] T013 [US2] Update cookie issuance in `app.py` to store the encrypted structured remembered-session payload (depends on T012)

**Checkpoint**: Normal remembered-login convenience remains intact.

---

## Phase 5: User Story 3 - Support Safe Operations and Audits (Priority: P3)

**Goal**: Maintain repeatable security evidence and docs without leaking secrets.

**Independent Test**: Smoke and audit tests pass without printing passwords, hashes, raw cookies, or secrets.

### Tests for User Story 3

- [X] T014 [P] [US3] Update security audit smoke assertions in `tests/smoke/test_security_audit_smoke.py` (depends on T013)

### Implementation for User Story 3

- [X] T015 [US3] Document password rotation SQL pattern with session metadata in `docs/database_migrations.md` (depends on T014)
- [X] T016 [US3] Update production readiness notes in `docs/production_readiness_status.md` (depends on T015)
- [X] T017 [US3] Update `.agents/MEMORY.md` changelog with session invalidation completion (depends on T016)

**Checkpoint**: Security evidence and operational docs are complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and Spec-Kit evidence.

- [X] T018 Run `python scripts\production_readiness_audit.py` (depends on T017)
- [X] T019 Run `python -m unittest discover -s tests\smoke` (depends on T017)
- [X] T020 Run `python scripts\supabase_schema_check.py` if schema docs changed or live metadata verification is needed (depends on T017)
- [X] T021 Run `python scripts\supabase_rls_index_check.py` if schema docs changed or live metadata verification is needed (depends on T017)
- [X] T022 Update task checkboxes in `specs/019-session-invalidation/tasks.md` after implementation and verification (depends on T018, T019)

**Bugfix**: 2026-07-08 - [BUG-001] Active Streamlit sessions must be invalidated when credential-version metadata changes.

- [X] T023 [US1] Store the accepted credential-version marker in `st.session_state.current_session_version` for password login and remembered-cookie auto-login (depends on T008, T012)
- [X] T024 [US1] Revalidate logged-in Streamlit sessions against `users_auth.session_version` on rerun and clear stale sessions/cookies in `app.py` (depends on T023)
- [X] T025 [US3] Add smoke coverage proving active-session revalidation is present in `app.py` without exposing secrets (depends on T024)
- [X] T026 Run `python -m unittest discover -s tests\smoke` and `python scripts\production_readiness_audit.py` after BUG-001 implementation (depends on T025)

**Bugfix**: 2026-07-08 - [BUG-002] Manual Entry progress bar must reach 100% after successful completion.

- [X] T027 Add smoke coverage in `tests/smoke/test_manual_progress_smoke.py` proving default Manual Entry progress reaches `1.0` on success
- [X] T028 Patch `playwright_engine.py` so `run_execution_manual()` updates the active progress bar object and finalizes it at success
- [X] T029 Run focused smoke test, full smoke suite, and production readiness audit after BUG-002 implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion.
- **US1 (Phase 3)**: Depends on Foundational completion.
- **US2 (Phase 4)**: Depends on Foundational completion, but implementation follows US1 to minimize auth-gate conflicts.
- **US3 (Phase 5)**: Depends on US1 and US2 implementation.
- **Polish (Phase 6)**: Depends on all user stories.

### Execution Wave DAG

- **Wave 1**: T001, T002
- **Wave 2**: T003, T004
- **Wave 3**: T005
- **Wave 4**: T006, T007, T010, T011
- **Wave 5**: T008
- **Wave 6**: T009
- **Wave 7**: T012
- **Wave 8**: T013
- **Wave 9**: T014
- **Wave 10**: T015
- **Wave 11**: T016
- **Wave 12**: T017
- **Wave 13**: T018, T019, T020, T021
- **Wave 14**: T022

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational tasks.
2. Complete US1 stale-session rejection.
3. Verify stale cookies fail closed before improving valid-session convenience.

### Incremental Delivery

1. US1: revoke old sessions after password rotation.
2. US2: ensure valid remembered sessions keep working.
3. US3: update docs and audit evidence.

### Parallel Opportunities

- T003 and T004 can be implemented together because both are helper additions in `database.py` but should be coordinated carefully.
- T006, T007, T010, and T011 are independent test cases once helper tests exist.
- Final verification commands can run in parallel where network approvals permit.
