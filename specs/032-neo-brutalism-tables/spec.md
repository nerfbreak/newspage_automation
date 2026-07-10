# Feature Specification: Neo Brutalism Tables

**Feature Branch**: `032-neo-brutalism-tables`
**Created**: 2026-07-10
**Status**: Draft
**Input**: User description: "tolong table gw semua dikasih garis hitam khas neobrutalism , semua table yang ada di project gw ya."

## Table of Contents

- [User Scenarios & Testing](#user-scenarios--testing-mandatory)
- [Requirements](#requirements-mandatory)
- [Success Criteria](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View any data table (Priority: P1)

As a user, when I view any data table in the application, I want it to have black grid lines separating the columns and rows, so that it matches the Neo-Brutalism design system.

**Why this priority**: Core visual consistency requirement spanning the entire app.

**Independent Test**: Can be fully tested by opening any page with a table (like Stock Mutation progress, Sales Extraction preview, etc.) and verifying the grid borders.

**Acceptance Scenarios**:

1. **Given** a user is on a page with a dataframe table, **When** the table renders, **Then** all internal cells (th, td) have solid dark borders (`#0F172A`) mimicking a grid.
2. **Given** a user views a metric or summary table, **When** it renders, **Then** it follows the same border styling without breaking existing padding/alignment.

### Edge Cases

- What happens when a table is empty? (It should still render its headers with the correct borders).
- How does system handle very wide tables with horizontal scrolling? (Borders must persist across the scrollable area).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST apply a dark solid border (`2px` or `3px` solid `#0F172A` based on internal vs outer) to all table cells (`th`, `td`) rendered via Streamlit dataframes or markdown tables.
- **FR-002**: System MUST ensure the table styling integrates cleanly with existing `.neo-container-marker` wrappers without doubling up outer borders improperly.
- **FR-003**: System MUST NOT alter the data processing, automation logic, or CSV export functionalities.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of visible tables in the application display the Neo-Brutalist grid lines.
- **SC-002**: 0 visual regressions in table alignment, scrolling, or cell padding.

## Assumptions

- Streamlit's internal CSS structure for `st.dataframe` or `st.table` allows targeting of individual cell borders.
- The global `style.css` is the appropriate place to inject these rules.
