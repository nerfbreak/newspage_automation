# Project Decisions Log

This file logs architectural and technical decisions made during development to ensure the AI agent (and sub-agents) maintain context and avoid repeating mistakes.

## [2026-06-24] Implementation of AI-Facing Memory System
- **Decision**: Implemented a markdown-based internal memory system (`docs/memory/`) instead of a standalone Vector DB/Chatbot app.
- **Reason**: The user clarified that the goal is simply for the AI to remember its context and not go off-track across sessions, rather than building a user-facing RAG application.
- **Consequence**: Added `.agents/AGENTS.md` to force the AI to read this memory folder upon starting tasks.

## [Legacy] Technology Choices
- **Streamlit**: Chosen for rapid UI development of internal tools.
- **Playwright**: Chosen for robust headless browser automation to extract and inject data into the legacy Newspage ERP.
- **Supabase**: Chosen for managed PostgreSQL, auth, and configuration storage.
