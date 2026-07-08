# Data Model: Friendly Extraction Terminal Logs

No persistent data model changes are required.

## Existing Runtime Concepts

### Terminal Log Entry

- **Tag**: Short category rendered by the terminal logger, such as `SYS`, `AUTH`,
  `SERVER`, or `ERROR`.
- **Message**: User-visible text explaining the current extraction state.
- **Order**: Messages appear chronologically as the existing automation flow calls
  the logger.

## Validation Rules

- Messages must not include raw credentials, cookies, secrets, or raw stack traces.
- Messages should describe the operational phase in plain language.
- Messages must remain concise enough to scan in the existing terminal box.
- Tags may remain unchanged if the message text is clear.

## State Transitions

The wording should map to the existing extraction phases:

1. Preparing browser and Newspage connection
2. Logging in and opening the required distributor/module
3. Searching or requesting extraction data
4. Waiting for the portal to prepare the result
5. Downloading and storing the file
6. Packaging or reading the result
7. Completion or user-actionable failure
