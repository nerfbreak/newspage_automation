# Research: Session Invalidation on Password Rotation

## Decision: Use credential-version metadata for remembered sessions

Remembered sessions will include a non-secret credential-version marker. The marker is compared to the current user row before auto-login is granted.

**Rationale**: Password rotation may happen outside the app through SQL Editor. A stored version marker gives the app a direct way to determine whether an existing cookie was issued before or after the latest credential state.

**Alternatives considered**:

- **Only shorten cookie lifetime**: Reduces risk window but does not immediately revoke old sessions after password rotation.
- **Force all users to login every load**: Secure but removes the existing remembered-login convenience.
- **Compare cookie to password hash**: Avoided because password hashes should not be copied into cookie payloads or logs.

## Decision: Store encrypted structured session payloads

New remembered-session cookies will encrypt structured JSON with username and credential version. Legacy cookies containing only a username will be treated as stale and cleared.

**Rationale**: Existing cookies are encrypted, but they are not tied to any credential state. Structured encrypted payloads let the app evolve while preserving the existing secret boundary.

**Alternatives considered**:

- **Plain JSON cookie**: Rejected because plaintext identifiers without integrity validation violate the constitution.
- **Signed-only cookie**: Acceptable, but existing Fernet encryption already provides confidentiality and integrity with current project dependencies.

## Decision: Fail closed when validation cannot complete

If the cookie is malformed, legacy, for a missing user, or cannot be checked against the database, the app clears it and requires password login.

**Rationale**: Auto-login is a convenience feature. It should not grant access when the app cannot prove the remembered session is current.

**Alternatives considered**:

- **Allow cookie during database outage**: Rejected because it could preserve access after credential revocation.

## Decision: Additive migration only

The user table will receive optional credential metadata. Existing users without metadata can still sign in with their password; the app will establish metadata during successful login when possible.

**Rationale**: This avoids a breaking migration and keeps production recovery simple.

**Alternatives considered**:

- **Require pre-migration of every user**: Safer on paper, but more operational friction and easier to misapply.
