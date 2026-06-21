"""
Flat Design Corporativo Theme for Streamlit
Injects custom CSS to override default Streamlit styling
"""

import streamlit as st

def load_theme():
    """Load the Flat Design Corporativo theme via custom CSS injection."""
    
    st.markdown("""
    <style>
    /* Import Lato Font */
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap');

    /* Design System Variables */
    :root {
        --corporate-blue: #007BFF;
        --dark-grey-flat: #343A40;
        --white-flat: #FFFFFF;
        --light-grey-flat: #F8F9FA;
        --success-green: #28A745;
        --warning-orange: #FFC107;
        --danger-red: #DC3545;
        --info-cyan: #17A2B8;
        --flat-shadow-strength: 0.1;
        --font-flat: 'Lato', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    /* Global Styles */
    .stApp {
        font-family: var(--font-flat);
        color: var(--dark-grey-flat);
        background-color: var(--light-grey-flat);
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-flat);
        font-weight: 700;
        color: var(--dark-grey-flat);
        letter-spacing: -0.02em;
    }
    
    p, span, div, label {
        font-family: var(--font-flat);
        font-weight: 400;
        line-height: 1.6;
    }
    
    code, pre {
        font-family: var(--font-mono);
        font-size: 0.875rem;
    }

    /* Main Container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1280px;
    }

    /* Buttons - Sharp Corners & Corporate Blue */
    .stButton > button {
        border-radius: 4px !important;
        font-family: var(--font-flat);
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.5rem 1.5rem;
        border: none;
        transition: all 0.2s ease-out;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        filter: brightness(0.92);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }

    /* Primary Button Override */
    .stButton > button[kind="primary"] {
        background-color: var(--corporate-blue) !important;
        color: var(--white-flat) !important;
    }

    /* Inputs - Sharp Borders */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiselect > div > div > select {
        border-radius: 4px !important;
        border: 1px solid #ced4da !important;
        font-family: var(--font-flat);
        padding: 0.5rem 0.75rem;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stMultiselect > div > div > select:focus {
        border-color: var(--corporate-blue) !important;
        box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25) !important;
    }

    /* Cards - Custom Class */
    .corporate-card {
        background-color: var(--white-flat);
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        transition: transform 0.2s ease-out, box-shadow 0.2s ease-out;
        margin-bottom: 1rem;
    }
    
    .corporate-card:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--white-flat);
        border-right: 1px solid #e9ecef;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* Hide Default Streamlit Branding (Optional) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Utility Classes for Icons (SVG inline handling) */
    .icon-sm { width: 16px; height: 16px; vertical-align: middle; }
    .icon-md { width: 24px; height: 24px; vertical-align: middle; }
    .icon-lg { width: 32px; height: 32px; vertical-align: middle; }

    </style>
    """, unsafe_allow_html=True)

def create_card(title, content, icon_svg=None):
    """Helper to create a styled corporate card."""
    icon_html = f'<span style="margin-right: 8px;">{icon_svg}</span>' if icon_svg else ''
    st.markdown(f"""
    <div class="corporate-card">
        <h3 style="margin-top: 0; display: flex; align-items: center;">{icon_html}{title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)
