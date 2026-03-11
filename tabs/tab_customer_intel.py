# -*- coding: utf-8 -*-
"""
Tab Customer Intelligence - Dashboard v6.0
===========================================
DISC profiles, Generation cohorts, Lifestyle analysis.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import safe_float
from utils.charts import create_chart_layout, CHART_COLORS
from utils.ai_insights import render_insight_box
from components.drill_down import render_drill_section


def render(df: pd.DataFrame):
    """
    Render Customer Intelligence tab.
    
    Args:
        df: Filtered DataFrame
    """
    st.header("🧠 Customer Intelligence")
    st.caption("Deep understanding of customer profiles and behaviors")
    
    # KPI Row
    _render_kpis(df)
    
    st.divider()
    
    # Charts Row 1
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_disc_distribution(df)
    
    with col_right:
        _render_generation_cohort(df)
    
    # Charts Row 2
    col_left2, col_right2 = st.columns(2)
    
    with col_left2:
        _render_lifestyle_segments(df)
    
    with col_right2:
        _render_usage_context(df)
    
    st.divider()
    
    # DISC × Intent Matrix
    _render_disc_intent_matrix(df)

    # ── Interactive Drill-Down ──────────────────────
    render_drill_section(df, [
        ("disc_primary",       "DISC Type",        "🎭"),
        ("generation_cohort",  "Generation",       "👥"),
        ("lifestyle_segment",  "Lifestyle Segment","🎯"),
        ("decision_making_style", "Decision Style", "🧠"),
    ], key_prefix="intel")


def _render_kpis(df: pd.DataFrame):
    """Render KPI metrics row."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'disc_primary' in df.columns:
            dominant_disc = df['disc_primary'].mode().iloc[0] if not df['disc_primary'].mode().empty else "N/A"
            st.metric("Dominant DISC", dominant_disc)
        else:
            st.metric("Dominant DISC", "N/A")
    
    with col2:
        if 'generation_cohort' in df.columns:
            dominant_gen = df['generation_cohort'].mode().iloc[0] if not df['generation_cohort'].mode().empty else "N/A"
            st.metric("Primary Generation", dominant_gen)
        else:
            st.metric("Primary Gen", "N/A")
    
    with col3:
        if 'price_sensitivity' in df.columns:
            high_sensitivity = safe_float((df['price_sensitivity'] == 'high').mean()) * 100
            st.metric("Price Sensitive", f"{high_sensitivity:.1f}%")
        else:
            st.metric("Price Sensitive", "N/A")
    
    with col4:
        if 'likely_to_return' in df.columns:
            return_rate = (
                df['likely_to_return']
                .astype(str).str.lower()
                .isin(['true', '1', 'yes', 'có', 'co'])
                .mean() * 100
            )
            st.metric("Likely to Return", f"{return_rate:.1f}%")
        else:
            st.metric("Return Rate", "N/A")


def _render_disc_distribution(df: pd.DataFrame):
    """Render DISC profile distribution pie chart."""
    st.subheader("🎭 DISC Profile Distribution")
    
    if 'disc_primary' not in df.columns:
        st.info("DISC column not found")
        return
    
    disc_counts = df['disc_primary'].value_counts()
    
    if disc_counts.empty:
        st.info("No DISC data")
        return
    
    colors = {
        'D': '#e74c3c', 
        'I': '#f1c40f', 
        'S': '#2ecc71', 
        'C': '#3498db', 
        'unknown': '#95a5a6'
    }
    
    fig = px.pie(
        values=disc_counts.values,
        names=disc_counts.index,
        hole=0.4,
        color=disc_counts.index,
        color_discrete_map=colors
    )
    fig.update_layout(**create_chart_layout())
    st.plotly_chart(fig, use_container_width=True, key='intel_disc_pie')
    _total_disc = int(disc_counts.sum())
    render_insight_box('intel_disc_pie', {
        "dominant_type": str(disc_counts.index[0]),
        "dominant_pct": round(int(disc_counts.iloc[0]) / _total_disc * 100, 1),
        "disc_distribution": {str(k): int(v) for k, v in disc_counts.items()},
        "total": _total_disc,
    })

    # DISC Legend
    st.markdown("""
    **DISC Profiles:**
    - **D (Dominance):** Direct, results-oriented
    - **I (Influence):** Enthusiastic, collaborative  
    - **S (Steadiness):** Patient, reliable
    - **C (Compliance):** Analytical, detail-oriented
    """)


def _render_generation_cohort(df: pd.DataFrame):
    """Render generation cohort bar chart."""
    st.subheader("👥 Generation Cohort")
    
    if 'generation_cohort' not in df.columns:
        st.info("Generation column not found")
        return
    
    gen_counts = df['generation_cohort'].value_counts()
    
    if gen_counts.empty:
        st.info("No generation data")
        return
    
    fig = px.bar(
        x=gen_counts.index,
        y=gen_counts.values,
        color=gen_counts.values,
        color_continuous_scale='Plasma'
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(xaxis_title="Generation", yaxis_title="Count", showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key='intel_gen_bar')
    _total_gen = int(gen_counts.sum())
    render_insight_box('intel_gen_bar', {
        "dominant_generation": str(gen_counts.index[0]),
        "dominant_pct": round(int(gen_counts.iloc[0]) / _total_gen * 100, 1),
        "generation_distribution": {str(k): int(v) for k, v in gen_counts.items()},
        "total": _total_gen,
    })


def _render_lifestyle_segments(df: pd.DataFrame):
    """Render lifestyle segments treemap."""
    st.subheader("🎯 Lifestyle Segments")
    
    if 'lifestyle_segment' not in df.columns:
        st.info("Lifestyle column not found")
        return
    
    lifestyle_counts = df['lifestyle_segment'].value_counts().head(10)
    
    if lifestyle_counts.empty:
        st.info("No lifestyle data")
        return
    
    fig = px.treemap(
        names=lifestyle_counts.index,
        parents=[""] * len(lifestyle_counts),
        values=lifestyle_counts.values,
        color=lifestyle_counts.values,
        color_continuous_scale='Tealgrn'
    )
    fig.update_layout(**create_chart_layout())
    st.plotly_chart(fig, use_container_width=True, key='intel_lifestyle_tree')


def _render_usage_context(df: pd.DataFrame):
    """Render usage context bar chart."""
    st.subheader("🎁 Usage Context (Why They Buy)")
    
    if 'usage_context' not in df.columns:
        st.info("Usage context column not found")
        return
    
    context_counts = df['usage_context'].value_counts().head(8)
    
    if context_counts.empty:
        st.info("No usage context data")
        return
    
    fig = px.bar(
        y=context_counts.index,
        x=context_counts.values,
        orientation='h',
        color=context_counts.values,
        color_continuous_scale='Sunset'
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True, key='intel_usage_bar')


def _render_disc_intent_matrix(df: pd.DataFrame):
    """Render DISC vs Intent cross-tabulation matrix."""
    st.subheader("📊 DISC × Intent Matrix")
    
    if 'disc_primary' not in df.columns or 'intent_primary' not in df.columns:
        st.info("Required columns not found")
        return
    
    cross_tab = pd.crosstab(df['disc_primary'], df['intent_primary'])
    
    if cross_tab.empty:
        st.info("Not enough data for matrix")
        return
    
    fig = px.imshow(
        cross_tab,
        color_continuous_scale='Blues',
        aspect='auto',
        text_auto=True
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(xaxis_title="Intent", yaxis_title="DISC Profile")
    st.plotly_chart(fig, use_container_width=True, key='intel_disc_matrix')
    _stacked = cross_tab.stack().sort_values(ascending=False).head(6)
    render_insight_box('intel_disc_matrix', {
        "top_combinations": [
            {"disc": str(idx[0]), "intent": str(idx[1]), "count": int(v)}
            for idx, v in _stacked.items()
        ],
        "disc_types": [str(x) for x in cross_tab.index.tolist()],
        "intent_types": [str(x) for x in cross_tab.columns.tolist()],
        "total_conversations": int(cross_tab.values.sum()),
    })
