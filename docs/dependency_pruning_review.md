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

### Second Round Pruning (Streamlit Cloud Linux & Python Runtime Compatibility)
On 2026-07-07, during Streamlit Cloud Linux deployment, `litellm==1.86.2` caused a Python version incompatibility, and `pywin32==312` caused a fatal platform error (`No matching distribution found for pywin32==312`) because `pywin32` is Windows-only while Streamlit Cloud runs on Linux. Following **Principle XII (Minimal & Clean Dependency Architecture)** in `constitution.md` v2.6.0, a comprehensive second pruning round was executed. Exactly 77 additional unused and OS-incompatible packages (`pywin32`, `win32_setctime`, `litellm`, `mcp`, `fastapi`, `google*`, `huggingface_hub`, `openai`, `opentelemetry-*`, `openviking*`, `tree-sitter*`, `volcengine*`, `grpcio*`, `protobuf`, etc.) were removed from `requirements.txt`.
- `python -m unittest discover -s tests/smoke`: PASS (68/68 tests in 1.113s)
- `python scripts/production_readiness_audit.py`: PASS (21/21 rules)
- **Status**: Pruned from 243 down to 166 clean, cross-platform essential requirements, fully resolving the Streamlit Cloud Linux build failure.

On 2026-07-08, GitHub Actions dependency scanning found newly reported vulnerabilities in unused direct requirements `ecdsa==0.19.2` and `PyPDF2==3.0.1`. Static search found no application or smoke-test imports for `ecdsa`, `python-jose`, or `PyPDF2`; the project already keeps `pypdf` and `pypdfium2` for PDF-related capability. Removed `ecdsa`, `python-jose`, and `PyPDF2`, reducing the deployment dependency set from 166 to 163 pinned requirements.
- `python -m pip_audit -r requirements.txt --no-deps --disable-pip --progress-spinner off --ignore-vuln CVE-2025-3000`: PASS (No known vulnerabilities found)
- `python -m unittest discover -s tests/smoke`: PASS (77/77 tests)
- `python scripts/production_readiness_audit.py`: PASS
