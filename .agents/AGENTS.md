# Project AI Rules: Newspage Automation (Optimize)

## Core Memory Principle
As an AI agent working on this project, you must act as the "AI-assisted Distributed Project Memory System". 
Whenever the user asks you to implement a new feature, fix a bug, or make architectural changes:
1. **READ FIRST**: Always read `.agents/MEMORY.md` and `product_requirements_document.md` to understand the current context and prevent hallucinations.
2. **UPDATE MEMORY**: After successfully completing a task, you MUST append a brief summary of what you did to `.agents/MEMORY.md` under the "Changelog & Decisions" section. Keep it concise.
3. **DO NOT GUESS**: Rely on the existing codebase files and the `elements_yang_dipakai_dinewspage_sebagai_otomasi.md` for UI selectors instead of guessing.

## Architectural Notes
- The app uses **Streamlit** for frontend and **Playwright** for headless automation.
- Never hardcode credentials; always use **Supabase** and `.streamlit/secrets.toml`.
- Always respect the `session_state` management logic in `app.py` (e.g., `logged_in`, `current_user`, `last_activity`).
