# Plan: Laptop Responsive Design (1366x768)

## Overview
Implement an intermediate responsive tier in `static/style.css` targeting 1366x768 laptops to fix font clipping in `.neo-table` and oversized dashboard cards, while strictly protecting the `< 768px` mobile tier and Neo-Brutalist design tokens.

## Step-by-Step Implementation

1. **Inject Laptop Media Query**
   - File: `static/style.css`
   - Action: Add a new CSS block: `@media (max-width: 1366px) and (min-width: 769px) { ... }`.
   - Ensure it is placed *before* or *independent of* the `max-width: 768px` block to avoid cascading override issues.

2. **Scale Table Fonts & Padding (`.neo-table`)**
   - Inside the new laptop media query, target `.neo-table th` and `.neo-table td`.
   - Reduce `font-size` (e.g., from `0.85rem`/`0.8rem` to `0.75rem`/`0.7rem`).
   - Reduce `padding` slightly (e.g., from `8px 12px` to `6px 8px`) to give text more breathing room.

3. **Scale Dashboard Cards**
   - Identify Dashboard metric card classes (e.g., `.metric-card`, or equivalent Streamlit container selectors used for App Launchers).
   - Target these classes in the laptop media query.
   - Reduce `padding`, `min-height`, and header `font-size`.

4. **Verify Mobile Protection**
   - Confirm the existing `@media (max-width: 768px)` block remains completely untouched.

5. **Run Verification**
   - Run the full offline smoke test suite (`pytest tests/smoke/`) to ensure no Python syntax or component rendering logic was broken.
   - Visually check CSS syntax integrity (brace balance).