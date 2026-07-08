# Feature Specification: Friendly Extraction Terminal Logs

**Feature Branch**: `020-friendly-extract-logs`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "bisa gak log text di terminal log saat extract bahasanya bisa lebih dipahami oleh user"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand Extraction Progress (Priority: P1)

As an operations user running an extraction, I want the terminal log to explain each
step in simple operational language so I can understand what the bot is doing
without reading technical automation terms.

**Why this priority**: Extraction runs can take time and users rely on the terminal
log to decide whether the bot is still working, waiting, downloading, or finished.
Clearer wording reduces confusion and support questions.

**Independent Test**: Run an extraction flow in a controlled test or smoke check
and review the terminal log messages. The visible messages should describe user
meaning, not implementation details.

**Acceptance Scenarios**:

1. **Given** a user starts an extraction, **When** the bot begins opening and
   preparing Newspage, **Then** the terminal log describes that the bot is
   preparing the connection and opening the required page.
2. **Given** the bot is searching or downloading extraction data, **When** the
   action is in progress, **Then** the terminal log explains that data is being
   searched, prepared, or downloaded using clear user-facing wording.
3. **Given** an extraction completes successfully, **When** the terminal log is
   shown, **Then** the final messages clearly tell the user that the extraction
   is complete and the file is ready.

---

### User Story 2 - Understand Recoverable Waits and Failures (Priority: P2)

As an operations user, I want wait and failure messages to explain what happened
in plain language so I know whether to wait, retry, or report the issue.

**Why this priority**: Technical errors and vague waits make users unsure whether
the bot is stuck. Plain language helps users make the right next decision.

**Independent Test**: Review existing timeout, missing data, and no-result paths
for extraction flows and confirm messages explain the condition without exposing
raw stack traces or internal implementation wording.

**Acceptance Scenarios**:

1. **Given** Newspage is slow, **When** the bot waits for a page or result,
   **Then** the terminal log says the portal is still loading or responding.
2. **Given** no extraction data is found, **When** the bot reaches the no-data
   state, **Then** the terminal log explains that no data was found for the
   selected filter/date range.
3. **Given** the extraction cannot finish, **When** the error is surfaced to the
   user, **Then** the terminal log includes a concise user-facing explanation and
   does not expose credentials, cookies, raw selectors, or unnecessary stack
   details.

### Edge Cases

- Newspage returns no rows for the selected date or distributor.
- Newspage responds slowly and the bot waits longer than usual.
- The downloaded file is delayed or missing.
- The extraction completes but there are warnings that should not sound like
  fatal failures.
- A technical exception still needs to be useful for debugging without exposing
  secrets.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Extraction terminal logs MUST use plain user-facing wording for
  start, preparation, search, download, packaging, completion, wait, and failure
  states.
- **FR-002**: Extraction terminal logs MUST avoid raw technical jargon where a
  simple operational phrase is available.
- **FR-003**: Extraction terminal logs MUST preserve the existing chronological
  order and meaning of the current automation steps.
- **FR-004**: Extraction terminal logs MUST NOT change Playwright selectors,
  portal navigation behavior, download behavior, generated files, Supabase
  logging, credentials, or session management.
- **FR-005**: Failure and timeout messages MUST remain useful for support while
  avoiding secrets, cookies, raw credentials, and unnecessary stack traces in
  user-facing terminal output.
- **FR-006**: The update MUST cover extraction-oriented flows visible to users,
  including inventory extraction and sales extraction, and any shared extraction
  helper messages reused by those flows.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 90% of extraction terminal log messages visible during the
  happy path use user-facing operational wording instead of implementation jargon.
- **SC-002**: A reviewer can identify the current extraction phase from the log
  without reading source code or knowing Playwright terminology.
- **SC-003**: Existing extraction behavior remains unchanged: the same inputs
  produce the same output files and workflow states.
- **SC-004**: Smoke or focused tests confirm that the user-facing log wording is
  present for representative extraction messages.

## Assumptions

- "Extract" refers to user-visible extraction flows, especially Inventory
  Extraction and Sales Extraction.
- This request is a UX wording improvement, not a change to extraction logic.
- Existing terminal log rendering and Neo-Brutalist styling remain unchanged.
- Messages may be in clear Indonesian or simple mixed operational wording if the
  surrounding module already uses that style, but they must be understandable to
  non-technical operations users.
