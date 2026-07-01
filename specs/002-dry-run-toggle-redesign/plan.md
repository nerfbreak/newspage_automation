# Implementation Plan: Dry Run Toggle Redesign

**Branch**: `[002-dry-run-toggle-redesign]` | **Date**: 2026-07-01 | **Spec**: [specs/002-dry-run-toggle-redesign/spec.md](file:///c:/Users/Reckitt/Documents/Optimize/specs/002-dry-run-toggle-redesign/spec.md)

**Input**: Feature specification from `/specs/002-dry-run-toggle-redesign/spec.md`

## Summary

The Dry Run toggle's CSS redesign failed because Streamlit 1.58.0's DOM structure prevents the `div[data-testid="stCheckbox"]` selector from applying correctly to the toggle, or the CSS is being overridden. 
The plan is to use a robust CSS injection method utilizing the `:has()` pseudo-class to target the specific `div.element-container` that immediately follows a uniquely identifiable anchor div. This guarantees the flat, premium design applies directly to the toggle's outer container.

## Technical Context

**Language/Version**: Python 3.11, Streamlit 1.58.0
**Target Platform**: Web (Streamlit Community Cloud)

## Project Structure

### Documentation (this feature)

```text
specs/002-dry-run-toggle-redesign/
├── plan.md              # This file
├── spec.md              # Phase 0 output
└── checklists/requirements.md
```

## Implementation Steps

1. Modify `utils.py:render_header`.
2. Inject a hidden anchor div: `<div class="dry-run-anchor"></div>` immediately before `st.toggle`.
3. Update the CSS to use `div.element-container:has(.dry-run-anchor) + div.element-container` to style the toggle's container directly.
4. Apply the flat, premium design (solid white background, crisp borders, blue left accent, 4px border radius).
5. Ensure the toggle label uses the `:material/science:` icon.

## Verification

After applying the fix, I will verify the CSS selector correctly applies the style.
