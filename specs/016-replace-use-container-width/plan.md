# Implementation Plan: Streamlit Layout Width Deprecation Migration

**Branch**: `016-replace-use-container-width` | **Date**: 2026-07-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-replace-use-container-width/spec.md`

## Table of Contents

- [Summary](#summary)
- [Technical Context](#technical-context)
- [Constitution Check](#constitution-check)
- [Project Structure](#project-structure)
- [Complexity Tracking](#complexity-tracking)

## Summary

Migrate the deprecated `use_container_width` parameter to the modern `width` parameter across the codebase. Specifically, change `use_container_width=True` to `width='stretch'` for all standard Streamlit widgets (buttons, dataframes, images) in the following files:
- `app.py`
- `playwright_engine.py`
- `pages/0_dashboard.py`
- `pages/1_inventory_adjustment.py`
- `pages/2_sales_extraction.py`
- `pages/3_promotion_comparison.py`
- `pages/4_stock_mutation.py`
- `pages/5_clearance_stock.py`
- `pages/6_initial_stock.py`

This will satisfy Streamlit API deprecation requirements without changing any user-facing logic or styling.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Streamlit  
**Storage**: N/A  
**Testing**: Manual validation  
**Target Platform**: Windows / Streamlit Cloud  
**Project Type**: web-service  
**Performance Goals**: N/A  
**Constraints**: Neo-Brutalist design constraints  
**Scale/Scope**: 9 python files containing 30 occurrences of `use_container_width`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (sacred logic)**: No business or automation logic is modified. Only layout width configuration is changed.
- **Principle X (Streamlit Deprecation Compliance - Layout Widths)**: The proposed changes directly enforce compliance with this principle.
- **Gate**: PASS. No violations of design, security, or feature rules.

## Project Structure

### Documentation (this feature)

```text
specs/016-replace-use-container-width/
├── plan.md              # This file
├── research.md          # Research findings (completed)
├── quickstart.md        # Quickstart verification details (completed)
└── checklists/
    └── requirements.md  # Quality checklist (completed)
```

### Proposed Changes

#### [MODIFY] [app.py](../../app.py)
Replace `use_container_width=True` with `width='stretch'` on line 107.

#### [MODIFY] [playwright_engine.py](../../playwright_engine.py)
Replace `use_container_width=True` with `width='stretch'` on line 857.

#### [MODIFY] [0_dashboard.py](../../pages/0_dashboard.py)
Replace `use_container_width=True` with `width='stretch'` on lines 154, 274, and 283.

#### [MODIFY] [1_inventory_adjustment.py](../../pages/1_inventory_adjustment.py)
Replace `use_container_width=True` with `width='stretch'` on lines 93, 124, 129, 164, 200, 297, 304, 318, 425, and 428.

#### [MODIFY] [2_sales_extraction.py](../../pages/2_sales_extraction.py)
Replace `use_container_width=True` with `width='stretch'` on lines 78, 84, and 89.

#### [MODIFY] [3_promotion_comparison.py](../../pages/3_promotion_comparison.py)
Replace `use_container_width=True` with `width='stretch'` on lines 73, 108, and 163.

#### [MODIFY] [4_stock_mutation.py](../../pages/4_stock_mutation.py)
Replace `use_container_width=True` with `width='stretch'` on lines 91 and 174.

#### [MODIFY] [5_clearance_stock.py](../../pages/5_clearance_stock.py)
Replace `use_container_width=True` with `width='stretch'` on lines 68, 74, and 166.

#### [MODIFY] [6_initial_stock.py](../../pages/6_initial_stock.py)
Replace `use_container_width=True` with `width='stretch'` on lines 79, 122, 161, and 203.

## Complexity Tracking

No violations or deviations exist. No extra components are introduced.
