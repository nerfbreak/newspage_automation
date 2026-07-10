# Plan 030 — Center Column Mapping Headers

**Status**: Draft
**Spec**: specs/030-center-column-mapping-headers/spec.md
**Constitution Check**: Principle IV (Neo-Brutalism) — no amendment needed

## Implementation Strategy

Swap the wrapper class / raw HTML on two lines in two files. No new CSS, no new components, no logic changes.

## Changes

### 1. `pages/4_stock_mutation.py` (line 116)
- **Before**: `<div class='header-wrapper-left'><span class='section-header-underline'>Column Mapping</span></div>`
- **After**: `<div class='header-wrapper-center'><span class='section-header-underline'>Column Mapping</span></div>`

### 2. `pages/1_inventory_adjustment.py` (line 309)
- **Before**: `<div style='margin-bottom:10px;'><b>Mapping Kolom:</b></div>`
- **After**: `<div class='header-wrapper-center'><span class='section-header-underline'>Column Mapping</span></div>`

## Verification

1. Python compilation check on both files.
2. Full offline smoke suite must pass (94+ tests).
3. Visual: headers should render centered with the underline style.

## Risks & Mitigations

- Risk: None. Pure HTML attribute change.
