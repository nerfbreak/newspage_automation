# Data Model: Session Invalidation on Password Rotation

## User Account

Represents an application login identity.

### Fields Relevant To This Feature

- `username`: Existing login identifier.
- `password`: Existing bcrypt password hash.
- `session_version`: Non-secret version marker for remembered-session validation.
- `password_changed_at`: Optional timestamp documenting the latest credential change.

### Validation Rules

- `session_version` must be present before a new remembered-session cookie is issued.
- `session_version` must change whenever a password is rotated.
- Password hashes must remain server-side only and must never be copied into cookie payloads.

## Remembered Session

Represents the encrypted persistent login cookie.

### Fields

- `username`: The authenticated user identity.
- `session_version`: Credential version at the time the cookie was issued.

### State Rules

- **Valid**: Cookie decrypts, payload is structured, user exists, and payload version matches the current user row.
- **Stale**: Cookie decrypts but is legacy, missing version metadata, or version does not match the current user row.
- **Invalid**: Cookie cannot decrypt or payload cannot be parsed.

## Password Rotation Event

Represents any password update through SQL Editor, admin tooling, or a future app admin flow.

### Required Result

- The user's password hash changes.
- The user's `session_version` changes.
- The user's `password_changed_at` is updated when available.
- Any remembered-session cookie with the previous version fails validation.
