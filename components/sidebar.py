# -*- coding: utf-8 -*-
"""
Sidebar Component for Dashboard v6.0
=====================================
Filters, data status, and export functionality.
"""
import streamlit as st
import pandas as pd
from typing import Tuple
from data.loader import get_data_status
from config.settings import VERSION


def render_sidebar(df_original: pd.DataFrame) -> pd.DataFrame:
    """
    Render sidebar with filters and return filtered DataFrame.
    
    Args:
        df_original: Original unfiltered DataFrame
        
    Returns:
        Filtered DataFrame based on user selections
    """
    with st.sidebar:
        # Header
        st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=60)
        st.title(f"Analytics v{VERSION[:3]}")
        st.caption("Modular Business Intelligence")
        
        st.divider()
        
        # Data Status Section
        _render_data_status(df_original)
        
        st.divider()
        
        # Date Filter
        df = _apply_date_filter(df_original)
        
        st.divider()
        
        # Additional Filters
        df = _apply_filters(df)
        
        st.divider()
        
        # Auto Refresh
        _render_auto_refresh()
        
        # Export
        _render_export(df)
        
    return df


def _render_data_status(df: pd.DataFrame):
    """Render data status metrics."""
    st.subheader("📊 Data Status")
    
    status = get_data_status(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", f"{status['total']:,}")
    with col2:
        st.metric("AI Done", f"{status['processed']:,}")
    
    if status['total'] > 0:
        success_rate = status['processed'] / status['total']
        st.progress(success_rate, text=f"{success_rate*100:.1f}% Processed")


def _apply_date_filter(df_original: pd.DataFrame) -> pd.DataFrame:
    """Apply date range filter."""
    st.subheader("📅 Date Range")
    
    if 'conversation_date' not in df_original.columns or df_original.empty:
        return df_original.copy()
    
    df_original['conversation_date'] = pd.to_datetime(
        df_original['conversation_date'], 
        errors='coerce'
    )
    
    min_date = df_original['conversation_date'].min()
    max_date = df_original['conversation_date'].max()
    
    if pd.isna(min_date) or pd.isna(max_date):
        return df_original.copy()
    
    date_range = st.date_input(
        "Select Period",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        return df_original[
            (df_original['conversation_date'].dt.date >= start_date) &
            (df_original['conversation_date'].dt.date <= end_date)
        ].copy()
    
    return df_original.copy()


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply platform and intent filters."""
    st.subheader("🎛️ Filters")
    
    # Platform Filter
    if 'platform' in df.columns and not df.empty:
        platforms = ['All'] + df['platform'].dropna().unique().tolist()
        selected_platform = st.selectbox("Platform", platforms)
        if selected_platform != 'All':
            df = df[df['platform'] == selected_platform]
    
    # Intent Filter
    if 'intent_primary' in df.columns and not df.empty:
        intents = ['All'] + df['intent_primary'].dropna().unique().tolist()
        selected_intent = st.selectbox("Intent", intents)
        if selected_intent != 'All':
            df = df[df['intent_primary'] == selected_intent]
    
    return df


def _render_auto_refresh():
    """Render auto-refresh controls."""
    st.subheader("🔄 Auto Refresh")
    
    auto_refresh = st.toggle("Enable Auto-Refresh", value=False)
    refresh_interval = st.selectbox(
        "Interval",
        [30, 60, 120, 300],
        format_func=lambda x: f"{x} seconds" if x < 60 else f"{x//60} minutes",
        disabled=not auto_refresh
    )
    
    if auto_refresh:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh_counter")
            st.info(f"⏱️ Auto-refresh every {refresh_interval}s")
        except ImportError:
            st.warning("streamlit-autorefresh not installed. Add to requirements.txt.")
    
    # Manual Refresh
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


def _render_export(df: pd.DataFrame):
    """Render export button."""
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export CSV",
            csv,
            "chat_analytics_export.csv",
            "text/csv",
            use_container_width=True
        )
