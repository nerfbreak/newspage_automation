# Implementation Plan: Neo Brutalism Tables

**Branch**: `032-neo-brutalism-tables` | **Date**: 2026-07-10
**Spec**: [specs/032-neo-brutalism-tables/spec.md](specs/032-neo-brutalism-tables/spec.md)

## Goal

Apply Neo-Brutalist grid borders to all tables across the entire Streamlit application by modifying the global CSS.

## Implementation Strategy

- Single-point injection via global `style.css`.
- Use Streamlit's container structure to scope `table` and `th`/`td` selectors safely.
- Ensure existing dataframe rendering (like the Inventory Adjustment review) aligns with the new grid.

## Task Breakdown

| ID | Task | Deps | Status |
|---|---|---|---|
| 1.0 | [style.css] Inject table grid CSS into `style.css` | None | Pending |

## Verification Plan

- Open a page containing a table (like the Inventory Adjustment result table).
- Visually confirm `th` and `td` have `border: 2px solid #0F172A` or `3px solid #0F172A` grid lines.
- Verify no layout breakage in the rest of the app.
