# Optimize Newspage — Streamlit Automation

Web-based automation tool for inventory adjustment, sales extraction, and promotion comparison on Newspage.

## Features

- **Inventory Adjustment** — Extract, compare, and execute stock adjustments
- **Sales Extraction** — Export sales data by date range
- **Promotion Comparison** — Sync and compare promotion data with SharePoint
- **Dashboard** — Real-time system overview and job history

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | [Streamlit](https://streamlit.io/) (Python) |
| Automation | [Playwright](https://playwright.dev/) (headless Chromium) |
| Database | [Supabase](https://supabase.com/) (PostgreSQL) |
| Encryption | Fernet (AES-256) |

## Project Structure

```
newspage_automation/
├── app.py                  # Streamlit entry point (login, navigation)
├── pages/
│   ├── 0_dashboard.py      # System overview
│   ├── 1_inventory_adjustment.py
│   ├── 2_sales_extraction.py
│   └── 3_promotion_comparison.py
├── database.py             # Supabase queries, encryption
├── utils.py                # Shared utilities, Telegram alerts
├── playwright_engine.py    # Headless browser automation
├── data_processor.py       # CSV/Excel data processing
├── static/                 # CSS, fonts
├── requirements.txt        # Python dependencies
└── .streamlit/config.toml  # Streamlit theme config
```

## Setup

### Prerequisites

- Python 3.10+
- Chromium browser (installed via Playwright)

### Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

### Configuration

Create `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-service-role-key"
MASTER_KEY = "your-fernet-key"
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""
NP_USER_SUPER = ""
NP_PASS_SUPER = ""
```

### System Config (Supabase)

Runtime settings stored in `system_config` table:

| Key | Description |
|-----|-------------|
| `URL_LOGIN` | Newspage login URL |
| `TIMEOUT_MS` | Playwright timeout (ms) |
| `TABLE_UPDATE_INTERVAL` | UI refresh interval (s) |
| `REASON_CODE` | Stock adjustment reason |
| `WAREHOUSE` | Default warehouse |

### Run

```bash
streamlit run app.py
```

## Related

- **Android client + FastAPI backend** → [automation_apps](https://github.com/nerfbreak/automation_apps)

## License

Built by **Muhammad Rizki Firdaus**
