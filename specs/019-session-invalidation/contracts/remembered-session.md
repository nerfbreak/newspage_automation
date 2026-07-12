# Contract: Remembered Session Validation

## Purpose

Define the app-level contract for persistent login cookies after password rotation.

## Cookie Payload Contract

The remembered-session cookie is encrypted. After decryption, the logical payload must contain:

```json
{
  "username": "Rizki",
  "session_version": "opaque-non-secret-version"
}
```

## Acceptance Contract

A remembered session may grant access only when all conditions are true:

1. The cookie decrypts successfully.
2. The decrypted payload is structured and includes `username` and `session_version`.
3. The user exists in the current user account store.
4. The stored current `session_version` matches the cookie payload version.

## Rejection Contract

A remembered session must be cleared and must not grant access when any condition is true:

1. The cookie is missing, malformed, or cannot decrypt.
2. The cookie is legacy plaintext username payload without a version.
3. The user does not exist.
4. The user row cannot be validated.
5. The cookie version differs from the current stored user version.

## Security Contract

- Raw passwords are never stored in cookies.
- Password hashes are never stored in cookies.
- Raw cookie values are never printed in logs, tests, docs, or UI.
- Validation failures use generic user-facing messaging.
