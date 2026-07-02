import subprocess
import time
import os

from playwright.sync_api import sync_playwright

st_process = subprocess.Popen(["streamlit", "run", "scratch_st.py", "--server.port", "8502", "--server.headless", "true"])
time.sleep(3)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8502")
        page.wait_for_selector('div[data-testid="stFileUploader"]', timeout=10000)
        
        # Get outer HTML of everything
        html = page.locator('div[data-testid="stMainBlockContainer"]').evaluate("el => el.outerHTML")
        print(html)
        browser.close()
finally:
    st_process.kill()
