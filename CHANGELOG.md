# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- Fixed `SyntaxError` caused by escaped triple quotes in `database.py` docstrings.
- Fixed positional argument error (`AttributeError`) by correctly passing dual `WAREHOUSE` arguments to `run_mutasi_execution`.
- Comprehensive security, concurrency, and architecture overhaul.
- Restored missing `run_mutasi_execution` in `playwright_engine`.
- UI enhancements: Removed implicit h1 bottom border and redundant empty anchors/dividers; updated backlink label to `< Back To Dashboard`.

### Reverted
- Rolled back v2.0 changes (FastAPI headless engine, RBAC, Multi-Warehouse) as per user request.
