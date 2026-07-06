# Production Readiness Status

**Project**: Optimize Newspage Automation  
**Last reviewed**: 2026-07-07  
**Status**: Offline production-readiness baseline complete; live environment checks remain operational gates.

## Coverage Matrix

| Area | Status | Evidence | Remaining live gate |
|---|---|---|---|
| Security audit baseline | Complete for offline/static scope | `SECURITY_AUDIT_REPORT.md`, `scripts/production_readiness_audit.py` | Run live Supabase/RLS review and deployment secret review |
| Secrets hygiene | Guarded | `.gitignore`, static audit secret tracking check | Rotate secrets if workspace/repo exposure is suspected |
| Session cookie review | Documented risk | `SECURITY_AUDIT_REPORT.md` SEC-001 | Validate deployed cookie attributes and lifetime policy |
| Subprocess review | Guarded | Static audit rejects `shell=True`; dashboard ping uses env arguments | Re-review any future subprocess helper before merge |
| HTML injection review | Guarded by tests for shared helpers | `tests/smoke/test_core_smoke.py` | Audit future `unsafe_allow_html=True` changes during review |
| Dependency CVE scan | Complete with one documented exception | `.github/workflows/security-audit.yml`, local `pip-audit --no-deps --disable-pip` run | `torch` CVE-2025-3000 has no fix version from `pip-audit`; keep ignored until upgrade/removal path is available |
| Automated smoke tests | Complete for offline critical helpers | `tests/smoke/`, `.github/workflows/smoke-tests.yml` | Add live Playwright regression only when safe credentials/test environment exist |
| Manual regression checklist | Complete | `tests/manual/REGRESSION_CHECKLIST.md` | Execute before major releases |
| Spec Kit ignored artifacts | Documented | `docs/spec_artifact_policy.md`, `.gitignore` | Force-add only specific durable artifacts |
| Database migration docs | Complete baseline | `docs/database_migrations.md` | Compare against live Supabase schema before deployment |
| Observability/error taxonomy | Foundation complete | `error_taxonomy.py`, `docs/error_taxonomy.md`, smoke tests | Gradually wire taxonomy into non-frozen runtime paths |

## Operational Definition Of Done

For a release candidate:

1. `python scripts/production_readiness_audit.py`
2. `python -m unittest discover -s tests/smoke`
3. `python -m pip_audit -r requirements.txt --no-deps --disable-pip --progress-spinner off --ignore-vuln CVE-2025-3000` in a network-enabled environment
4. Manual regression checklist in `tests/manual/REGRESSION_CHECKLIST.md`
5. Supabase schema/RLS comparison against `docs/database_migrations.md`

The project should not be called production-ready for a new deployment until all five gates are either passing or explicitly accepted by the owner.
