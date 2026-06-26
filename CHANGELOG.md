# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Added credentials auto-encryption feature: plain text passwords stored in Supabase are automatically encrypted on first use.

### Fixed
- Fixed Stock Mutation quantity execution bug by adding a fallback to the `Qty` column when `PAC`, `CAR`, and `EA` are missing, ensuring quantities are correctly written to the Newspage portal.
- Fixed visual glitches in Stock Mutation execution tables by pre-initializing Status and Keterangan columns.
- Fixed `SyntaxError` caused by escaped triple quotes in `database.py` docstrings.
- Fixed positional argument error (`AttributeError`) by correctly passing dual `WAREHOUSE` arguments to `run_mutasi_execution`.
- Restored missing `run_mutasi_execution` in `playwright_engine`.
- Improved UI styling: Removed implicit h1 bottom border and redundant empty anchors/dividers, and updated the backlink label.
- Fixed frozen progress bars on the Stock Mutation page during injection run by passing progress placeholders to `run_execution_manual` and updating them dynamically.
