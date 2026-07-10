# Implementation Plan: Mobile-First Responsive Design

**Branch**: `017-mobile-responsive` | **Date**: 2026-07-05 | **Spec**: [spec.md](file:///c:/Users/Reckitt/Documents/Optimize/specs/017-mobile-responsive/spec.md)
**Input**: Feature specification from `/specs/017-mobile-responsive/spec.md`

## Table of Contents
- [Summary](#summary)
- [Technical Context](#technical-context)
- [Constitution Check](#constitution-check)
- [Project Structure](#project-structure)
- [Complexity Tracking](#complexity-tracking)

## Summary
Implement dynamic responsive design for mobile viewports across the application, ensuring that forms, inputs, and buttons stack neatly without overlapping, and wide data tables convert to stacked card-based layouts. The changes will strictly maintain the existing Neo-Brutalism design system.

## Technical Context

**Language/Version**: Python 3.x
**Primary Dependencies**: Streamlit
**Storage**: N/A (UI only)
**Testing**: Manual UI verification via mobile viewport simulation
**Target Platform**: Web browsers (Mobile & Desktop)
**Project Type**: Streamlit Web Application
**Performance Goals**: Instant layout reflow without JS lag (pure CSS/Streamlit native where possible)
**Constraints**: Streamlit's limited native layout control requires clever CSS overrides and column adjustments.
**Scale/Scope**: CSS file (`static/style.css`) and layout wrapper functions in `utils.py` and `app.py`/`pages/`.

**Bugfix**: 2026-07-10 - [BUG-003] Equalize the two Stock Mutation desktop execution table viewports with a page-scoped marker and CSS rule using the existing 400px table cap. Keep `render_responsive_dataframe()`, mobile cards, progress updates, and automation behavior unchanged.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle XI (Mobile-First Responsive Design)**: Validated. This plan directly implements this principle.
- **Principle IV (UI Consistency — Flat & Premium Design)**: Validated. All responsive changes will maintain Neo-Brutalism (solid `#FFFFFF` background, thick borders, sharp corners, no glassmorphism).
- **Principle X (Streamlit Deprecation Compliance — Layout Widths)**: Validated. Will use `width` parameters instead of `use_container_width`.
- **Bugfix**: 2026-07-06 - [BUG-001] Confirmed mobile responsive work must use Streamlit `width` parameters only; deprecated `use_container_width` remains disallowed.
- **Principle I (Feature Freeze)**: Validated. UI layout changes will not alter any frozen backend/automation business logic.
- **Bugfix**: 2026-07-10 - [BUG-002] Restore only the missing `st.container(border=True)` wrappers in `pages/4_stock_mutation.py` and add source-level smoke coverage; upload parsing, session-state transitions, Playwright selectors, and execution behavior remain unchanged.
- **Bugfix**: 2026-07-10 - [BUG-003] Limit the alignment patch to a zero-height marker in `pages/4_stock_mutation.py` and desktop-only CSS in `static/style.css`; do not modify dataframe values, Playwright selectors, progress calculations, or execution sequencing.

## Project Structure

### Documentation (this feature)

```text
specs/017-mobile-responsive/
├── plan.md              
├── research.md          
├── data-model.md        
└── quickstart.md        
```

### Source Code (repository root)

```text
# Single project (DEFAULT)
static/
└── style.css            # Will contain @media queries for responsive adjustments

pages/
└── [all page files]     # Update layout logic for dataframe-to-card transformations on mobile

utils.py                 # Potential responsive helper functions for Streamlit columns
```

**Structure Decision**: Will utilize the existing Streamlit app structure. `static/style.css` will be heavily updated with `@media (max-width: 768px)` rules to handle Streamlit container stacking.

**Bugfix implementation note**: BUG-002 is a page-structure correction rather than a CSS redesign. The uploader feedback belongs inside one marker-backed bordered container. Each of the three mapping columns must create one marker-backed bordered container containing its dropdown and a metric placeholder that is populated after review data is calculated. Regression coverage must inspect the page structure so CSS-only assertions cannot report a false pass.

**Bugfix implementation note**: BUG-003 uses a marker immediately before the dual execution columns so the CSS selector remains local to Stock Mutation. Under desktop widths, both `.neo-table-wrapper` elements reserve the existing 400px table viewport; under mobile widths the responsive card layout remains unchanged.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
