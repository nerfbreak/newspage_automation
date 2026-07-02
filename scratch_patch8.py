toast_css = """
/* ============================================================
   NEO-BRUTALISM TOASTS (Sonner Style)
   ============================================================ */
div[data-testid="stToast"] {
    background-color: #FFFFFF !important;
    border: 3px solid #0F172A !important;
    box-shadow: 6px 6px 0px 0px #0F172A !important;
    border-radius: 0px !important;
    padding: 16px 20px !important;
    color: #0F172A !important;
    font-family: "Source Sans 3", sans-serif !important;
    font-weight: 700 !important;
    transition: all 0.2s ease-in-out !important;
    margin-bottom: 12px !important;
}

div[data-testid="stToast"]:hover {
    transform: translate(2px, 2px) !important;
    box-shadow: 4px 4px 0px 0px #0F172A !important;
}

/* Toast message text */
div[data-testid="stToast"] [data-testid="stMarkdownContainer"] p {
    color: #0F172A !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
}

/* Close button inside toast */
div[data-testid="stToast"] button {
    border: 2px solid #0F172A !important;
    background-color: #FFDE59 !important;
    color: #0F172A !important;
    border-radius: 0px !important;
    box-shadow: 2px 2px 0px 0px #0F172A !important;
    transition: all 0.1s ease !important;
    opacity: 1 !important;
    padding: 2px !important;
    right: 12px !important;
    top: 12px !important;
}

div[data-testid="stToast"] button:hover {
    transform: translate(1px, 1px) !important;
    box-shadow: 1px 1px 0px 0px #0F172A !important;
    background-color: #FFC000 !important;
}

div[data-testid="stToast"] button svg {
    stroke: #0F172A !important;
    stroke-width: 3px !important;
    width: 14px !important;
    height: 14px !important;
}
"""

with open('static/style.css', 'a', encoding='utf-8') as f:
    f.write(toast_css)
print("Appended Neo-Brutalism Toast CSS")
