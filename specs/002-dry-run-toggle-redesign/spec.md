# Feature Specification: Dry Run Toggle Redesign

**Feature Branch**: `[002-dry-run-toggle-redesign]`

**Created**: 2026-07-01

**Status**: Draft

**Input**: User description: "design nya kurang flat dan premium... SAMA AJA GAK ADA PERUBAHAN DARI DESIGN SEBELUMNYA , pake speckit design lo sampah"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Premium Flat Design Toggle (Priority: P1)

As a user, I want the "Dry Run (Simulate Only)" toggle to have a premium, flat design that strictly adheres to the UI guidelines (solid background, sharp borders, material icons) so that it looks professional and consistent with the rest of the application without using unsupported glassmorphism effects.

**Why this priority**: The current toggle styling is failing to apply or looks generic. It is a critical user-facing safety feature, and its design must reflect its importance.

**Independent Test**: Can be fully tested by opening any main page (e.g., Dashboard or Inventory Adjustment) and visually confirming that the Dry Run toggle renders as a distinct, flat, premium card with a blue left border and a proper material icon.

**Acceptance Scenarios**:

1. **Given** the user opens the Streamlit application, **When** the sidebar/header renders, **Then** the Dry Run toggle is displayed with a solid #FFFFFF or #F8FAFC background, a distinct left border accent (#0068C9), and sharp typography.
2. **Given** the Dry Run toggle is displayed, **When** the user hovers over it, **Then** the toggle provides a smooth, flat color transition without blurry drop-shadows.

---

### Edge Cases

- What happens when the Streamlit version changes its internal DOM structure? The CSS injection must be robust enough or use native Streamlit container styling to ensure the design persists.
- How does the system handle multiple toggles on the same page? The styling should specifically target the Dry Run toggle or universally improve all toggles gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render the Dry Run toggle with a flat design (no `backdrop-filter`, no `rgba` glass effects).
- **FR-002**: System MUST inject CSS that correctly targets the Streamlit 1.58.0 toggle component (verifying the exact `data-testid` or DOM structure).
- **FR-003**: The toggle MUST use a Streamlit Material Icon (e.g., `:material/science:`) in its label text.
- **FR-004**: The toggle MUST have a vertical colored border on the left side to group the action visually.

### Key Entities

- **Dry Run Toggle**: The Streamlit widget (`st.toggle`) controlling simulation mode.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of page loads successfully apply the custom CSS to the toggle, overriding the default Streamlit styling.
- **SC-002**: The toggle passes visual inspection for flat design (0 glassmorphism effects detected in computed CSS).
- **SC-003**: The user explicitly confirms the design successfully changed and looks premium.

## Assumptions

- The Streamlit DOM allows CSS targeting of the toggle container without breaking the layout.
- The failure of the previous CSS was due to an incorrect selector or CSS specificity issue that can be resolved through DOM inspection.
