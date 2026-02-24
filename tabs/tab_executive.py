# -*- coding: utf-8 -*-
"""
Tab Executive - Dashboard v6.0
===============================
Executive Overview with KPIs and trends.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta
from utils.helpers import safe_float, safe_percentage, get_delta_indicator
from utils.charts import create_chart_layout
from components.drill_down import render_drill_section


def render(df: pd.DataFrame):
    """
    Render Executive Overview tab.
    
    Args:
        df: Filtered DataFrame
    """
    st.header("📈 Executive Dashboard")
    st.caption("Key Performance Indicators at a Glance")
    
    # Calculate period comparison
    current_period, previous_period = _calculate_periods(df)
    
    # KPI Row
    _render_kpis(df, current_period, previous_period)
    
    st.divider()
    
    # Charts Row 1
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_time_series(df)
    
    with col_right:
        _render_intent_pie(df)
    
    # Charts Row 2
    col_left2, col_right2 = st.columns(2)
    
    with col_left2:
        _render_hourly_heatmap(df)
    
    with col_right2:
        _render_funnel_breakdown(df)

    # ── Interactive Drill-Down ──────────────────────
    render_drill_section(df, [
        ("intent_primary",  "Intent chính",  "🎯"),
        ("funnel_type",     "Funnel Type",   "📦"),
        ("purchase_stage",  "Purchase Stage", "🛒"),
    ], key_prefix="exec")


def _calculate_periods(df: pd.DataFrame):
    """Calculate current and previous periods for comparison."""
    if 'conversation_date' not in df.columns:
        return df, pd.DataFrame()
    
    today = df['conversation_date'].max()
    if pd.isna(today):
        return df, pd.DataFrame()
    
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)
    
    current_period = df[df['conversation_date'] > week_ago]
    previous_period = df[
        (df['conversation_date'] > two_weeks_ago) & 
        (df['conversation_date'] <= week_ago)
    ]
    
    return current_period, previous_period


def _render_kpis(df: pd.DataFrame, current_period: pd.DataFrame, previous_period: pd.DataFrame):
    """Render KPI metrics row."""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        current_count = len(df)
        prev_count = len(previous_period) if not previous_period.empty else 0
        st.metric(
            "Total Conversations",
            f"{current_count:,}",
            delta=get_delta_indicator(len(current_period), prev_count) if prev_count > 0 else None
        )
    
    with col2:
        if 'funnel_is_successful' in df.columns:
            success_rate = safe_float(df['funnel_is_successful'].mean()) * 100
            prev_rate = safe_float(previous_period['funnel_is_successful'].mean()) * 100 if 'funnel_is_successful' in previous_period.columns and not previous_period.empty else 0
            st.metric(
                "Conversion Rate",
                f"{success_rate:.1f}%",
                delta=f"{success_rate - prev_rate:+.1f}pp" if prev_rate > 0 else None
            )
        else:
            st.metric("Conversion Rate", "N/A")
    
    with col3:
        if 'predicted_csat' in df.columns:
            avg_csat = safe_float(df['predicted_csat'].mean())
            prev_csat = safe_float(previous_period['predicted_csat'].mean()) if 'predicted_csat' in previous_period.columns and not previous_period.empty else 0
            st.metric(
                "Avg CSAT",
                f"{avg_csat:.2f}/10",
                delta=f"{avg_csat - prev_csat:+.2f}" if prev_csat > 0 else None
            )
        else:
            st.metric("Avg CSAT", "N/A")
    
    with col4:
        if 'ai_processed' in df.columns:
            ai_rate = safe_float(df['ai_processed'].mean()) * 100
            st.metric("AI Success Rate", f"{ai_rate:.1f}%")
        else:
            st.metric("AI Success", "N/A")
    
    with col5:
        if 'sentiment_overall' in df.columns:
            positive_rate = safe_float((df['sentiment_overall'] == 'positive').mean()) * 100
            st.metric("Positive Sentiment", f"{positive_rate:.1f}%")
        else:
            st.metric("Positive Rate", "N/A")


def _render_time_series(df: pd.DataFrame):
    """Render conversations over time chart."""
    st.subheader("📊 Conversations Over Time")
    
    if 'conversation_date' not in df.columns:
        st.info("Date column not found")
        return
    
    daily_counts = df.groupby(df['conversation_date'].dt.date).size().reset_index()
    daily_counts.columns = ['Date', 'Count']
    
    if daily_counts.empty:
        st.info("No time data available")
        return
    
    fig = px.area(
        daily_counts,
        x='Date',
        y='Count',
        color_discrete_sequence=['#667eea']
    )
    fig.update_layout(**create_chart_layout())
    fig.update_traces(fill='tozeroy', fillcolor='rgba(102, 126, 234, 0.3)')
    st.plotly_chart(fig, use_container_width=True, key='exec_time_series')


def _render_intent_pie(df: pd.DataFrame):
    """Render intent distribution pie chart."""
    st.subheader("🎯 Intent Distribution")
    
    if 'intent_primary' not in df.columns:
        st.info("Intent column not found")
        return
    
    intent_counts = df['intent_primary'].value_counts().head(8)
    
    if intent_counts.empty:
        st.info("No intent data")
        return
    
    fig = px.pie(
        values=intent_counts.values,
        names=intent_counts.index,
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(**create_chart_layout())
    fig.update_traces(textposition='outside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True, key='exec_intent_pie')


def _render_hourly_heatmap(df: pd.DataFrame):
    """Render hourly activity heatmap."""
    st.subheader("🕐 Hourly Activity Heatmap")
    
    if 'conversation_date' not in df.columns:
        st.info("Date column not found")
        return
    
    df_copy = df.copy()
    df_copy['hour'] = df_copy['conversation_date'].dt.hour
    df_copy['day_of_week'] = df_copy['conversation_date'].dt.day_name()
    
    heatmap_data = df_copy.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex([d for d in day_order if d in heatmap_data.index])
    
    if heatmap_data.empty:
        st.info("Not enough data for heatmap")
        return
    
    fig = px.imshow(
        heatmap_data,
        color_continuous_scale='Viridis',
        aspect='auto'
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(xaxis_title="Hour", yaxis_title="Day")
    st.plotly_chart(fig, use_container_width=True, key='exec_heatmap')


def _render_funnel_breakdown(df: pd.DataFrame):
    """Render funnel type breakdown chart."""
    st.subheader("📦 Funnel Type Breakdown")
    
    if 'funnel_type' not in df.columns:
        st.info("Funnel column not found")
        return
    
    funnel_counts = df['funnel_type'].value_counts()
    
    if funnel_counts.empty:
        st.info("No funnel data")
        return
    
    fig = px.bar(
        x=funnel_counts.values,
        y=funnel_counts.index,
        orientation='h',
        color=funnel_counts.values,
        color_continuous_scale='Tealgrn'
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True, key='exec_funnel')
