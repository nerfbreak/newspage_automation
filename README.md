# Optimize Newspage: Stock Adjustment Automation Engine

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3EC988?style=for-the-badge&logo=supabase&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)

A production-grade automation toolkit for comparing and reconciling stock data between **Newspage** (central system) and **Distributor** systems. Designed for high accuracy, operational security, and zero-touch execution.

---

## Key Features

- **Auto-Extraction** — Pulls real-time inventory and sales data from Newspage via headless Chromium, no manual export needed.
- **Smart Reconciliation** — Instant comparison between Newspage and distributor stock with automatic SKU mapping and multiplier logic.
- **Auto-Adjustment Bot** — Injects stock differences into Newspage's Stock Adjustment module automatically with live terminal logging.
- **Sales Extraction** — Extracts date-range sales data per distributor for analysis and reporting.
- **Promotion Comparison** — Syncs promotion data from Newspage and compares against SharePoint MDM tracker for conflict detection.
- **Stock Mutation** — Tracks stock movement and mutation records across distributors.
- **Clearance Stock** — Monitors and reconciles clearance inventory.
- **Initial Stock** — Manages initial stock setup and baseline data.
- **Enterprise Security** — `bcrypt` password hashing, `AES-256 Fernet` credential encryption, session timeout, and login lockout.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web App | [Streamlit](https://streamlit.io/) |
| Automation Engine | [Playwright](https://playwright.dev/) (headless Chromium) |
| Database | [Supabase](https://supabase.com/) (PostgreSQL) |
| Security | Bcrypt + Cryptography (Fernet/AES-256) |
| Alerts | Telegram Bot API (optional) |

---

## Project Structure

```
.
├── app.py                          # Entry point — auth gate, session, page router
├── pages/
│   ├── 0_dashboard.py              # Live DB status, KPI metrics, quick-launch
│   ├── 1_inventory_adjustment.py   # Extract → Compare → Execute workflow
│   ├── 2_sales_extraction.py       # Date-range sales extraction
│   ├── 3_promotion_comparison.py   # Promo sync + SharePoint comparison
│   ├── 4_stock_mutation.py         # Stock mutation tracking
│   ├── 5_clearance_stock.py        # Clearance stock monitoring
│   └── 6_initial_stock.py          # Initial stock baseline management
├── database.py                     # Supabase client, config, auth, vault queries
├── utils.py                        # CSS injection, sidebar, session helpers
├── playwright_engine.py            # Core Playwright automation logic
├── data_processor.py               # CSV/XLSX loading and reconciliation logic
├── static/                         # Fonts, stylesheets
│   ├── style.css                   # Main application theme
│   └── login.css                   # Login page styling
└── .streamlit/
    └── config.toml                 # Streamlit theme configuration
```

---

## Setup & Installation

### 1. Supabase Database

Create the required tables in your Supabase project:

- `users_auth` — user credentials (bcrypt hashed passwords)
- `distributor_vault` — distributor info + encrypted NP credentials
- `system_config` — runtime configuration (URLs, timeouts, defaults)

Insert runtime config values:

```sql
INSERT INTO system_config (config_key, config_value)
VALUES
  ('REASON_CODE', 'SA2'),
  ('WAREHOUSE', 'GOOD_WHS'),
  ('URL_LOGIN', 'https://your-newspage-url/Logon.aspx'),
  ('TIMEOUT_MS', '60000'),
  ('TABLE_UPDATE_INTERVAL', '5');
```

### 2. Secrets Configuration

Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key"
MASTER_KEY = "your-fernet-encryption-key"   # AES-256 Fernet key

# Optional
TELEGRAM_BOT_TOKEN = "your-bot-token"
TELEGRAM_CHAT_ID = "your-chat-id"
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Run Locally

```bash
streamlit run app.py
```

---

## Security

All runtime configuration containing sensitive URLs and credentials is stored in **Supabase** (`system_config` table), not in source code. This keeps the repository safe to make public.

- **Password Hashing** — User passwords are stored as `bcrypt` hashes, never plaintext.
- **Credential Encryption** — Distributor Newspage passwords are encrypted with `AES-256 Fernet` before being written to the database. The `MASTER_KEY` must be kept secret.
- **Session Management** — 1-hour idle timeout, 5-attempt lockout (5 min), brute-force throttle.

---

*Built by **Muhammad Rizki Firdaus** **@cakwe.sore** · 2026*
