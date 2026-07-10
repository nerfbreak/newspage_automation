# Feature Specification: Neo-Brutalist Section Headers

**Feature Branch**: `029-neo-brutalist-section-headers`

**Created**: 2026-07-10

**Status**: Completed

**Input**: User request: "gaya ini belom gaya neo brutalism kayak yang lain" referring to the plain/unstyled subheaders on the page.

## Table of Contents
- [User Scenarios & Testing](#user-scenarios--testing)
  - [User Story 1 - Standardize Section Headers (Priority: P1)](#user-story-1---standardize-section-headers-priority-p1)
- [Requirements](#requirements)
  - [Functional Requirements](#functional-requirements)
- [Success Criteria](#success-criteria)
  - [Measurable Outcomes](#measurable-outcomes)
- [Assumptions](#assumptions)

## User Scenarios & Testing

### User Story 2 - Standardize Promotion Comparison (Priority: P1)

As a user, I want the Promotion Comparison page to use Neo-Brutalist dividers and headers, so that the UI does not feel like legacy Streamlit.

**Acceptance Scenarios**:
1. **Given** the user triggers the comparison view, **When** the page renders, **Then** the divider is 3px thick black line and the title is a `.section-header-underline` block.

### User Story 1 - Standardize Section Headers (Priority: P1)

As a user, I want all subheaders and section headers in the application to follow the locked Neo-Brutalist design language, so that the visual styling remains consistent across all modules.

**Independent Test**: Load the pages (Stock Mutation, Clearance Stock, Initial Stock) and verify that all section headers (e.g., Column Mapping, Stock Review, Map Columns, clearance/initial execution headings) are rendered with a white boxed background, 2px solid border, and flat shadow.

**Acceptance Scenarios**:

1. **Given** the user is on the Stock Mutation page, **When** they view the column mapping or stock review areas, **Then** the headers "Column Mapping" and "Stock Review" are styled as Neo-Brutalist blocks.
2. **Given** the user is on the Clearance Stock or Initial Stock pages, **When** they view the headers, **Then** all standard `st.subheader` blocks are replaced by Neo-Brutalist styled headers.

## Requirements

### Functional Requirements

- **FR-001**: System MUST replace standard `st.subheader` calls in `pages/4_stock_mutation.py`, `pages/5_clearance_stock.py`, and `pages/6_initial_stock.py` with custom HTML section headers.
- **FR-002**: Custom section headers MUST use the CSS classes `.header-wrapper-left` (for left-aligned headers) or `.header-wrapper-center` (for center-aligned headers) and containing `<span class='section-header-underline'>` matching the existing styles in `static/style.css`.
- **FR-003**: System MUST NOT change the underlying execution logic, dataframe parsing, or page-state interactions.

**Bugfix**: 2026-07-10 - [BUG-006] Replaced unstyled `<h3>` and `---` divider in `pages/3_promotion_comparison.py` found during final sweep.

### Measurable Outcomes

- **SC-001**: 100% of standard `st.subheader` calls in the targeted modules are replaced with Neo-Brutalist HTML headers.
- **SC-002**: The aesthetic output of all subheaders matches `pages/1_inventory_adjustment.py` exactly.
- **SC-003**: Python compilation passes cleanly for all modified pages.

## Assumptions

- No custom font overrides or new CSS rules are required, as `.section-header-underline` and its wrapper classes are already present in `static/style.css`.
