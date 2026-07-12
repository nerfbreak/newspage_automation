# Quickstart: Session Invalidation on Password Rotation

## Local Verification

1. Run the production readiness gate:

   ```powershell
   python scripts\production_readiness_audit.py
   ```

2. Run smoke tests:

   ```powershell
   python -m unittest discover -s tests\smoke
   ```

3. Confirm tests include:

   - A stale remembered session is rejected after version mismatch.
   - A valid remembered session is accepted when the version matches.
   - Legacy username-only cookies are rejected.
   - Password authentication still works for existing users.

## Manual Live Verification

1. Login to the live app with a test user.
2. Rotate the test user's password and session version in Supabase.
3. Reboot or refresh the app with the same browser profile.
4. Confirm the old remembered session returns to sign-in.
5. Confirm the old password fails.
6. Confirm the new password succeeds.

## Operational Rotation SQL Pattern

Use a project-approved SQL snippet that updates both password hash and session version. Do not paste real passwords into docs or chat logs.
