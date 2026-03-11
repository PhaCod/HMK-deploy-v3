# -*- coding: utf-8 -*-
"""
Tab Conversion Funnel - Dashboard v6.0
=======================================
Purchase stage funnel, drop-off analysis, churn reasons.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import safe_float, safe_percentage
from utils.charts import create_chart_layout
from utils.ai_insights import render_insight_box
from components.drill_down import render_drill_section


def render(df: pd.DataFrame):
    """
    Render Conversion Funnel tab.
    
    Args:
        df: Filtered DataFrame
    """
    st.header("🔄 Conversion Funnel Analysis")
    st.caption("Track customer journey from awareness to purchase")
    
    # KPI Row
    _render_kpis(df)
    
    st.divider()
    
    # Main visualizations
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_purchase_funnel(df)
    
    with col_right:
        _render_dropoff_analysis(df)
    
    st.divider()
    
    # Churn Reasons
    _render_churn_reasons(df)

    # ── Interactive Drill-Down ──────────────────────
    render_drill_section(df, [
        ("purchase_stage",   "Purchase Stage", "📦"),
        ("churn_reason",     "Churn Reason",  "💔"),
        ("funnel_type",      "Funnel Type",   "🔄"),
        ("conversion_status","Conv. Status",  "✅"),
    ], key_prefix="conv")


def _render_kpis(df: pd.DataFrame):
    """Render KPI metrics row."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'funnel_is_successful' in df.columns:
            total_funnels = len(df)
            successful = int(
                df['funnel_is_successful'].map(
                    {True: 1, False: 0, 'True': 1, 'False': 0, 1: 1, 0: 0, '1': 1, '0': 0}
                ).fillna(0).sum()
            )
            conversion = safe_percentage(successful, total_funnels)
            st.metric("Overall Conversion", f"{conversion:.1f}%")
        else:
            st.metric("Conversion", "N/A")
    
    with col2:
        if 'funnel_steps_completed' in df.columns:
            try:
                import ast
                def _count_steps(x):
                    if pd.isna(x):
                        return 0
                    s = str(x).strip()
                    if s in ('', '[]', 'null', 'none', 'None'):
                        return 0
                    if s.startswith('['):
                        try:
                            return len(ast.literal_eval(s))
                        except Exception:
                            return 0
                    return 1
                steps_counts = df['funnel_steps_completed'].apply(_count_steps)
                avg_steps = safe_float(steps_counts.mean())
            except Exception:
                avg_steps = 0.0
            st.metric("Avg Steps Completed", f"{avg_steps:.1f}")
        else:
            st.metric("Avg Steps", "N/A")
    
    with col3:
        if 'funnel_drop_off_step' in df.columns:
            drop_offs = df['funnel_drop_off_step'].notna().sum()
            st.metric("Total Drop-offs", f"{drop_offs:,}")
        else:
            st.metric("Drop-offs", "N/A")
    
    with col4:
        if 'objections' in df.columns:
            objection_rate = safe_float(df['objections'].notna().mean()) * 100
            st.metric("Objection Rate", f"{objection_rate:.1f}%")
        else:
            st.metric("Objections", "N/A")


def _render_purchase_funnel(df: pd.DataFrame):
    """Render purchase stage funnel chart."""
    st.subheader("📉 Purchase Stage Funnel")
    
    if 'purchase_stage' not in df.columns:
        st.info("Purchase stage column not found")
        return
    
    stages = ['nhan_thuc', 'quan_tam', 'can_nhac', 'quyet_dinh', 'mua_hang']
    stage_labels = {
        'nhan_thuc': '1. Awareness',
        'quan_tam': '2. Interest', 
        'can_nhac': '3. Consideration',
        'quyet_dinh': '4. Decision',
        'mua_hang': '5. Purchase',
        'rot_don': 'Churned'
    }
    
    counts = df['purchase_stage'].value_counts()
    if counts.empty:
        st.info("No purchase stage data")
        return
    
    funnel_data = []
    funnel_labels = []
    for stage in stages:
        if stage in counts.index:
            funnel_data.append(counts[stage])
            funnel_labels.append(stage_labels.get(stage, stage))

    if not funnel_data:
        st.info("No funnel stages found")
        return

    # Sort by count descending so chart renders as a proper funnel (wide → narrow)
    sorted_pairs = sorted(zip(funnel_data, funnel_labels), reverse=True)
    funnel_data, funnel_labels = zip(*sorted_pairs)
    funnel_data = list(funnel_data)
    funnel_labels = list(funnel_labels)

    total_customers = funnel_data[0] if funnel_data else 1

    fig = go.Figure(go.Funnel(
        y=funnel_labels,
        x=funnel_data,
        texttemplate="%{value:,}<br>%{percentInitial:.1%}",
        textposition="inside",
        marker=dict(
            color=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'][:len(funnel_labels)]
        ),
        connector=dict(line=dict(color="rgba(255,255,255,0.3)", width=2))
    ))
    fig.update_layout(**create_chart_layout())
    fig.update_layout(funnelmode="stack", showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key='conv_funnel')
    render_insight_box('conv_funnel', {
        "stages": [
            {"label": l, "count": c,
             "pct_of_first": round(c / total_customers * 100, 1) if total_customers > 0 else 0}
            for l, c in zip(funnel_labels, funnel_data)
        ],
        "first_stage": funnel_labels[0] if funnel_labels else "",
        "last_stage": funnel_labels[-1] if funnel_labels else "",
        "conversion_pct": round(
            funnel_data[-1] / total_customers * 100, 1
        ) if funnel_data and total_customers > 0 else 0,
    })
    
    # Show actual stage breakdown
    st.markdown("**Actual customers at each stage:**")
    for label, count in zip(funnel_labels, funnel_data):
        pct = (count / total_customers) * 100
        st.caption(f"• {label}: {count:,} ({pct:.1f}%)")


def _render_dropoff_analysis(df: pd.DataFrame):
    """Render drop-off analysis chart."""
    st.subheader("🚫 Drop-off Analysis")
    
    dropoff_data = None
    
    # Try funnel_drop_off_step column first
    if 'funnel_drop_off_step' in df.columns:
        dropoff_data = df['funnel_drop_off_step'].dropna()
        dropoff_data = dropoff_data[~dropoff_data.isin(['unknown', 'Unknown', '', 'none', 'None', 'n/a'])]
    
    # Fallback: Calculate from purchase_stage
    if (dropoff_data is None or dropoff_data.empty) and 'purchase_stage' in df.columns:
        stage_counts = df['purchase_stage'].dropna().value_counts()
        # Map cả tên tiếng Anh lẫn tiếng Việt → label hiển thị
        funnel_order = [
            ('nhan_thuc',     'awareness',     'Nhận Thức'),
            ('quan_tam',      'interest',      'Quan Tâm'),
            ('can_nhac',      'consideration', 'Cân Nhắc'),
            ('quyet_dinh',    'decision',      'Quyết Định'),
            ('mua_hang',      'purchase',      'Mua Hàng'),
        ]
        ordered_counts = []

        for vi_key, en_key, label in funnel_order:
            for idx in stage_counts.index:
                idx_lower = str(idx).lower()
                if vi_key in idx_lower or en_key in idx_lower:
                    ordered_counts.append((label, stage_counts[idx]))
                    break
        
        if len(ordered_counts) >= 2:
            dropoff_dict = {}
            for i in range(len(ordered_counts) - 1):
                current_stage, current_count = ordered_counts[i]
                next_stage, next_count = ordered_counts[i + 1]
                drop_count = current_count - next_count
                if drop_count > 0:
                    dropoff_dict[f"{current_stage} → {next_stage}"] = drop_count
            
            if dropoff_dict:
                dropoff_data = pd.Series(dropoff_dict)
    
    if dropoff_data is None or dropoff_data.empty:
        st.info("📊 No drop-off data available")
        st.caption("Enable AI enrichment with funnel analysis to see drop-off patterns")
        return
    
    if isinstance(dropoff_data, pd.Series) and dropoff_data.name is None:
        dropoff_counts = dropoff_data.head(10)
    else:
        dropoff_counts = dropoff_data.value_counts().head(10)
    
    if dropoff_counts.empty:
        st.info("No drop-off patterns detected")
        return
    
    # Color code by severity
    max_val = dropoff_counts.max()
    colors = [f'rgba(231, 76, 60, {0.3 + 0.7 * (v/max_val)})' for v in dropoff_counts.values]
    
    fig = go.Figure(go.Bar(
        x=dropoff_counts.values,
        y=dropoff_counts.index,
        orientation='h',
        marker_color=colors,
        text=dropoff_counts.values,
        textposition='outside'
    ))
    fig.update_layout(**create_chart_layout())
    fig.update_layout(showlegend=False, xaxis_title="Drop-off Count", yaxis_title="Stage/Step")
    st.plotly_chart(fig, use_container_width=True, key='conv_dropoff')
    
    # Insights
    st.markdown("**📊 Drop-off Insights:**")
    total_conversations = len(df)
    total_dropoffs = dropoff_counts.sum()
    dropoff_rate = (total_dropoffs / total_conversations) * 100 if total_conversations > 0 else 0
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Total Drop-offs", f"{total_dropoffs:,}", 
                  delta=f"{dropoff_rate:.1f}% of convos", delta_color="inverse")
    with col_b:
        worst_step = dropoff_counts.index[0]
        worst_count = dropoff_counts.iloc[0]
        st.error(f"🔴 Biggest leak: **{worst_step}** ({worst_count:,})")
    
    # Actionable recommendation
    _render_dropoff_recommendation(str(worst_step))
    render_insight_box('conv_dropoff', {
        "total_conversations": int(total_conversations),
        "total_dropoffs": int(total_dropoffs),
        "dropoff_rate_pct": round(float(dropoff_rate), 1),
        "worst_step": str(worst_step),
        "worst_step_count": int(worst_count),
        "top_dropoffs": [
            {"step": str(s), "count": int(c)}
            for s, c in dropoff_counts.head(5).items()
        ],
    })


def _render_dropoff_recommendation(worst_step: str):
    """Render recommendation based on drop-off step."""
    worst_lower = worst_step.lower()
    
    if 'price' in worst_lower or 'cost' in worst_lower:
        st.info("💡 **Tip:** Consider payment plans or price anchoring")
    elif 'trust' in worst_lower:
        st.info("💡 **Tip:** Add testimonials, warranties, or social proof")
    elif 'stock' in worst_lower or 'availability' in worst_lower:
        st.info("💡 **Tip:** Improve inventory or offer alternatives")
    elif 'consideration' in worst_lower or 'decision' in worst_lower:
        st.info("💡 **Tip:** Improve product education & consultation")
    else:
        st.info(f"💡 **Tip:** Investigate why customers drop at '{worst_step}'")


def _render_churn_reasons(df: pd.DataFrame):
    """Render churn reasons chart."""
    st.subheader("💔 Top Churn Reasons")
    
    if 'churn_reason' not in df.columns:
        st.info("Churn reason column not found")
        return
    
    churn_counts = df['churn_reason'].dropna().value_counts().head(8)
    
    if churn_counts.empty:
        st.info("No churn reason data")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.bar(
            x=churn_counts.values,
            y=churn_counts.index,
            orientation='h',
            color=churn_counts.values,
            color_continuous_scale='OrRd'
        )
        fig.update_layout(**create_chart_layout())
        fig.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="Reason")
        st.plotly_chart(fig, use_container_width=True, key='conv_churn')
    
    with col2:
        st.markdown("**Actionable Insights:**")
        top_reason = churn_counts.index[0]
        st.warning(f"🔴 Top churn reason: **{top_reason}**")
        
        if 'price' in top_reason.lower():
            st.info("💡 Consider reviewing pricing strategy or offering payment plans")
        elif 'stock' in top_reason.lower():
            st.info("💡 Improve inventory management to reduce stockouts")
        elif 'trust' in top_reason.lower():
            st.info("💡 Focus on building trust through reviews and guarantees")

    render_insight_box('conv_churn', {
        "top_churn_reasons": [
            {"reason": str(r), "count": int(c),
             "pct": round(int(c) / int(churn_counts.sum()) * 100, 1)}
            for r, c in churn_counts.items()
        ],
        "total_churned": int(churn_counts.sum()),
        "top_reason": str(churn_counts.index[0]),
    })
