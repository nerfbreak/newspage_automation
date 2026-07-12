# Implementation Plan: Session Invalidation on Password Rotation

**Branch**: `019-session-invalidation` | **Date**: 2026-07-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/019-session-invalidation/spec.md`

**Note**: This plan is filled for the `/speckit-plan` workflow.

## Table of Contents

- [Summary](#summary)
- [Technical Context](#technical-context)
- [Constitution Check](#constitution-check)
- [Project Structure](#project-structure)
- [Complexity Tracking](#complexity-tracking)

## Summary

Harden remembered-login behavior so password rotation invalidates previously issued persistent cookies. The implementation will add user credential-version metadata, issue encrypted remembered-session payloads that include that version, verify the payload against the current user row before auto-login, revalidate active Streamlit session state against the same metadata on rerun, and fail closed when validation cannot be completed. Existing locked Newspage automation workflows remain untouched.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: Streamlit, extra-streamlit-components CookieManager, Supabase client, Cryptography Fernet, bcrypt

**Storage**: Supabase PostgreSQL `users_auth` table, plus existing browser cookie storage

**Testing**: Python `unittest` smoke suite under `tests/smoke`

**Target Platform**: Windows local development and Streamlit Cloud deployment

**Project Type**: Streamlit web app

**Performance Goals**: Auto-login validation should add only one lightweight user lookup per remembered-session app load. Active logged-in reruns may perform one lightweight user metadata lookup to detect password rotation without waiting for manual logout.

**Constraints**: No hardcoded secrets; no raw passwords, password hashes, or raw cookies in logs; preserve Neo-Brutalist UI; do not modify frozen automation logic or Playwright selectors.

**Scale/Scope**: Single internal Streamlit app with existing Supabase-backed authentication.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I - Feature Freeze**: PASS. Scope is limited to app authentication/session handling and docs/tests; frozen Newspage automation workflows are not modified.
- **Principle II - Security-First Credential Handling & Session Protection**: PASS. Feature directly improves encrypted remembered-session validation and credential rotation hygiene.
- **Principle III - Selector Integrity**: PASS. No Playwright selectors are introduced or changed.
- **Principle IV / XI - UI Consistency & Mobile-First Design**: PASS. No new UI components are required beyond existing sign-in flow behavior.
- **Principle V - Session & Logging Integrity**: PASS. Session state remains based on `logged_in`, `current_user`, and `last_activity`, with stronger cookie validation.
- **Principle XII - Minimal Dependencies**: PASS. No new dependency is required.

Post-design re-check: PASS. Design uses existing dependencies, additive database metadata, and smoke tests only.

## Project Structure

### Documentation (this feature)

```text
specs/019-session-invalidation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── remembered-session.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
app.py
database.py
docs/database_migrations.md
docs/production_readiness_status.md
tests/smoke/test_auth_session_smoke.py
tests/smoke/test_security_audit_smoke.py
```

**Structure Decision**: Keep the change in the existing auth boundary: `database.py` owns Supabase user/session helper reads and `app.py` owns CookieManager/session-state decisions. Tests remain in the existing smoke suite. Documentation updates stay in the existing production readiness and migration docs.

**Bugfix**: 2026-07-08 - [BUG-001] Active Streamlit sessions must store and re-check the accepted session version, so a rotated password invalidates logged-in tabs on rerun as well as remembered-cookie auto-login.

## Complexity Tracking

No constitution violations or exceptional complexity are required.
