progress_css = """
/* ============================================================
   NEO-BRUTALISM PROGRESS BAR
   ============================================================ */
div[data-testid="stProgressBar"] > div {
    background-color: #FFFFFF !important;
    border: 3px solid #0F172A !important;
    border-radius: 0px !important;
    height: 24px !important;
    box-shadow: 4px 4px 0px 0px #0F172A !important;
}

div[data-testid="stProgressBar"] > div > div {
    background-color: #FFDE59 !important;
    border-radius: 0px !important;
    height: 100% !important;
    border-right: 3px solid #0F172A !important;
}

/* Fix right border overlap when 100% */
div[data-testid="stProgressBar"] > div > div[style*="width: 100%"] {
    border-right: none !important;
}
"""

with open('static/style.css', 'a', encoding='utf-8') as f:
    f.write(progress_css)
print("Appended Neo-Brutalism Progress Bar CSS")
