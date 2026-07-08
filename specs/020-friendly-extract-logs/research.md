# Research: Friendly Extraction Terminal Logs

## Decision: Keep this as a wording-only UX patch

**Rationale**: The request is to make terminal log text easier for users to
understand. Existing extraction flows are locked and validated, so changing
automation behavior would introduce unnecessary risk.

**Alternatives considered**:

- Refactor terminal logging into a centralized message catalog. Rejected for this
  pass because it would touch broader shared behavior than needed.
- Redesign the terminal UI. Rejected because the user asked for language clarity,
  not layout changes.

## Decision: Cover inventory and sales extraction first

**Rationale**: These are the user-facing extraction flows named in the product
scope and routed through `run_extract()` and `run_sales_extract()`. Shared download
helper messages used by these flows should also be made clearer.

**Alternatives considered**:

- Change every log message in every automation module. Rejected because Stock
  Mutation, Adjustment, Clearance, and Initial Stock are frozen workflows and the
  user asked specifically about extraction.

## Decision: Use concise operational Indonesian-friendly wording

**Rationale**: The project UI already mixes English labels with Indonesian
operational wording. Logs should be clear to non-technical users, e.g. "Menyiapkan
halaman Newspage" is clearer than "Session established" or "Intercepting download
link".

**Alternatives considered**:

- Fully technical English logs. Rejected because it does not solve user
  comprehension.
- Long explanatory sentences. Rejected because terminal logs must stay scannable.

## Decision: Add focused smoke coverage for representative message constants

**Rationale**: Full browser extraction is not suitable for smoke tests because it
depends on Newspage. A focused test can guard that selected user-facing messages
remain friendly and that old jargon does not reappear in changed paths.

**Alternatives considered**:

- Manual-only verification. Rejected because wording regressions are easy to
  reintroduce.
- Mocking the full Playwright extraction flow. Rejected as too brittle for a
  wording-only patch.
