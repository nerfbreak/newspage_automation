# Dependency Pruning Review

**Status**: Pruned, verified on staging, and merged to main  
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

## Current Decision & Execution

On 2026-07-07, dependency pruning was executed on branch `chore/dependency-pruning`. Exactly 32 unused heavy ML/agent packages (`torch`, `sentence-transformers`, `transformers`, `faiss-cpu`, `langchain*`, `langgraph*`, `langsmith`, `reflex*`, `firebase_admin`) were removed from `requirements.txt`.
- `python scripts/production_readiness_audit.py`: PASS
- `python -m unittest discover -s tests/smoke`: 48 tests OK
- `python -m pip_audit -r requirements.txt --no-deps --disable-pip`: PASS (No known vulnerabilities found, resolving the ignored `CVE-2025-3000` exception).
- **Staging / Streamlit Cloud Live Regression**: PASS (Verified Playwright headless automation and app startup on 2026-07-07).
- **Status**: Successfully merged into `main` (commit `3cc1ffe`).

### Second Round Pruning (Streamlit Cloud Python Runtime Compatibility)
On 2026-07-07, during Streamlit Cloud deployment, `litellm==1.86.2` caused a fatal installation error due to Python runtime restrictions (`Requires-Python <3.14,>=3.10`). Following **Principle XII (Minimal & Clean Dependency Architecture)** added to `constitution.md` v2.6.0, a second pruning round was executed. Exactly 37 additional unused packages (`litellm`, `mcp`, `fastapi`, `fastuuid`, `google*`, `huggingface_hub`, `lark-oapi`, `openai`, `opentelemetry-*`, `openviking*`, `redis`, `scikit-learn`, `scipy`, `SQLAlchemy`, `sympy`, `tiktoken`, `tokenizers`, `tree-sitter*`, `volcengine*`, `uvicorn`, etc.) were removed from `requirements.txt`.
- `python -m unittest discover -s tests/smoke`: PASS (68/68 tests in 1.301s)
- `python scripts/production_readiness_audit.py`: PASS (21/21 rules)
- **Status**: Pruned from 243 down to 206 essential deployment requirements, resolving the Streamlit Cloud build failure.
