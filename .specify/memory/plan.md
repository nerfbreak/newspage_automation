# Plan: Bot Task Monitor Dashboard

1. **Database Tracking**
   - Add `active_bot_tasks` table to schema script.
   - Add functions to `database.py` to insert/delete/select active tasks.

2. **Dashboard UI**
   - Insert a `render_active_tasks` component before the main overview section in `pages/0_dashboard.py`.
   - Add a refresh button or use `st_autorefresh` if available (manual refresh via button is safer for Streamlit Cloud).
   - Apply Neo-Brutalism CSS (3px solid border, 6px 6px shadow, `#FFFFFF` background, sharp corners).

3. **Playwright Integration**
   - In `playwright_engine.py`, at the start of major execution functions, call `register_active_task`.
   - Before returning or inside the `terminate_callback`, call `clear_active_task`.
   - Or, easier: wrap the `managed_browser_session` or just inject cleanly at the top and bottom of functions.
