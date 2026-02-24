# -*- coding: utf-8 -*-
"""
Tab Explorer - Dashboard v6.0
==============================
Data explorer for AI-enriched records with column selection.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.charts import create_chart_layout
from config.settings import COLUMN_GROUPS
from components.drill_down import render_drill_down_panel


def render(df: pd.DataFrame):
    """
    Render Data Explorer tab.
    
    Args:
        df: Filtered DataFrame
    """
    st.header("🔍 Data Explorer")
    st.caption("Deep dive into raw AI-enriched records")
    
    # Quick Stats
    _render_quick_stats(df)
    
    st.divider()
    
    # Column Selection
    final_cols = _render_column_selector(df)
    
    st.divider()
    
    # Search and Filter
    display_df = _render_search_filter(df, final_cols)
    
    # Data Preview
    _render_data_preview(display_df)
    
    # Column Statistics
    st.divider()
    _render_column_stats(df, final_cols)

    # ── Conversation Detail Viewer ──────────────────
    st.divider()
    st.subheader("💬 Conversation Detail Viewer")
    if 'conversation_id' in df.columns:
        conv_ids = df['conversation_id'].dropna().unique()[:200]
        sel_conv = st.selectbox("Select Conversation ID", ["— Select —"] + list(conv_ids), key="explorer_conv_id")
        if sel_conv and sel_conv != "— Select —":
            render_drill_down_panel(
                df, "conversation_id", sel_conv,
                title=f"💬 Conversation: {sel_conv}",
                key_prefix="explorer_dd_conv",
                show_conversation=True,
            )
    else:
        st.info("conversation_id column not available")


def _render_quick_stats(df: pd.DataFrame):
    """Render quick data statistics."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    
    with col2:
        st.metric("Columns Available", f"{len(df.columns)}")
    
    with col3:
        if 'ai_processed' in df.columns:
            st.metric("AI Processed", f"{df['ai_processed'].sum():,}")
        else:
            st.metric("AI Processed", "N/A")


def _render_column_selector(df: pd.DataFrame) -> list:
    """Render column group selector and return selected columns."""
    st.subheader("📋 Select Column Groups")
    
    # Use predefined column groups from settings
    column_groups = COLUMN_GROUPS
    
    selected_groups = st.multiselect(
        "Select column groups",
        list(column_groups.keys()),
        default=["Basic Info", "AI Classification"]
    )
    
    # Build selected columns
    selected_cols = []
    for group in selected_groups:
        selected_cols.extend([c for c in column_groups.get(group, []) if c in df.columns])
    
    # Remove duplicates while preserving order
    selected_cols = list(dict.fromkeys(selected_cols))
    
    # Additional custom columns
    all_cols = df.columns.tolist()
    remaining_cols = [c for c in all_cols if c not in selected_cols]
    
    additional_cols = st.multiselect(
        "Add more columns",
        remaining_cols
    )
    
    final_cols = selected_cols + additional_cols
    
    return final_cols


def _render_search_filter(df: pd.DataFrame, final_cols: list) -> pd.DataFrame:
    """Render search and filter options, return filtered DataFrame."""
    col1, col2 = st.columns(2)
    
    with col1:
        search = st.text_input("🔎 Search by Conversation ID")
    
    with col2:
        if 'ai_processed' in df.columns:
            filter_processed = st.selectbox("AI Processing Status", ["All", "Processed Only", "Failed Only"])
        else:
            filter_processed = "All"
    
    # Apply filters
    display_df = df[final_cols].copy() if final_cols else df.copy()
    
    if search and 'conversation_id' in display_df.columns:
        display_df = display_df[display_df['conversation_id'].str.contains(search, na=False)]
    
    if filter_processed == "Processed Only" and 'ai_processed' in df.columns:
        display_df = display_df[df['ai_processed'] == True]
    elif filter_processed == "Failed Only" and 'ai_processed' in df.columns:
        display_df = display_df[df['ai_processed'] == False]
    
    return display_df


def _render_data_preview(display_df: pd.DataFrame):
    """Render data preview table."""
    max_preview = 500
    st.subheader(f"📊 Data Preview ({min(max_preview, len(display_df))} of {len(display_df)} records)")
    
    st.dataframe(
        display_df.head(max_preview),
        use_container_width=True,
        height=500
    )


def _render_column_stats(df: pd.DataFrame, final_cols: list):
    """Render column statistics section."""
    st.subheader("📈 Column Statistics")
    
    all_cols = df.columns.tolist()
    available_cols = final_cols if final_cols else all_cols
    
    stats_col = st.selectbox("Select column for statistics", available_cols)
    
    if not stats_col:
        st.info("Select a column to view statistics")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Statistics for `{stats_col}`**")
        col_data = df[stats_col]
        
        if col_data.dtype in ['int64', 'float64']:
            st.write(col_data.describe())
        else:
            st.write(f"- **Unique values:** {col_data.nunique()}")
            st.write(f"- **Missing:** {col_data.isna().sum()} ({col_data.isna().mean()*100:.1f}%)")
            mode_val = col_data.mode().iloc[0] if not col_data.mode().empty else 'N/A'
            st.write(f"- **Most common:** {mode_val}")
    
    with col2:
        st.markdown("**Value Distribution**")
        col_data = df[stats_col]
        
        if col_data.dtype in ['int64', 'float64']:
            fig = px.histogram(
                col_data.dropna(), 
                nbins=20, 
                color_discrete_sequence=['#667eea']
            )
        else:
            value_counts = col_data.value_counts().head(10)
            fig = px.bar(
                x=value_counts.index, 
                y=value_counts.values, 
                color_discrete_sequence=['#667eea']
            )
        
        fig.update_layout(**create_chart_layout())
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True, key='explorer_dist_chart')
