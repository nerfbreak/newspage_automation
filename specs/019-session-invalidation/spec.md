# Feature Specification: Session Invalidation on Password Rotation

**Feature Branch**: `019-session-invalidation`

**Created**: 2026-07-08

**Status**: Draft

**Input**: User description: "Invalidate existing persistent login sessions when a user password changes so rotated credentials immediately revoke old auth_user cookies and force re-authentication without changing frozen automation workflows."

## Table of Contents

- [User Scenarios & Testing](#user-scenarios--testing-mandatory)
- [Requirements](#requirements-mandatory)
- [Success Criteria](#success-criteria-mandatory)
- [Assumptions](#assumptions)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Revoke Old Persistent Sessions (Priority: P1)

An operator or admin rotates a user's password after the old password was exposed or shared. Any browser that still has a remembered login for that user must lose access and return to the sign-in screen instead of continuing into the dashboard.

**Why this priority**: Password rotation is only meaningful if existing remembered sessions are revoked. This is the core security value of the feature.

**Independent Test**: Sign in as a user, simulate a password rotation for that account, reload the app using the prior remembered session, and confirm the app returns to sign-in instead of showing authenticated pages.

**Acceptance Scenarios**:

1. **Given** a user has a valid remembered session, **When** that user's password is rotated, **Then** the old remembered session is rejected on the next app load.
2. **Given** a user's remembered session is rejected after password rotation, **When** the app redirects to sign-in, **Then** the user can authenticate only with the new password.
3. **Given** a remembered session belongs to a user whose account no longer exists, **When** the app loads, **Then** the remembered session is cleared and access is denied.

---

### User Story 2 - Preserve Valid User Convenience (Priority: P2)

A user whose password has not changed can keep using the existing remembered login behavior without being unexpectedly logged out before the normal session lifetime expires.

**Why this priority**: The hardening must not make normal daily operations painful for users whose credentials are still valid.

**Independent Test**: Sign in as a user, reload the app before any password change, and confirm the remembered session remains accepted.

**Acceptance Scenarios**:

1. **Given** a user has a valid remembered session and no password rotation has occurred, **When** the app reloads, **Then** the user remains signed in.
2. **Given** a remembered session cannot be validated because it is malformed or encrypted with an invalid key, **When** the app loads, **Then** the cookie is cleared and the user is asked to sign in.

---

### User Story 3 - Support Safe Operations and Audits (Priority: P3)

Maintainers need clear, repeatable evidence that session invalidation works without exposing passwords, hashes, cookies, or secret values.

**Why this priority**: Authentication changes require verifiable safety while preserving project security hygiene.

**Independent Test**: Run offline smoke tests that prove old session payloads fail after a credential version change and no sensitive values are printed.

**Acceptance Scenarios**:

1. **Given** maintainers run the smoke suite, **When** session validation tests execute, **Then** the tests prove stale remembered sessions are rejected.
2. **Given** a validation failure occurs, **When** the app reports it to the user, **Then** the message is generic and does not expose password hashes, raw cookies, or secret values.

### Edge Cases

- A user row exists but has no credential version metadata yet; the next successful login should establish a current remembered-session version without blocking the user.
- A remembered session was created before this feature existed; it should be rejected safely and replaced only after a fresh password login.
- The account lookup fails because the database is temporarily unavailable; the remembered session should not silently grant access.
- A password hash is updated by SQL or an admin process outside the app; remembered sessions should become invalid without requiring a code deployment.
- A user logs out manually; the remembered session should still be deleted immediately.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST reject remembered login sessions created before the user's latest password credential state.
- **FR-002**: The system MUST verify a remembered session against the current user record before granting authenticated access.
- **FR-003**: The system MUST clear invalid, stale, malformed, or unverifiable remembered sessions before showing the sign-in screen.
- **FR-004**: The system MUST continue allowing remembered login for users whose credential state has not changed and whose session is otherwise valid.
- **FR-005**: The system MUST allow existing users without credential-version metadata to sign in with their password and receive a newly valid remembered session.
- **FR-006**: The system MUST avoid storing raw passwords, password hashes, or unencrypted session identifiers in browser cookies.
- **FR-007**: The system MUST avoid printing passwords, password hashes, raw cookie values, or Supabase secrets in logs, test output, or UI messages.
- **FR-008**: The system MUST preserve the existing failed-login lockout behavior.
- **FR-009**: The system MUST preserve the existing manual logout behavior.
- **FR-010**: The system MUST NOT modify frozen Newspage automation workflows, Playwright selectors, or module execution logic.
- **FR-011**: The system MUST provide repeatable smoke/regression evidence for stale-session rejection and valid-session acceptance.
- **FR-012**: The system MUST document the required credential metadata migration and the operational password-rotation process.

### Key Entities

- **User Account**: Represents an application login identity. Relevant attributes include username, password credential state, and optional session invalidation metadata.
- **Remembered Session**: Represents a browser-side persistent login token. Relevant attributes include the username identity and a credential-state marker that proves the token was issued after the latest password state.
- **Password Rotation Event**: Represents a change to a user's password credential state. It must invalidate remembered sessions issued before the change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A remembered session issued before password rotation is rejected on the next app load in 100% of tested cases.
- **SC-002**: A remembered session issued after the latest successful password login remains accepted in 100% of tested valid-session cases.
- **SC-003**: Existing users can recover from pre-feature remembered sessions by signing in again within one normal login attempt.
- **SC-004**: The smoke suite includes at least one stale-session rejection test and one valid-session acceptance test.
- **SC-005**: No test output, documentation example, or user-facing message reveals raw passwords, password hashes, raw cookie tokens, or secrets.

## Assumptions

- The existing application user table remains the source of truth for username/password authentication.
- Password rotation may happen outside the app through Supabase SQL Editor or an admin process.
- Remembered sessions should remain convenient for normal users, but must fail closed if validation cannot be completed.
- The feature is limited to Streamlit app authentication/session behavior and database documentation; frozen automation workflows remain out of scope.
