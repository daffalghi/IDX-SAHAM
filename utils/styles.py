import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Remove sidebar background to look sleeker */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Premium Cards / Containers for metrics */
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease !important;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Metric Values Gradient */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #F63366, #ff9a9e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        font-weight: 500 !important;
        color: #94a3b8 !important;
        margin-bottom: 4px !important;
    }

    /* Primary Buttons Styling */
    .stButton>button {
        background: linear-gradient(135deg, #F63366 0%, #f43f5e 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px 0 rgba(246, 51, 102, 0.39) !important;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(246, 51, 102, 0.6) !important;
        background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%) !important;
    }
    
    /* Expanders styling */
    .streamlit-expanderHeader {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 1rem !important;
    }
    
    /* Inputs */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input {
        border-radius: 10px !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
    }
    
    /* Selectbox */
    div[data-baseweb="select"] > div {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    /* Header Gradient */
    h1 {
        background: -webkit-linear-gradient(45deg, #ffffff, #93c5fd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
        padding-bottom: 10px !important;
    }
    
    /* Subheaders */
    h2, h3 {
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        letter-spacing: -0.2px !important;
    }
    
    /* Layout Container adjustments */
    [data-testid="block-container"] {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1200px !important;
    }
    
    /* Info/Warning Boxes */
    div[data-testid="stMarkdownContainer"] > div[role="alert"] {
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)
