# Feature Specification: Success Screenshot

**Feature Branch**: `004-success-screenshot`

**Created**: 2026-07-04

**Status**: Draft

**Input**: User description: "menambahkan fitur agar bot juga memfoto hasil akhir layar saat berhasil lalu mengirimkannya ke Telegram"

## Table of Contents
- [User Scenarios & Testing (mandatory)](#user-scenarios--testing-mandatory)
- [Edge Cases](#edge-cases)
- [Requirements (mandatory)](#requirements-mandatory)
- [Success Criteria (mandatory)](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Task Completion Screenshot (Priority: P1)

As a user, I want to receive a screenshot of the final browser screen in Telegram when a bot task finishes successfully, so that I have visual proof that the operation completed as expected.

**Why this priority**: Visual confirmation of success increases user trust and provides an immediate audit trail without needing to log in to the application.

**Independent Test**: Can be fully tested by running a short, safe bot task (e.g., a dummy extraction) and verifying that a success message with a photo arrives in Telegram.

**Acceptance Scenarios**:

1. **Given** the bot is executing a task (e.g., extraction or execution), **When** the task reaches successful completion (right before logout), **Then** the bot captures a screenshot.
2. **Given** the bot has captured a success screenshot, **When** it sends the completion alert, **Then** the Telegram alert includes the screenshot photo along with the success message text.

### Edge Cases

- What happens when the screenshot capture fails? (The system should log a warning but still send the text-based success message to Telegram, avoiding a hard crash).
- What happens if the Telegram API fails to send the photo? (The system should log the failure and continue closing the browser properly).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST capture a screenshot of the active browser window immediately upon the successful completion of an automated Playwright task (prior to the logout sequence).
  - *Clarification (BUG-001)*: For transaction-generating modules (like Stock Adjustment), the system MUST navigate to the transaction list view and search for the newly created transaction before capturing the screenshot, ensuring the image provides meaningful proof.
  - *Clarification (BUG-002)*: The search filter for Status MUST specifically be set to "Approved" (`"A"`) rather than selecting all statuses.
- **FR-002**: The system MUST attach the captured screenshot to the success notification sent to the configured Telegram chat.
- **FR-003**: The system MUST gracefully handle screenshot failures (e.g., file system errors) by falling back to sending a text-only success notification.
- **FR-004**: The system MUST ensure the existing error screenshot functionality remains unaffected.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of successfully completed bot tasks trigger a Telegram message containing both the success summary text and the final state screenshot.
- **SC-002**: Capturing the success screenshot adds no more than 3 seconds to the total execution runtime.

## Assumptions

- The existing Telegram alert infrastructure (`send_telegram_alert`) already supports sending photos via a `photo_path` parameter.
- The server has sufficient disk space to store these additional success screenshots.
- Screenshots are saved in the same directory (`screenshots/`) as the error screenshots.

---
**Bugfix**: 2026-07-04 — [BUG-001] Updated FR-001 to mandate navigating to the list view for Stock Adjustment screenshots.
**Bugfix**: 2026-07-05 — [BUG-002] Updated FR-001 to specify "Approved" status filter for Stock Adjustment screenshots.
