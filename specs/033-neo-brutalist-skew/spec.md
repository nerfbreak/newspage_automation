# Feature Specification: Neo Brutalism Skew

**Feature Branch**: `033-neo-brutalist-skew`
**Created**: 2026-07-10
**Status**: Draft
**Input**: User description: "tambah fitur efek miring khas neobrutalism pada tombol dan judul"

## Table of Contents

- [User Scenarios & Testing](#user-scenarios--testing-mandatory)
- [Requirements](#requirements-mandatory)
- [Success Criteria](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tilted Titles and Buttons (Priority: P1)

As a user, when I view titles (h1, h2, h3) and action buttons, I want them to be slightly tilted (rotated) to emphasize the authentic unpolished Neo-Brutalism aesthetic.

**Why this priority**: Enhances the global design language without changing functional behavior.

**Independent Test**: Load any module. Observe that `h1`/`h2`/`h3` elements and `st.button` elements appear rotated (e.g. by `-1deg` or `1deg`). 

**Acceptance Scenarios**:

1. **Given** a user views a primary button, **When** it renders, **Then** it is skewed by `-1deg`.
2. **Given** a user views a secondary (red) button, **When** it renders, **Then** it is skewed by `1deg`.
3. **Given** a user views a page header (`h1`/`h2`/`h3`), **When** it renders, **Then** it is skewed by `-1deg` and has a slight text-shadow for a sticker effect.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST apply a `transform: rotate(-1deg)` to all `h1`, `h2`, and `h3` tags in the global CSS.
- **FR-002**: System MUST apply a `text-shadow` to headers to simulate a cutoff sticker aesthetic.
- **FR-003**: System MUST apply a `transform: rotate(-1deg)` to all primary buttons.
- **FR-004**: System MUST apply a `transform: rotate(1deg)` to all secondary/destructive buttons to create intentional misalignment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of standard Streamlit buttons and header tags exhibit the skew effect via CSS.

## Assumptions

- Streamlit's internal CSS structure allows `transform` rules on buttons and headers without breaking interactive hitboxes.
