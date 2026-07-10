# Feature Specification: Mobile-First Responsive Design

**Feature Branch**: `017-mobile-responsive`

**Created**: 2026-07-05

**Status**: Completed

**Input**: User description: "buat fitur baru dong di project aplikasi gw , buat dynamic responsive design khusus kalo dibuka lewat mobile , jadi ukurannya presisi gak numpuk2"

## Table of Contents
- [User Scenarios & Testing *(mandatory)*](#user-scenarios--testing-mandatory)
- [Requirements *(mandatory)*](#requirements-mandatory)
- [Success Criteria *(mandatory)*](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mobile UI Navigation and Interaction (Priority: P1)

As a mobile user, I want the application layout to dynamically adapt to my small screen size, so that I can view forms, data tables, and interact with buttons clearly without them overlapping, being cut off, or requiring horizontal scrolling to find key actions.

**Why this priority**: Users accessing the tool on-the-go must be able to execute core workflows (like stock mutation or adjustments) reliably. An overlapping UI prevents users from completing their tasks.

**Independent Test**: Can be fully tested by opening the application on a mobile device emulator (e.g., iPhone 13 or Pixel 5 viewport) and verifying that all forms and buttons are perfectly stacked, accessible, and not overlapping.

**Acceptance Scenarios**:

1. **Given** a user opens the application on a mobile phone (viewport width < 768px), **When** they view the main execution page, **Then** all input fields and execution buttons stack vertically with precise spacing and no overlap.
2. **Given** a user is viewing a page with multiple action buttons, **When** the viewport is narrow, **Then** the buttons adjust their width to fit the screen or stack cleanly without squishing the text.
3. **Given** a user uploads a Stock Mutation file, **When** upload feedback and column mappings are displayed, **Then** the upload controls remain inside one outer Neo-Brutalist group container and each mapping dropdown remains grouped with its corresponding summary metric inside a white bordered card.
4. **Given** a Stock Mutation is running in the two-column desktop execution view, **When** table cell content wraps to different line counts in DEDUCT and ADD, **Then** both table viewports and their following progress bars remain vertically aligned.
5. **Given** a Stock Mutation file is loaded, **When** the user clicks **Hapus File Upload**, **Then** the uploader and upload-derived review state reset without modifying an already-instantiated widget key or raising a Streamlit runtime exception.

---

### User Story 2 - Wide Data Table Handling on Mobile (Priority: P2)

As a mobile user viewing reports or data grids, I want to be able to read the data comfortably without the table breaking the page layout or squishing columns to the point of unreadability.

**Why this priority**: Data visibility is crucial, but it's secondary to being able to execute the core actions (Story 1).

**Independent Test**: Can be tested by loading a large dataset (e.g., 10+ columns) and viewing it on a mobile viewport to ensure the page layout remains intact.

**Acceptance Scenarios**:

1. **Given** a user generates a data table with many columns, **When** viewing on a mobile screen, **Then** each row is transformed into a readable stacked card layout without requiring horizontal scrolling or breaking the overall page layout.

### Edge Cases

- What happens when a very wide data table is displayed on a narrow mobile screen? (Does it enable horizontal scrolling or wrap text awkwardly?)
- How does the system handle rapid orientation changes (portrait to landscape) on a mobile device?
- Do third-party component embeds (if any) resize correctly within the new responsive containers?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST dynamically adjust container widths, margins, and paddings based on the device viewport size, using CSS media queries or framework-native responsive parameters.
- **FR-002**: System MUST prevent UI elements (buttons, inputs, text areas) from overlapping vertically or horizontally on screen widths under 768px.
- **FR-003**: System MUST ensure all interactive elements are easily tappable on touch screens (adequate minimum height/width) without accidental clicks on adjacent elements.
- **FR-004**: System MUST preserve the core Neo-Brutalism design system (solid colors, thick borders, sharp corners, distinct shadows) across all viewport sizes.
- **FR-005**: System MUST handle wide data grids on mobile by transforming each row into a vertical stacked card-based layout to ensure readability without horizontal scrolling.
- **FR-006**: The Stock Mutation upload controls and each column-mapping dropdown/metric pair MUST retain their outer `st.container(border=True)` group structure and locked Neo-Brutalist card styling without changing upload or execution behavior.
- **FR-007**: On desktop, the paired Stock Mutation DEDUCT and ADD execution table viewports MUST use equal heights so their progress indicators remain vertically aligned regardless of content wrapping; mobile stacked-card behavior MUST remain unchanged.
- **FR-008**: Stock Mutation upload reset MUST execute before widget re-instantiation through a callback or equivalent lifecycle-safe mechanism and MUST clear the uploader value, `mutasi_file_id`, and `mutasi_review_df` without direct post-instantiation assignment to the widget-owned key.
- **FR-009**: After Stock Mutation upload reset, the file uploader dropzone MUST visually restore to its default empty state by rotating the widget key so Streamlit creates a fresh widget instance.

### Key Entities

- **Viewport**: The visible area of the application, determining the layout rules applied (e.g., Mobile < 768px, Desktop >= 768px).
- **UI Container**: The building blocks of the page (columns, expanders, forms) that must dynamically resize.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of primary execution buttons and input fields are fully visible and clickable without horizontal scrolling on a standard 320px wide viewport.
- **SC-002**: Zero instances of UI elements visually overlapping or overflowing their parent containers on screens down to 320px width.
- **SC-003**: The Neo-Brutalism aesthetic (borders, shadows, colors) remains 100% consistent between desktop and mobile views.
- **SC-004**: Source-level regression coverage confirms the Stock Mutation uploader and all three mapping groups emit explicit bordered container wrappers.
- **SC-005**: Regression coverage confirms **Hapus File Upload** uses lifecycle-safe reset handling and contains no direct assignment to `st.session_state.mutasi_file_uploader` after widget creation.
- **SC-006**: After clicking **Hapus File Upload**, the uploader widget key rotates so Streamlit renders a fresh empty dropzone on the next rerun.

## Assumptions

- "Mobile" primarily targets modern smartphone viewports (typically 320px to 480px width).
- Tablets (481px to 768px) will also benefit gracefully from these responsive adjustments.
- The underlying framework (Streamlit) provides sufficient CSS hooks or native responsive parameters (~~`use_container_width=True`~~ deprecated and disallowed by Constitution Principle X; use `width='stretch'` or `width='content'`) to implement these changes without a complete rewrite of the frontend stack.
- Custom CSS injected via `static/style.css` is permitted to use `@media` queries to enforce the responsive design.

**Bugfix**: 2026-07-06 - [BUG-001] Removed deprecated `use_container_width=True` from responsive assumptions to comply with Constitution Principle X.

**Bugfix**: 2026-07-10 - [BUG-002] Added explicit Stock Mutation upload and mapping group-container requirements after the page structure drifted away from the locked Neo-Brutalist card layout.

**Bugfix**: 2026-07-10 - [BUG-003] Added desktop alignment requirements for paired Stock Mutation execution tables and progress bars when cell content wraps differently.

**Bugfix**: 2026-07-10 - [BUG-004] Added lifecycle-safe Stock Mutation uploader reset requirements after Streamlit 1.58 rejected inline mutation of the instantiated uploader key.

**Bugfix**: 2026-07-10 - [BUG-005] Added visual dropzone restoration requirement after BUG-004 fix cleared state but did not force a fresh widget instance, leaving the uploader area visually empty.
