# -*- coding: utf-8 -*-
"""
Tab Sentiment - Dashboard v6.0
===============================
Sentiment analysis, trust levels, behavioral signals.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import safe_float, safe_percentage
from utils.charts import create_chart_layout
from components.drill_down import render_drill_section


def render(df: pd.DataFrame):
    """
    Render Sentiment & Signals tab.
    
    Args:
        df: Filtered DataFrame
    """
    st.header("💬 Sentiment & Signal Analysis")
    st.caption("Understanding customer emotions and behavioral signals")
    
    # KPI Row
    _render_kpis(df)
    
    st.divider()
    
    # Charts Row 1
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_sentiment_distribution(df)
    
    with col_right:
        _render_sentiment_trend(df)
    
    st.divider()
    
    # Behavioral Signals
    _render_behavioral_signals(df)
    
    # Politeness
    _render_politeness(df)

    # ── Interactive Drill-Down ──────────────────────
    render_drill_section(df, [
        ("sentiment_overall",    "Sentiment",      "💬"),
        ("trust_level",          "Trust Level",    "🤝"),
        ("decision_making_style","Decision Style", "🧠"),
        ("urgency_level",        "Urgency",        "⚡"),
    ], key_prefix="sent")


def _render_kpis(df: pd.DataFrame):
    """Render sentiment KPIs."""
    col1, col2, col3, col4 = st.columns(4)
    total = len(df)
    
    with col1:
        if 'sentiment_overall' in df.columns:
            positive = (df['sentiment_overall'] == 'positive').sum()
            st.metric("😊 Positive", f"{positive:,}",
                      delta=f"{safe_percentage(positive, total):.1f}%",
                      delta_color="normal")
        else:
            st.metric("Positive", "N/A")

    with col2:
        if 'sentiment_overall' in df.columns:
            neutral = (df['sentiment_overall'] == 'neutral').sum()
            st.metric("😐 Neutral", f"{neutral:,}",
                      delta=f"{safe_percentage(neutral, total):.1f}%",
                      delta_color="off")
        else:
            st.metric("Neutral", "N/A")

    with col3:
        if 'sentiment_overall' in df.columns:
            negative = (df['sentiment_overall'] == 'negative').sum()
            st.metric("😞 Negative", f"{negative:,}",
                      delta=f"{safe_percentage(negative, total):.1f}%",
                      delta_color="inverse")
        else:
            st.metric("Negative", "N/A")
    
    with col4:
        if 'sentiment_delta' in df.columns:
            avg_delta = safe_float(df['sentiment_delta'].mean())
            st.metric("📈 Avg Sentiment Δ", f"{avg_delta:+.2f}")
        else:
            st.metric("Sentiment Δ", "N/A")


def _render_sentiment_distribution(df: pd.DataFrame):
    """Render sentiment distribution pie chart."""
    st.subheader("🎭 Sentiment Distribution")
    
    if 'sentiment_overall' not in df.columns:
        st.info("Sentiment column not found")
        return
    
    sentiment_counts = df['sentiment_overall'].value_counts()
    
    if sentiment_counts.empty:
        st.info("No sentiment data")
        return
    
    colors = {'positive': '#2ecc71', 'neutral': '#f1c40f', 'negative': '#e74c3c'}
    
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        hole=0.5,
        color=sentiment_counts.index,
        color_discrete_map=colors
    )
    fig.update_layout(**create_chart_layout())
    st.plotly_chart(fig, use_container_width=True, key='sent_dist_pie')


def _render_sentiment_trend(df: pd.DataFrame):
    """Render sentiment trend over time."""
    st.subheader("📈 Sentiment Trend Over Time")
    
    if 'conversation_date' not in df.columns or 'sentiment_score' not in df.columns:
        st.info("Sentiment score or date column not found")
        return
    
    sentiment_numeric = pd.to_numeric(df['sentiment_score'], errors='coerce')
    daily_sentiment = sentiment_numeric.groupby(df['conversation_date'].dt.date).mean().reset_index()
    daily_sentiment.columns = ['Date', 'Avg Sentiment']
    
    if daily_sentiment.empty:
        st.info("Not enough data for trend")
        return
    
    fig = px.line(
        daily_sentiment,
        x='Date',
        y='Avg Sentiment',
        markers=True,
        color_discrete_sequence=['#00f5d4']
    )
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
    fig.update_layout(**create_chart_layout())
    st.plotly_chart(fig, use_container_width=True, key='sent_trend_line')


def _render_behavioral_signals(df: pd.DataFrame):
    """Render behavioral signals section."""
    st.subheader("🔍 Behavioral Signals")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        _render_trust_level(df)
    
    with col2:
        _render_price_sensitivity(df)
    
    with col3:
        _render_decision_style(df)


def _render_trust_level(df: pd.DataFrame):
    """Render trust level chart."""
    st.markdown("**🤝 Trust Level**")
    
    if 'trust_level' not in df.columns:
        st.info("Trust level column not found")
        return
    
    trust_data = df['trust_level'].dropna()
    trust_data = trust_data[~trust_data.isin(['unknown', 'Unknown', '', 'none', 'None'])]
    
    if trust_data.empty:
        st.info("No trust data (all unknown)")
        st.caption("💡 AI enrichment needed")
        return
    
    trust_counts = trust_data.value_counts()
    trust_colors = {
        'high': '#2ecc71', 'medium': '#f39c12', 'low': '#e74c3c',
        'very_high': '#27ae60', 'very_low': '#c0392b'
    }
    
    fig = px.pie(
        values=trust_counts.values,
        names=trust_counts.index,
        hole=0.6,
        color=trust_counts.index,
        color_discrete_map=trust_colors
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(height=250)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True, key='sent_trust_pie')
    
    # Trust insight
    high_trust = trust_counts.get('high', 0) + trust_counts.get('very_high', 0)
    high_trust_pct = (high_trust / len(trust_data)) * 100 if len(trust_data) > 0 else 0
    st.caption(f"✅ High trust customers: **{high_trust_pct:.1f}%**")


def _render_price_sensitivity(df: pd.DataFrame):
    """Render price sensitivity chart."""
    st.markdown("**💰 Price Sensitivity**")
    
    if 'price_sensitivity' not in df.columns:
        st.info("Price sensitivity not found")
        return
    
    price_data = df['price_sensitivity'].dropna()
    price_data = price_data[~price_data.isin(['unknown', 'Unknown', '', 'none', 'None'])]
    
    if price_data.empty:
        st.info("No sensitivity data")
        st.caption("💡 Check AI enrichment")
        return
    
    price_counts = price_data.value_counts()
    sensitivity_colors = {
        'high': '#e74c3c', 'medium': '#f39c12', 'low': '#2ecc71',
        'very_high': '#c0392b', 'budget_conscious': '#e67e22', 
        'value_seeker': '#3498db', 'premium': '#9b59b6'
    }
    
    fig = px.pie(
        values=price_counts.values,
        names=price_counts.index,
        hole=0.6,
        color=price_counts.index,
        color_discrete_map=sensitivity_colors
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(height=250)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True, key='sent_price_pie')
    
    # Sensitivity insight
    high_sens = sum(price_counts.get(k, 0) for k in ['high', 'very_high', 'budget_conscious'])
    high_sens_pct = (high_sens / len(price_data)) * 100 if len(price_data) > 0 else 0
    if high_sens_pct > 40:
        st.caption(f"⚠️ **{high_sens_pct:.1f}%** highly price sensitive - consider promotions")
    else:
        st.caption(f"💎 Price sensitivity: **{high_sens_pct:.1f}%** high")


def _render_decision_style(df: pd.DataFrame):
    """Render decision making style chart."""
    st.markdown("**🧠 Decision Style**")
    
    if 'decision_making_style' not in df.columns:
        st.info("Decision style not found")
        return
    
    decision_data = df['decision_making_style'].dropna()
    decision_data = decision_data[~decision_data.isin(['unknown', 'Unknown', '', 'none', 'None'])]
    
    if decision_data.empty:
        st.info("No decision style data")
        return
    
    decision_counts = decision_data.value_counts()
    style_colors = {
        'analytical': '#3498db', 'impulsive': '#e74c3c', 
        'deliberate': '#9b59b6', 'consensus': '#2ecc71',
        'emotional': '#e91e63', 'logical': '#00bcd4'
    }
    
    fig = px.pie(
        values=decision_counts.values,
        names=decision_counts.index,
        hole=0.6,
        color=decision_counts.index,
        color_discrete_map=style_colors
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(height=250)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True, key='sent_decision_pie')
    
    # Decision insight
    top_style = decision_counts.index[0]
    top_pct = (decision_counts.iloc[0] / len(decision_data)) * 100
    style_tips = {
        'analytical': 'Provide detailed specs & comparisons',
        'impulsive': 'Limited offers work well',
        'deliberate': 'Give time, follow-up reminders',
        'emotional': 'Focus on feelings & benefits'
    }
    tip = style_tips.get(top_style.lower(), 'Tailor approach accordingly')
    st.caption(f"🎯 Top: **{top_style}** ({top_pct:.0f}%)")
    st.caption(f"💡 {tip}")


def _render_politeness(df: pd.DataFrame):
    """Render politeness score distribution."""
    if 'politeness_score' not in df.columns:
        return
    
    st.subheader("🎩 Politeness Score Distribution")
    politeness_data = df['politeness_score'].dropna()
    
    if politeness_data.empty:
        st.info("No politeness data")
        return
    
    fig = px.histogram(
        politeness_data,
        nbins=10,
        color_discrete_sequence=['#00f5d4']
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(xaxis_title="Politeness Score (1-10)", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True, key='sent_politeness_hist')
