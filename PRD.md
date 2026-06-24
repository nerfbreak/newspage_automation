# PRD: Optimize Newspage — Stock Adjustment Automation Engine

## 1. Product Overview

**Product Name:** Optimize Newspage  
**Version:** 1.0  
**Type:** Internal Automation Tool (Streamlit + Playwright)  
**Target Users:** IT Support / Stock Controllers at Newspage distributors  
**Core Value:** Eliminate manual stock reconciliation between Newspage (central ERP) and distributor systems via automated extraction, comparison, and adjustment injection.

---

## 2. Problem Statement

Distributors maintain stock in **Newspage** (central system) but also have local records. Monthly reconciliation requires:
- Manual export from Newspage → Excel
- Manual comparison with distributor files
- Manual entry of adjustments in Newspage Stock Adjustment module

**Pain points:** Human error, 2-4 hours per distributor per month, no audit trail, credential sharing via chat.

---

## 3. User Personas

| Persona | Role | Needs |
|---------|------|-------|
| **Stock Controller** | Operations | Run extraction, upload distributor file, review diffs, execute adjustments |
| **IT Support (Admin)** | Technical | Manage distributor credentials, monitor bot health, view audit logs |
| **Superuser** | Cross-distributor | Run promotion sync, global extractions |

---

## 4. Functional Requirements

### 4.1 Authentication & Security (Implemented)
- **FR-AUTH-01:** Username/password login with bcrypt verification against Supabase `users_auth`
- **FR-AUTH-02:** 5-attempt lockout (5 min), 1-hour idle session timeout
- **FR-AUTH-03:** Distributor NP credentials encrypted with AES-256 Fernet (MASTER_KEY)
- **FR-AUTH-04:** Telegram alerts on lockout/fatal errors (optional)

### 4.2 Dashboard (Implemented)
- **FR-DASH-01:** KPI cards — Total Extractions, Last Extraction, Registered Distributors
- **FR-DASH-02:** System health — Playwright bot status, DB connection, last sync time, synced logs count
- **FR-DASH-03:** Navigation hub to all 6 modules

### 4.3 Module 1: Inventory Adjustment (Implemented)
| ID | Requirement |
|----|-------------|
| FR-INV-01 | Extract real-time stock from Newspage via Playwright (headless Chromium) |
| FR-INV-02 | Upload distributor stock file (CSV/XLSX/ZIP) |
| FR-INV-03 | Column mapping UI for both sources |
| FR-INV-04 | SKU normalization: prefix `0` for target SKUs (exclude `8021803`, `8021804`) |
| FR-INV-05 | Multiplier rules per distributor (from `distributor_sku_multiplier` table) |
| FR-INV-06 | Outer join comparison → Match / Mismatch / Selisih |
| FR-INV-07 | Review table with editable qty before execution |
| FR-INV-08 | **Auto Compare** mode: automated adjustment injection via Playwright |
| FR-INV-09 | **Manual Entry** mode: free-form SKU + PAC/CAR/EA entry |
| FR-INV-10 | Live terminal logging during execution |
| FR-INV-11 | Progress bar + per-SKU status (Success/Failed/Invalid) |
| FR-INV-12 | Abort on any failure → no document saved to Newspage |
| FR-INV-13 | Audit log to `adjustment_logs` table |

### 4.4 Module 2: Sales Extraction (Implemented)
| ID | Requirement |
|----|-------------|
| FR-SAL-01 | Date-range selection (default: current month) |
| FR-SAL-02 | Playwright extraction of "Invoice Detail" interface (`E_28880804000000001`) |
| FR-SAL-03 | JS-based CalendarExtender date injection (bypass UI) |
| FR-SAL-04 | Download CSV → browser download button |

### 4.5 Module 3: Promotion Comparison (Implemented)
| ID | Requirement |
|----|-------------|
| FR-PRO-01 | Upload SharePoint Excel (sheets: "tracker MDM", "BDP") |
| FR-PRO-02 | Multi-interface extraction (5 promo interfaces in one job) |
| FR-PRO-03 | ZIP download containing multiple CSVs (pipe-delimited) |
| FR-PRO-04 | Smart merge on Promo Code (case-insensitive) |
| FR-PRO-05 | Validation: dates, status conflict → MATCH / CONFLICT / MISSING |
| FR-PRO-06 | Filterable results table + CSV export |

### 4.6 Module 4: Stock Mutation (Implemented)
| ID | Requirement |
|----|-------------|
| FR-MUT-01 | Two-distributor flow: Sender (deduct) → Receiver (add) |
| FR-MUT-02 | Single upload file → preview both sides |
| FR-MUT-03 | Parallel execution: two browser contexts simultaneously |
| FR-MUT-04 | Dual terminal logs, dual progress bars |
| FR-MUT-05 | Same adjustment engine as Inventory (reuse `run_execution`) |

### 4.7 Module 5: Clearance Stock (Implemented)
| ID | Requirement |
|----|-------------|
| FR-CLR-01 | Extract Newspage stock → auto-convert to negative qty |
| FR-CLR-02 | Review table with "Clear Qty" preview |
| FR-CLR-03 | Execute as standard adjustment (negative quantities) |

### 4.8 Module 6: Initial Stock (Implemented)
| ID | Requirement |
|----|-------------|
| FR-INI-01 | Upload SKU + Qty file (no Newspage extraction) |
| FR-INI-02 | Column mapping + preview |
| FR-INI-03 | Validate qty > 0 (mark invalid ≤ 0) |
| FR-INI-04 | Execute positive adjustments only |

---

## 5. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Extraction ≤ 4 min (240s download timeout); Execution ≤ 30s per SKU |
| **Reliability** | Playwright retry on timeout; graceful degradation on partial failure |
| **Security** | No plaintext passwords in code/logs; Fernet key rotation documented |
| **Usability** | Streamlit Design System theme; responsive; Indonesian language UI |
| **Observability** | Terminal-style logs with timestamps, module tags, ms deltas |
| **Maintainability** | Modular pages; shared utils; config in Supabase (not code) |
| **Deployment** | Docker-ready; `playwright install chromium` in CI; headless mode |

---

## 6. Data Model (Supabase Tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users_auth` | App users | `username`, `password` (bcrypt) |
| `distributor_vault` | Distributor NP creds | `nama_distributor`, `np_user_id`, `np_password` (encrypted) |
| `system_config` | Runtime config | `config_key`, `config_value` (REASON_CODE, WAREHOUSE, URL_LOGIN, TIMEOUT_MS, TABLE_UPDATE_INTERVAL) |
| `sku_formatting_rules` | Target SKU list | `sku_code` |
| `distributor_sku_multiplier` | Qty multipliers | `np_user_id`, `sku_target`, `multiplier_value` |
| `distributor_exceptions` | Warehouse overrides | `distributor_id`, `target_warehouse` |
| `extraction_history` | Audit trail | `distributor_name`, `extracted_by`, `status`, `created_at` |
| `adjustment_logs` | Execution audit | `sku`, `qty`, `status`, `keterangan`, `np_user`, `created_at` |
| `audit_logs` | System events | generic audit |

---

## 7. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit App                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │Dashboard│ │Inventory│ │ Sales   │ │Promotion│ │Mutation│ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬───┘ │
└───────┼───────────┼───────────┼───────────┼───────────┼─────┘
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Shared Services                          │
│  database.py  │  utils.py  │  data_processor.py             │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Playwright Engine                          │
│  run_extract / run_sales_extract / run_promotion_sync       │
│  run_execution / run_execution_manual / run_mutasi_execution│
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              External Systems                               │
│  Newspage (Chromium)  │  Supabase (PostgreSQL)  │ Telegram  │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Configuration (Supabase `system_config`)

| Key | Default | Description |
|-----|---------|-------------|
| `REASON_CODE` | `SA2` | Stock adjustment reason code |
| `WAREHOUSE` | `GOOD_WHS` | Default warehouse |
| `URL_LOGIN` | — | Newspage login URL |
| `TIMEOUT_MS` | `60000` | Playwright default timeout |
| `TABLE_UPDATE_INTERVAL` | `5` | UI table refresh every N rows |

---

## 9. Deployment Requirements

| Component | Spec |
|-----------|------|
| Python | 3.11+ |
| Browser | Chromium (Playwright) |
| Memory | ≥ 2GB (browser + pandas) |
| Network | Access to Newspage URL + Supabase HTTPS |
| Secrets | `.streamlit/secrets.toml` with SUPABASE_URL, SUPABASE_KEY, MASTER_KEY, TELEGRAM_* |

---

## 10. Known Technical Debt (from Code Review)

| Priority | Item |
|----------|------|
| **Critical** | `importlib.reload(playwright_engine)` in 6 pages — breaks singleton caches |
| **Critical** | Module-level caches in `database.py` not thread-safe for multi-user |
| **High** | Duplicate terminal logging code (~200 lines across pages) |
| **High** | Hardcoded Newspage selectors (brittle) |
| **Medium** | `safe_parse_numeric` untested, complex |
| **Medium** | No unit tests |
| **Medium** | Session timeout logic resets on every render |

---

## 11. Future Enhancements (Backlog)

- [ ] **Reflex migration** — `database.py` already has framework-agnostic functions
- [ ] **Scheduler** — Cron-style automatic daily extraction
- [ ] **Multi-warehouse support** — Beyond `GOOD_WHS` default
- [ ] **Role-based access** — Viewer vs Operator vs Admin
- [ ] **API layer** — Headless mode for integration with other tools
- [ ] **Test suite** — Pytest for data_processor, utils, database

---

## 12. Acceptance Criteria for v1.0

- [x] All 6 modules functional end-to-end
- [x] Authentication with lockout/timeout
- [x] Credential encryption at rest
- [x] Audit logging on every adjustment
- [x] Telegram alerts on critical events
- [x] Docker build passes
- [x] Deployed to production Supabase + Streamlit Cloud / VM

---

## 13. Appendix: File Inventory

```
.
├── app.py                          # Entry point, auth, navigation
├── database.py                     # Supabase client, auth, vault, config
├── data_processor.py               # CSV/XLSX loading, reconciliation logic
├── playwright_engine.py            # All Playwright automation (963 lines)
├── utils.py                        # UI helpers, CSS, session, logging, numeric parsing
├── pages/
│   ├── 0_dashboard.py              # KPIs, nav, system health
│   ├── 1_inventory_adjustment.py   # Extract → Compare → Execute (Auto/Manual)
│   ├── 2_sales_extraction.py       # Date-range invoice extraction
│   ├── 3_promotion_comparison.py   # SharePoint vs Newspage promo sync
│   ├── 4_stock_mutation.py         # Inter-distributor transfer
│   ├── 5_clearance_stock.py        # Negative adjustment flow
│   └── 6_initial_stock.py          # Baseline stock setup
├── static/
│   ├── style.css                   # Streamlit Design System theme
│   └── login.css                   # Full-screen login page
├── .streamlit/
│   ├── config.toml                 # Theme + server config
│   └── secrets.toml                # Runtime secrets (not in git)
├── requirements.txt                # Python deps
└── README.md                       # Setup docs
```