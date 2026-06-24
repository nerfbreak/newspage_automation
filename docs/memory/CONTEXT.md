# Project Context: Optimize Newspage

## 1. Core Purpose
"Optimize Newspage" is an internal automation tool built with Streamlit and Playwright.
It eliminates manual stock reconciliation between the Newspage central ERP and distributor systems via automated extraction, comparison, and adjustment injection.

## 2. Technical Stack
- **Frontend**: Streamlit
- **Backend / DB**: Python, Supabase (PostgreSQL)
- **Automation Engine**: Playwright (Headless Chromium)

## 3. Key Modules
1. Inventory Adjustment
2. Sales Extraction
3. Promotion Comparison
4. Stock Mutation
5. Clearance Stock
6. Initial Stock

## 4. Current State
As of v1.0, all 6 modules are functional. Authentication, credential encryption, and audit logging are implemented. 
Known technical debt exists (e.g., `importlib.reload` breaking caches, non-thread-safe module caches).
