# Feature Specification: Streamlit Layout Width Deprecation Migration

**Feature Branch**: `016-replace-use-container-width`  
**Created**: 2026-07-05  
**Status**: Completed  
**Input**: User description: "Please replace use_container_width with width. use_container_width will be removed after 2025-12-31. For use_container_width=True, use width='stretch'. For use_container_width=False, use width='content'."

## Table of Contents

- [User Scenarios & Testing](#user-scenarios--testing-mandatory)
- [Requirements](#requirements-mandatory)
- [Success Criteria](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prevent Deprecation Crashes and Maintain Layout Alignment (Priority: P1)

Operations staff use the automation tool daily to manage inventory, mutations, and extraction history. The layout components (buttons, data editors, charts) must render correctly without visual corruption, and the application must continue running reliably without deprecation crashes or layout drift when transitioning to newer Streamlit library versions.

**Why this priority**: High. Streamlit is scheduled to remove the `use_container_width` parameter after December 31, 2025. Leaving this parameter in place will cause runtime exceptions and crash the entire application interface.

**Independent Test**: Perform a full code search for `use_container_width`. Verify that zero instances remain. Start the Streamlit application and navigate through all 7 page modules (Dashboard, Inventory Adjustment, Sales Extraction, etc.) to confirm that all layout elements render properly and no deprecation warnings are printed in stdout/stderr.

**Acceptance Scenarios**:

1. **Given** a user is viewing any dashboard or module page with interactive widgets, **When** the page loads, **Then** all widgets that previously had `use_container_width=True` are rendered with full container width using `width='stretch'` and align perfectly.
2. **Given** the Streamlit server console output, **When** any page runs or is refreshed, **Then** no warnings regarding the deprecation of `use_container_width` are logged.

### Edge Cases

- **Mismatched Streamlit Version**: If a developer runs the application on an old local Streamlit version that does not support the `width` parameter yet, it could cause layout issues or launch errors. (Assumption: Streamlit is pinned/updated in `requirements.txt` to a version supporting `width` parameter, which was validated in previous runs).
- **Custom Components**: Third-party custom components that use a custom wrapper might not support the new parameter or might require special handling. (Assumption: All standard Streamlit elements in our codebase are native widgets like `st.button`, `st.download_button`, `st.dataframe`, and `st.data_editor`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST replace all occurrences of `use_container_width=True` with `width='stretch'` inside all python scripts under the project root (`app.py`, `utils.py`, `playwright_engine.py`, and all sub-pages under `pages/`).
- **FR-002**: The system MUST replace all occurrences of `use_container_width=False` with `width='content'` inside all python scripts.
- **FR-003**: The updated application MUST preserve the Neo-Brutalist grid and card structure, guaranteeing zero layout shifting or visual drift.
- **FR-004**: All page scripts MUST load and compile without syntax errors or runtime exceptions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of files containing `use_container_width` in the codebase are successfully migrated to use the `width` parameter.
- **SC-002**: The application console is free of `use_container_width` deprecation warnings on server startup and runtime usage.
- **SC-003**: A visual audit of all Streamlit pages confirms that no container borders or button margins shift or break, keeping layout integrity intact.

## Assumptions

- The Streamlit version installed supports the `width` parameter natively (`st.button`, `st.dataframe`, etc.).
- There are no custom components in the codebase that require separate migration paths for layout sizing.
