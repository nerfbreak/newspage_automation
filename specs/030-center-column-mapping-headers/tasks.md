# Tasks 030 — Center Column Mapping Headers

**Spec**: specs/030-center-column-mapping-headers/spec.md
**Plan**: specs/030-center-column-mapping-headers/plan.md

## Tasks

- [x] T001: Change `header-wrapper-left` → `header-wrapper-center` in `pages/4_stock_mutation.py` line 116 (FR-001)
- [x] T002: Replace raw inline `<div>` with Neo-Brutalist `header-wrapper-center` + `section-header-underline` in `pages/1_inventory_adjustment.py` line 309 (FR-002)
- [x] T003: Python compilation check on both modified files
- [x] T004: Run full offline smoke test suite — confirm 0 regressions

## Dependencies

None — all tasks are independent of each other except T003/T004 depend on T001/T002.
