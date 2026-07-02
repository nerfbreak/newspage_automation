import subprocess
import time
from playwright.sync_api import sync_playwright

st_process = subprocess.Popen(["streamlit", "run", "scratch_st.py", "--server.port", "8502", "--server.headless", "true"])
time.sleep(3)

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8502")
        time.sleep(3) # wait for render
        html = page.evaluate("document.body.innerHTML")
        with open("scratch_st_dom.txt", "w", encoding="utf-8") as f:
            f.write(html)
        browser.close()
finally:
    st_process.kill()
