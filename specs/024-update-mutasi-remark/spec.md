# Feature Specification: Update Mutasi Remark

**Feature Branch**: `024-update-mutasi-remark`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "update fitur di stock mutation, pindahkan remark ke masing-masing distributor dan hapus remark global"

## Table of Contents

- [User Scenarios & Testing](#user-scenarios--testing-mandatory)
- [Requirements](#requirements-mandatory)
- [Success Criteria](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Remark per Distributor (Priority: P1)

Users should be able to provide specific remarks for the sender (pengirim) and receiver (penerima) distributors separately in the Stock Mutation module. 

**Why this priority**: It allows for better tracking of inventory movements when adjusting stock from one distributor to another.

**Independent Test**: Can be tested by filling out both the sender remark and receiver remark, executing a mutation, and verifying that the automation engine types the correct remarks for each distributor in Newspage.

**Acceptance Scenarios**:

1. **Given** a user is setting up a stock mutation, **When** they fill in "Remark Pengirim" and "Remark Penerima", **Then** the values are passed correctly to the automation engine for each respective distributor during execution.

---

### User Story 2 - Remove Global Remark (Priority: P2)

Users should no longer see the global remark field below the "Reason Adjustment" dropdown.

**Why this priority**: Since remarks are now bound to specific distributors, a global remark field is redundant and creates confusion.

**Independent Test**: Can be tested by verifying that the global remark field is absent from the UI, and the execution still proceeds without it.

**Acceptance Scenarios**:

1. **Given** a user is configuring a mutation on the UI, **When** they look below the Reason Adjustment section, **Then** they do not see any general "Remark" text input field.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture the value of "Remark Pengirim" from the UI.
- **FR-002**: System MUST capture the value of "Remark Penerima" from the UI.
- **FR-003**: System MUST NOT display a general "Remark" input field under the "Reason Adjustment" dropdown in the execution section.
- **FR-004**: System MUST pass the captured sender and receiver remarks to the `playwright_engine` mutation function to be used during the automation process.
  - **Bugfix**: 2026-07-12 — [BUG-004] Added explicit waits and Tab dispatch to ensure the filled remark survives the ASP.NET `REASON_CODE` UpdatePanel postback. Truncation increased to `[:100]`.

### Key Entities

- **Stock Mutation Automation**: The Playwright script that interacts with the Newspage portal, which requires the remark fields to fill out the transaction notes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Remarks are correctly decoupled and inputted into the Newspage portal for the Sender (Pengirim) transaction.
- **SC-002**: Remarks are correctly decoupled and inputted into the Newspage portal for the Receiver (Penerima) transaction.
- **SC-003**: No redundant global remark field is visible on the UI, streamlining the user experience.

## Assumptions

- The inputs for `remark_a` (sender) and `remark_b` (receiver) are already mounted in the UI (`pages/4_stock_mutation.py`) as stated by the user.
- The `playwright_engine.py` script parameters for Stock Mutation will need to be updated to accept `remark_text_a` and `remark_text_b` instead of a single `remark_text`.
