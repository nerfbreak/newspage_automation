# Feature Specification: Laptop Responsive Design (1366x768)

**Feature Branch**: `037-laptop-responsive`
**Created**: 2026-07-11
**Status**: Draft

**Input**: User description: "dynamic resolution untuk laptop, kayak font-size nya yang tadinya nanggung / kepotong pas dilayar 1366x768 (laptop biasa), tolong sesuaikan juga biar kebaca enak. terus ada lagi, ukuran card dashboard nya kayak kegedean gitu di layar laptop. tolong di perbaiki ya. ingat, jangan ganggu yg responsive mobile"

## Table of Contents
- [User Scenarios & Testing *(mandatory)*](#user-scenarios--testing-mandatory)
- [Requirements *(mandatory)*](#requirements-mandatory)
- [Success Criteria *(mandatory)*](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Laptop Data Table Readability (Priority: P1)

As a user on a standard 1366x768 laptop screen, I want the data tables (especially dual tables like Stock Mutation) to display text clearly without clipping or awkwardly wrapping fonts so I can read SKUs and Descriptions easily.

**Acceptance Scenarios**:
1. **Given** a user opens the Stock Mutation page on a 1366x768 screen, **When** the dual DEDUCT/ADD tables render, **Then** the font size and padding adapt so text does not clip or overflow cell boundaries.

### User Story 2 - Dashboard Card Proportions (Priority: P2)

As a user on a standard 1366x768 laptop screen, I want dashboard cards (metric cards, app launchers) to scale down proportionally so they don't consume excessive vertical space and force unnecessary scrolling.

**Acceptance Scenarios**:
1. **Given** a user views the Dashboard on a 1366x768 screen, **When** metric cards and app launchers render, **Then** their height, padding, and font sizes are proportionally reduced compared to the 1920x1080 desktop view.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST apply a specific CSS media query for laptop screens: `@media (max-width: 1366px) and (min-width: 769px)`.
- **FR-002**: Within this media query, font sizes and paddings for `.neo-table` (used in Stock Mutation) MUST be reduced to prevent text clipping.
- **FR-003**: Within this media query, padding and height for Dashboard metric cards and UI containers MUST be proportionally reduced.
- **FR-004**: System MUST NOT alter or break the existing mobile responsive design (`@media (max-width: 768px)`).
- **FR-005**: System MUST preserve all Neo-Brutalism design tokens (solid colors, thick borders, `#0F172A` shadows, `0px` radius).

## Success Criteria *(mandatory)*

- **SC-001**: Font sizes on 1366x768 displays render without clipping in dual tables.
- **SC-002**: Dashboard cards fit cleanly in the 1366x768 viewport without excessive scrolling.
- **SC-003**: Mobile view (< 768px) remains exactly as it was, with stacked cards working correctly.
- **SC-004**: Smoke tests pass verifying CSS syntax and unchanged backend logic.

## Assumptions

- The primary targets for this fix are `static/style.css` and specifically `.neo-table` and dashboard card classes.
- Standard Streamlit desktop view assumes > 1366px (e.g., 1920x1080).
- The existing mobile rules (`max-width: 768px`) will take precedence for smaller devices, so this new tier sits perfectly in the middle.