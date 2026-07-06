# Dependency Pruning Review

**Status**: Review baseline  
**Last reviewed**: 2026-07-07

This document tracks the remaining dependency-risk item from the production-readiness work: `torch` is currently ignored in `pip-audit` for `CVE-2025-3000` because the scanner does not report a fix version.

## Current Evidence

Direct application imports observed in the active app files are centered on:

- `streamlit`
- `extra_streamlit_components`
- `pandas`
- `playwright`
- `supabase`
- `bcrypt`
- `cryptography`
- `requests`
- Python standard-library modules

No direct app import was found for:

- `torch`
- `sentence_transformers`
- `transformers`
- `faiss`
- `langchain`
- `langgraph`
- `langsmith`
- `reflex`
- `firebase_admin`

The repository also contains ignored/local artifact folders such as `.specify/`, `spec-kit/`, and `newspage_automation/` on disk. Those folders can contain unrelated imports and should not be used as deployment dependency evidence.

## Recommendation

Do not prune the large dependency set blindly. Instead:

1. Create a deployment branch.
2. Remove unused heavyweight ML/agent packages in a small batch, starting with `torch`, `sentence-transformers`, `transformers`, `faiss-cpu`, `langchain*`, `langgraph*`, and `langsmith`.
3. Run `python -m pip install -r requirements.txt` in a clean environment.
4. Run `python scripts/production_readiness_audit.py`.
5. Run `python -m unittest discover -s tests/smoke`.
6. Start the Streamlit app and perform the manual regression checklist.
7. Only merge if app startup, smoke tests, and manual regression all pass.

## Current Decision

Keep the current dependency pins for now and keep `CVE-2025-3000` as the only documented `pip-audit` exception. Prune in a separate dependency-cleanup checkpoint so deployment risk stays isolated.
