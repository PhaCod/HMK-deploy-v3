# -*- coding: utf-8 -*-
"""
CSS Styles for Dashboard v7.0
==============================
Premium Dark Mode with Glassmorphism.
"""
import streamlit as st

# ============================================
# CUSTOM CSS
# ============================================
CUSTOM_CSS = """
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Cards with Glassmorphism */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        margin: 10px 0;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        color: #00f5d4 !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
        font-size: 0.85rem !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 6px;
        flex-wrap: wrap;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #a0a0a0;
        padding: 8px 16px;
        font-size: 0.85rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Dividers */
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Info/Success/Warning boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
    }
    
    /* Tables */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
    }
    
    /* Plotly Charts Background */
    .js-plotly-plot .plotly {
        background: transparent !important;
    }
    
    /* Selectbox and Multiselect */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.1);
    }
    
    /* Date Input */
    .stDateInput > div > div {
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* Hide Streamlit branding and header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppHeader {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
</style>
"""


def apply_styles():
    """Apply custom CSS styles to the dashboard."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
