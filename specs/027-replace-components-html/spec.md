# Feature Specification: Replace st.components.v1.html with st.iframe

**Feature Branch**: `027-replace-components-html`

**Created**: 2026-07-09

**Status**: Completed

**Input**: User description: "Please replace st.components.v1.html with st.iframe. st.components.v1.html will be removed after 2026-06-01."

## Table of Contents
- [User Scenarios & Testing *(mandatory)*](#user-scenarios--testing-mandatory)
  - [User Story 1 - Maintain Dashboard Functionality (Priority: P1)](#user-story-1---maintain-dashboard-functionality-priority-p1)
  - [Edge Cases](#edge-cases)
- [Requirements *(mandatory)*](#requirements-mandatory)
  - [Functional Requirements](#functional-requirements)
- [Success Criteria *(mandatory)*](#success-criteria-mandatory)
  - [Measurable Outcomes](#measurable-outcomes)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintain Dashboard Functionality (Priority: P1)

As a user, I want the web interface to continue functioning correctly without deprecation warnings or broken components, so that I can use the application smoothly.

**Why this priority**: Resolving deprecated functions before they are removed ensures the application remains operational and avoids sudden breakage.

**Independent Test**: Can be tested by loading the application pages that currently use custom embedded content and verifying they render correctly using the new implementation.

**Acceptance Scenarios**:

1. **Given** the application is running, **When** the user navigates to a page rendering custom content, **Then** the content is displayed correctly without any system deprecation warnings.
2. **Given** the application is running, **When** the user interacts with the embedded content, **Then** it behaves as it did before the system update.

### Edge Cases

- What happens when the content to be embedded relies on specific viewport sizing?
- How does the system handle responsive design if the new embedding method requires explicit width/height compared to the previous method?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST migrate away from deprecated rendering components to the recommended modern alternatives.
- **FR-002**: System MUST ensure that embedded content retains its visual formatting and styling exactly as before.
- **FR-003**: System MUST NOT introduce any new visual artifacts (e.g., unnecessary scrollbars or cropped content) due to the migration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of targeted deprecated calls are removed from the system.
- **SC-002**: The application starts and runs without any deprecation warnings in the system console.
- **SC-003**: UI components previously using the deprecated function render with 100% visual parity.

## Assumptions

- The modern recommended equivalent provides sufficient capability to render the required embedded content used in the current app.
- The migration only involves swapping the method calls and adjusting related sizing/scrolling parameters without needing a full rewrite of the embedded content itself.
