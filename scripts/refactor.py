import re

with open('playwright_engine.py', 'r', encoding='utf-8') as f:
    code = f.read()

context_manager = '''from contextlib import contextmanager

@contextmanager
def managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log):
    ensure_playwright()
    import sys, asyncio
    from playwright.sync_api import sync_playwright
    if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    with sync_playwright() as p:
        ui_log("SYS", "Spawning browser context with isolated session...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        try:
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log)
            yield page, browser
        finally:
            browser.close()
            ui_log("SYS", "Browser closed. Releasing session memory...")

'''

if 'managed_browser_session' not in code:
    code = code.replace('import asyncio\n', 'import asyncio\n' + context_manager, 1)

# For run_extract
ext_old = '''    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            ext_ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log)
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)'''

ext_new = '''    try:
        with managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log) as (page, browser):
            _navigate_to_import_export(page, TIMEOUT_MS, ext_ui_log)'''

code = code.replace(ext_old, ext_new)

# For run_extract close block
ext_close_old = '''            browser.close()
            ext_ui_log("SYS", "Browser closed. Releasing session memory...")
            ext_ui_log("SYS", f"Parsing payload file: {real_filename}...")'''
ext_close_new = '''            ext_ui_log("SYS", f"Parsing payload file: {real_filename}...")'''
code = code.replace(ext_close_old, ext_close_new)

# For run_sales_extract
sales_old = '''    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            ext_ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log)'''
sales_new = '''    try:
        with managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, ext_ui_log) as (page, browser):'''
code = code.replace(sales_old, sales_new)

# For run_sales_extract close block
sales_close_old = '''            browser.close()
            ext_ui_log("SYS", "Browser closed. Releasing session memory...")
            ext_ui_log("SYS", f"Parsing payload file: {real_filename}...")'''
code = code.replace(sales_close_old, ext_close_new)

# For run_execution
exec_old = '''    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()

            _login(page, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log)
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, ui_log)'''
exec_new = '''    try:
        with managed_browser_session(bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log) as (page, browser):
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, ui_log)'''
code = code.replace(exec_old, exec_new)

# For run_execution close block
exec_close_old = '''            browser.close()
            ui_log("SYS", "Browser closed. Releasing session memory...")
            
            st.session_state.execute_done = True'''
exec_close_new = '''            st.session_state.execute_done = True'''
code = code.replace(exec_close_old, exec_close_new)

# For run_promotion_sync
promo_old = '''    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        
        with sync_playwright() as p:
            promo_ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            
            _login(page, user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, promo_ui_log)'''
promo_new = '''    try:
        with managed_browser_session(user_id_np, pass_np, selected_distributor, URL_LOGIN, TIMEOUT_MS, promo_ui_log) as (page, browser):'''
code = code.replace(promo_old, promo_new)

# For run_promotion_sync close block
promo_close_old = '''            browser.close()
            promo_ui_log("SYS", "Browser closed. Releasing session memory...")
            promo_ui_log("SYS", f"Parsing payload file: {real_filename}...")'''
promo_close_new = '''            promo_ui_log("SYS", f"Parsing payload file: {real_filename}...")'''
code = code.replace(promo_close_old, promo_close_new)


# For run_execution_manual
exec_man_old = '''    ensure_playwright()
    try:
        if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        with sync_playwright() as p:
            ui_log("SYS", "Spawning browser context with isolated session...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(no_viewport=True)
            page = context.new_page()

            _login(page, bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log)
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, ui_log)'''
exec_man_new = '''    try:
        with managed_browser_session(bot_user, bot_pass, selected_distributor, URL_LOGIN, TIMEOUT_MS, ui_log) as (page, browser):
            _navigate_to_stock_adjustment(page, TIMEOUT_MS, ui_log)'''
code = code.replace(exec_man_old, exec_man_new)

# For run_execution_manual close block
exec_man_close_old = '''            browser.close()
            ui_log("SYS", "Browser closed. Releasing session memory...")
            
            st.session_state.is_bot_running = False'''
exec_man_close_new = '''            st.session_state.is_bot_running = False'''
code = code.replace(exec_man_close_old, exec_man_close_new)


with open('playwright_engine.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Playwright Engine Refactored.")
