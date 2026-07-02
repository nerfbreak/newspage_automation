import re

with open('static/style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Replace the Toast CSS
toast_pattern = re.compile(r'/\* ============================================================\s+NEO-BRUTALISM TOASTS \(Sonner Style\)\s+============================================================ \*/.*?/\* ============================================================', re.DOTALL)
new_toast_css = """/* ============================================================
   NEO-BRUTALISM TOASTS (Sonner Style)
   ============================================================ */
div[data-testid="stToast"] {
    background-color: #FFFFFF !important;
    border: 3px solid #0F172A !important;
    box-shadow: 6px 6px 0px 0px #0F172A !important;
    border-radius: 0px !important;
}

div[data-testid="stToast"] * {
    color: #0F172A !important;
    font-family: "Source Sans 3", sans-serif !important;
}

div[data-testid="stToast"] button {
    background-color: #FFDE59 !important;
    border: 2px solid #0F172A !important;
    border-radius: 0px !important;
    box-shadow: 2px 2px 0px 0px #0F172A !important;
    transition: all 0.1s ease !important;
    margin-right: 8px !important;
}

div[data-testid="stToast"] button:hover {
    transform: translate(1px, 1px) !important;
    box-shadow: 1px 1px 0px 0px #0F172A !important;
    background-color: #FFC000 !important;
}

div[data-testid="stToast"] button svg {
    stroke: #0F172A !important;
    stroke-width: 2.5px !important;
}

/* ============================================================"""

if toast_pattern.search(css):
    css = toast_pattern.sub(new_toast_css, css)
else:
    print("Toast pattern not found!")

# Replace the Progress Bar CSS
progress_pattern = re.compile(r'/\* ============================================================\s+NEO-BRUTALISM PROGRESS BAR\s+============================================================ \*/.*', re.DOTALL)
new_progress_css = """/* ============================================================
   NEO-BRUTALISM PROGRESS BAR
   ============================================================ */
div[data-testid="stProgressBar"] > div,
div[data-testid="stProgress"] > div {
    background-color: #FFFFFF !important;
    border: 3px solid #0F172A !important;
    border-radius: 0px !important;
    height: 24px !important;
    box-shadow: 4px 4px 0px 0px #0F172A !important;
    overflow: hidden !important;
}

div[data-testid="stProgressBar"] > div > div,
div[data-testid="stProgress"] > div > div {
    background-color: #FFDE59 !important;
    border-radius: 0px !important;
    height: 100% !important;
    border-right: 3px solid #0F172A !important;
}

div[data-testid="stProgressBar"] > div > div[style*="width: 100%"],
div[data-testid="stProgress"] > div > div[style*="width: 100%"] {
    border-right: none !important;
}
"""

if progress_pattern.search(css):
    css = progress_pattern.sub(new_progress_css, css)
else:
    print("Progress pattern not found!")

with open('static/style.css', 'w', encoding='utf-8') as f:
    f.write(css)
print("Updated Toast and Progress Bar CSS")
