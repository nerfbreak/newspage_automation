# Spec 030 — Center Column Mapping Headers

**Status**: Draft
**Created**: 2026-07-10
**Constitution Alignment**: Principle IV (Neo-Brutalism UI Consistency)

## Summary

Center-align the "Column Mapping" / "Mapping Kolom" section headers on the Stock Mutation and Inventory Adjustment pages to match the centered Neo-Brutalist header pattern used across the application.

## Motivation

Currently the column mapping titles use inconsistent alignment:
- `pages/4_stock_mutation.py` uses `header-wrapper-left` (left-aligned).
- `pages/1_inventory_adjustment.py` uses a raw inline `<div>` with `<b>` tag, without the standard Neo-Brutalist `.section-header-underline` component.

All section headers should use the centered `header-wrapper-center` class with the `.section-header-underline` span to maintain design consistency per the locked design system.

## Scope

- **In scope**: Changing the HTML markup of column mapping titles to use `header-wrapper-center` + `section-header-underline`.
- **Out of scope**: Business logic, Playwright selectors, column mapping functionality, any other pages.

## User Stories

### US-001: Consistent Column Mapping Header Alignment (Priority: P2)

As an operations user, I want the "Column Mapping" section headers to be visually centered and styled consistently with the rest of the application, so the UI feels cohesive.

**Acceptance Scenarios**:
1. **Given** the Stock Mutation page with a file uploaded, **When** the Column Mapping section renders, **Then** the "Column Mapping" header is center-aligned and uses the `section-header-underline` Neo-Brutalist component.
2. **Given** the Inventory Adjustment Manual Entry with a file uploaded, **When** the Mapping Kolom section renders, **Then** the "Mapping Kolom" header is center-aligned and uses the `section-header-underline` Neo-Brutalist component.

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-001 | `pages/4_stock_mutation.py` line 116: Change `header-wrapper-left` to `header-wrapper-center` |
| FR-002 | `pages/1_inventory_adjustment.py` line 309: Replace raw `<div style='margin-bottom:10px;'><b>Mapping Kolom:</b></div>` with `<div class='header-wrapper-center'><span class='section-header-underline'>Column Mapping</span></div>` |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NF-001 | No changes to column mapping logic, selectbox behavior, or data processing |
| NF-002 | No changes to Playwright selectors or automation engine |
| NF-003 | Must pass existing smoke test suite without regressions |

## Assumptions

- The `header-wrapper-center` and `section-header-underline` CSS classes already exist in `static/style.css` and are proven.
- No new CSS is needed.

## Risks

- None identified. This is a pure HTML class swap on two lines.
