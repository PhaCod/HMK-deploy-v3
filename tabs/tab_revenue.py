# -*- coding: utf-8 -*-
"""
Tab Revenue - Dashboard v6.0
=============================
Revenue metrics, conversion funnel, product interest.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import safe_float, safe_percentage
from utils.charts import create_chart_layout
from components.drill_down import render_drill_section


def render(df: pd.DataFrame):
    """
    Render Revenue Impact tab.
    
    Args:
        df: Filtered DataFrame
    """
    st.header("💰 Revenue Impact Analysis")
    st.caption("Track financial implications, conversion metrics, and revenue opportunities")
    
    # KPI Row 1
    _render_kpis_row1(df)
    
    st.divider()
    
    # KPI Row 2 (Optical-specific)
    _render_kpis_row2(df)
    
    st.divider()
    
    # Revenue Funnel
    _render_revenue_funnel(df)
    
    st.divider()
    
    # Product Interest & Urgency
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_product_interest(df)
    
    with col_right:
        _render_urgency_breakdown(df)
    
    st.divider()
    
    # Competitor Analysis
    _render_competitor_analysis(df)
    
    # Price Range
    _render_price_range(df)

    # ── Interactive Drill-Down ──────────────────────
    render_drill_section(df, [
        ("urgency_level",  "Urgency",         "⚡"),
        ("purchase_intent","Purchase Intent",  "🎯"),
        ("competitor_brand","Competitor Brand","🏆"),
        ("budget_range",   "Budget Range",     "💰"),
    ], key_prefix="rev")


def _render_kpis_row1(df: pd.DataFrame):
    """Render main revenue KPIs."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'conversion_probability' in df.columns:
            conv_data = pd.to_numeric(df['conversion_probability'], errors='coerce').dropna()
            if not conv_data.empty:
                avg_conv = conv_data.mean()
                high_conv = (conv_data >= 0.7).sum()
                st.metric("Avg Conversion Prob", f"{avg_conv:.0%}", 
                          delta=f"{high_conv:,} high-intent", delta_color="normal")
            else:
                st.metric("Conversion Probability", "N/A")
        elif 'price_mentioned' in df.columns:
            price_mentioned = df['price_mentioned'].sum() if df['price_mentioned'].dtype == bool else 0
            rate = safe_percentage(price_mentioned, len(df))
            st.metric("Price Discussed", f"{rate:.1f}%", delta=f"{price_mentioned:,} convos")
        else:
            st.metric("Price Discussed", "N/A")
    
    with col2:
        if 'purchase_intent' in df.columns:
            intent_data = df['purchase_intent'].dropna()
            intent_data = intent_data[~intent_data.isin(['unknown', 'Unknown', '', 'none'])]
            if not intent_data.empty:
                high_intent = intent_data.isin(['high', 'very_high', 'ready_to_buy']).sum()
                intent_rate = (high_intent / len(intent_data)) * 100 if len(intent_data) > 0 else 0
                st.metric("High Purchase Intent", f"{intent_rate:.1f}%", 
                          delta=f"{high_intent:,} customers", delta_color="normal")
            else:
                st.metric("Purchase Intent", "N/A")
        else:
            st.metric("Purchase Intent", "N/A")
    
    with col3:
        if 'urgency_level' in df.columns:
            urgency_data = df['urgency_level'].dropna()
            urgency_data = urgency_data[~urgency_data.isin(['unknown', 'Unknown', ''])]
            if not urgency_data.empty:
                high_urgency = urgency_data.isin(['high', 'urgent', 'immediate']).sum()
                urgency_rate = (high_urgency / len(urgency_data)) * 100 if len(urgency_data) > 0 else 0
                st.metric("🔥 High Urgency", f"{high_urgency:,}", 
                          delta=f"{urgency_rate:.1f}% of convos")
            else:
                st.metric("High Urgency", "N/A")
        else:
            st.metric("High Urgency", "N/A")
    
    with col4:
        if 'conversion_status' in df.columns:
            conv_status = df['conversion_status'].dropna()
            conv_status = conv_status[~conv_status.isin(['unknown', 'Unknown', ''])]
            if not conv_status.empty:
                converted = conv_status.isin(['converted', 'purchased', 'closed_won']).sum()
                conv_rate = (converted / len(conv_status)) * 100 if len(conv_status) > 0 else 0
                st.metric("✅ Conversion Rate", f"{conv_rate:.1f}%", 
                          delta=f"{converted:,} converted")
            else:
                st.metric("Conversion Rate", "N/A")
        else:
            st.metric("Conversion Rate", "N/A")


def _render_kpis_row2(df: pd.DataFrame):
    """Render optical-specific KPIs."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'budget_range' in df.columns:
            budget_data = df['budget_range'].dropna()
            budget_data = budget_data[~budget_data.isin(['unknown', 'Unknown', '', 'n/a'])]
            if not budget_data.empty:
                premium_keywords = ['high', 'premium', 'luxury', '>5tr', '>3tr']
                premium_count = sum(1 for b in budget_data if any(k in str(b).lower() for k in premium_keywords))
                premium_rate = (premium_count / len(budget_data)) * 100
                st.metric("💎 Premium Budget", f"{premium_rate:.1f}%", 
                          delta=f"{premium_count:,} customers")
            else:
                st.metric("Budget Data", "N/A")
        else:
            st.metric("Budget Range", "N/A - Enable AI enrichment")
    
    with col2:
        if 'has_prescription' in df.columns:
            rx_data = df['has_prescription'].dropna()
            rx_data = rx_data[~rx_data.isin(['unknown', 'Unknown', ''])]
            if not rx_data.empty:
                has_rx = rx_data.isin([True, 'true', 'yes', 'có', 1, '1']).sum()
                rx_rate = (has_rx / len(rx_data)) * 100 if len(rx_data) > 0 else 0
                st.metric("👓 Has Prescription", f"{rx_rate:.1f}%",
                          delta=f"{has_rx:,} customers", help="Customers with existing prescription")
            else:
                st.metric("Prescription", "N/A")
        else:
            st.metric("Prescription Data", "N/A")
    
    with col3:
        if 'optical_knowledge' in df.columns:
            opt_know = df['optical_knowledge'].dropna()
            opt_know = opt_know[~opt_know.isin(['unknown', 'Unknown', ''])]
            if not opt_know.empty:
                basic_count = opt_know.isin(['basic', 'none', 'low', 'beginner']).sum()
                needs_education = (basic_count / len(opt_know)) * 100 if len(opt_know) > 0 else 0
                st.metric("📚 Need Education", f"{needs_education:.1f}%",
                          delta=f"{basic_count:,} need guidance", 
                          help="Customers with basic optical knowledge - opportunity for consultative selling")
            else:
                st.metric("Optical Knowledge", "N/A")
        else:
            st.metric("Knowledge Level", "N/A")
    
    with col4:
        if 'agent_upsell_skill' in df.columns:
            upsell_data = pd.to_numeric(df['agent_upsell_skill'], errors='coerce').dropna()
            if not upsell_data.empty:
                avg_upsell = upsell_data.mean()
                good_upsellers = (upsell_data >= 7).sum()
                st.metric("📈 Upsell Skill", f"{avg_upsell:.1f}/10",
                          delta=f"{good_upsellers:,} skilled agents")
            else:
                st.metric("Upsell Skill", "N/A")
        else:
            st.metric("Upsell Tracking", "N/A")


def _render_revenue_funnel(df: pd.DataFrame):
    """Render revenue opportunity funnel."""
    st.subheader("🎯 Revenue Opportunity Funnel")
    
    # Build funnel stages
    funnel_stages = []
    total_convos = len(df)
    funnel_stages.append(("All Conversations", total_convos))
    
    if 'purchase_intent' in df.columns:
        intent_data = df['purchase_intent'].dropna()
        intent_data = intent_data[~intent_data.isin(['unknown', 'Unknown', '', 'none', 'no_intent'])]
        with_intent = len(intent_data)
        if with_intent > 0:
            funnel_stages.append(("Has Purchase Intent", with_intent))
        
        high_intent_count = df['purchase_intent'].isin(['high', 'very_high', 'ready_to_buy']).sum()
        if high_intent_count > 0:
            funnel_stages.append(("High Intent", high_intent_count))
    
    if 'conversion_probability' in df.columns:
        conv_prob = pd.to_numeric(df['conversion_probability'], errors='coerce').dropna()
        high_prob = (conv_prob >= 0.5).sum()
        if high_prob > 0:
            funnel_stages.append(("High Conv. Probability", high_prob))
    
    if 'conversion_status' in df.columns:
        converted_count = df['conversion_status'].isin(['converted', 'purchased', 'closed_won']).sum()
        if converted_count > 0:
            funnel_stages.append(("Converted", converted_count))
    
    if len(funnel_stages) < 2:
        st.info("📊 Enable AI enrichment with conversion tracking to see revenue funnel")
        return
    
    col_funnel, col_insights = st.columns([2, 1])
    
    with col_funnel:
        funnel_labels = [s[0] for s in funnel_stages]
        funnel_values = [s[1] for s in funnel_stages]
        
        fig = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_values,
            textposition="inside",
            textinfo="value+percent initial",
            marker=dict(
                color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6'][:len(funnel_stages)]
            ),
            connector=dict(line=dict(color="#a0a0a0", width=2))
        ))
        fig.update_layout(**create_chart_layout())
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True, key='rev_funnel')
    
    with col_insights:
        st.markdown("**📊 Funnel Insights:**")
        
        for i in range(len(funnel_stages) - 1):
            stage_name, stage_count = funnel_stages[i]
            next_name, next_count = funnel_stages[i + 1]
            if stage_count > 0:
                retention = (next_count / stage_count) * 100
                drop_off = 100 - retention
                
                if drop_off > 50:
                    st.error(f"🔴 {stage_name} → {next_name}: {drop_off:.0f}% drop")
                elif drop_off > 30:
                    st.warning(f"🟡 {stage_name} → {next_name}: {drop_off:.0f}% drop")
                else:
                    st.success(f"🟢 {stage_name} → {next_name}: {retention:.0f}% retained")
        
        initial = funnel_stages[0][1]
        final = funnel_stages[-1][1]
        if initial > 0:
            overall_rate = (final / initial) * 100
            st.metric("Overall Conversion", f"{overall_rate:.1f}%")


def _render_product_interest(df: pd.DataFrame):
    """Render product interest distribution."""
    st.subheader("🎯 Product Interest Distribution")
    
    product_cols = ['product_interest', 'vision_issue', 'usage_purpose']
    available_product_cols = [c for c in product_cols if c in df.columns]
    
    if not available_product_cols:
        st.info("Product interest columns not found in data")
        return
    
    all_products = []
    for col in available_product_cols:
        products = df[col].dropna()
        for val in products:
            if isinstance(val, (list, np.ndarray)):
                all_products.extend([str(v).strip() for v in val if v and str(v).strip()])
            elif val and str(val).strip() and str(val).lower() not in ['unknown', 'none', 'n/a']:
                all_products.append(str(val).strip())
    
    if not all_products:
        st.info("No product interest data - check AI enrichment")
        return
    
    product_series = pd.Series(all_products)
    product_counts = product_series.value_counts().head(10)
    
    fig = px.bar(
        y=product_counts.index,
        x=product_counts.values,
        orientation='h',
        color=product_counts.index,
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="Product/Vision Issue")
    st.plotly_chart(fig, use_container_width=True, key='rev_product_bar')
    
    top_product = product_counts.index[0]
    top_pct = (product_counts.iloc[0] / len(df)) * 100
    st.caption(f"🔥 Top interest: **{top_product}** ({top_pct:.1f}% of conversations)")


def _render_urgency_breakdown(df: pd.DataFrame):
    """Render urgency level breakdown."""
    st.subheader("⚡ Urgency Level Breakdown")
    
    if 'urgency_level' not in df.columns:
        st.info("Urgency column not found")
        return
    
    urgency_counts = df['urgency_level'].value_counts()
    
    if urgency_counts.empty:
        st.info("No urgency data")
        return
    
    colors = {'high': '#e74c3c', 'medium': '#f39c12', 'low': '#2ecc71'}
    
    fig = px.pie(
        values=urgency_counts.values,
        names=urgency_counts.index,
        hole=0.5,
        color=urgency_counts.index,
        color_discrete_map=colors
    )
    fig.update_layout(**create_chart_layout())
    st.plotly_chart(fig, use_container_width=True, key='rev_urgency_pie')


def _render_competitor_analysis(df: pd.DataFrame):
    """Render competitor analysis section."""
    st.subheader("🏆 Competitor Mentions")
    
    if 'competitor_brand' not in df.columns:
        st.info("Competitor column not found")
        return
    
    competitor_counts = df['competitor_brand'].dropna().value_counts().head(10)
    
    if competitor_counts.empty:
        st.info("No competitor data available")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.bar(
            x=competitor_counts.index,
            y=competitor_counts.values,
            color=competitor_counts.values,
            color_continuous_scale='Reds'
        )
        fig.update_layout(**create_chart_layout())
        fig.update_layout(showlegend=False, xaxis_title="Competitor", yaxis_title="Mentions")
        st.plotly_chart(fig, use_container_width=True, key='rev_competitor_bar')
    
    with col2:
        st.markdown("**Competitive Insights:**")
        top_competitor = competitor_counts.index[0]
        st.error(f"🎯 Top competitor: **{top_competitor}** ({competitor_counts.iloc[0]} mentions)")
        
        total_mentions = competitor_counts.sum()
        market_pressure = safe_percentage(total_mentions, len(df))
        st.metric("Market Pressure", f"{market_pressure:.1f}%")
        
        st.info("💡 **Tip:** Analyze what customers are saying about competitors to identify differentiation opportunities.")


def _render_price_range(df: pd.DataFrame):
    """Render price range distribution."""
    if 'price_range' not in df.columns:
        return
    
    st.divider()
    st.subheader("💵 Price Range Distribution")
    
    price_data = df['price_range'].dropna()
    
    if price_data.empty:
        st.info("No price data")
        return
    
    price_counts = price_data.value_counts().head(10)
    
    fig = px.bar(
        x=price_counts.index,
        y=price_counts.values,
        color=price_counts.values,
        color_continuous_scale='Greens'
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(showlegend=False, xaxis_title="Price Range", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True, key='rev_price_bar')
