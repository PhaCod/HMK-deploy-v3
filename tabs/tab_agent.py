# -*- coding: utf-8 -*-
"""
Tab Agent Performance - Dashboard v6.0
=======================================
Agent skills, quality metrics, strengths/improvements.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.helpers import safe_float, safe_int, safe_percentage, parse_list_column
from utils.charts import create_chart_layout
from components.drill_down import render_drill_section


def render(df: pd.DataFrame):
    """
    Render Agent Performance tab.
    
    Args:
        df: Filtered DataFrame
    """
    st.header("👥 Agent Performance Dashboard")
    st.caption("Track team performance and identify coaching opportunities")
    
    # KPI Row
    _render_kpis(df)
    
    st.divider()
    
    # Charts Row 1
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_skills_radar(df)
    
    with col_right:
        _render_disc_matching(df)
    
    st.divider()
    
    # Quality Metrics
    _render_quality_metrics(df)
    
    # Strengths & Improvements
    _render_strengths_improvements(df)

    # ── Interactive Drill-Down ──────────────────────
    render_drill_section(df, [
        ("disc_primary",       "Customer DISC",  "🎭"),
        ("agent_overall_score","Agent Score Band","📊"),
        ("intent_primary",     "Intent",         "🎯"),
        ("urgency_level",      "Urgency",        "⚡"),
    ], key_prefix="agent")


def _render_kpis(df: pd.DataFrame):
    """Render agent KPIs."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'agent_overall_score' in df.columns:
            avg_score = safe_float(pd.to_numeric(df['agent_overall_score'], errors='coerce').mean())
            st.metric("Team Avg Score", f"{avg_score:.1f}/10")
        else:
            st.metric("Avg Score", "N/A")

    with col2:
        if 'empathy_score' in df.columns:
            avg_empathy = safe_float(pd.to_numeric(df['empathy_score'], errors='coerce').mean())
            st.metric("Avg Empathy", f"{avg_empathy:.1f}/10")
        else:
            st.metric("Empathy", "N/A")

    with col3:
        if 'dead_air_count' in df.columns:
            avg_dead_air = safe_float(pd.to_numeric(df['dead_air_count'], errors='coerce').mean())
            st.metric("Avg Dead Air", f"{avg_dead_air:.1f}")
        else:
            st.metric("Dead Air", "N/A")
    
    with col4:
        if 'agent_knowledge_gap' in df.columns:
            knowledge_gaps = df['agent_knowledge_gap'].notna().sum()
            st.metric("Knowledge Gaps", f"{knowledge_gaps:,}")
        else:
            st.metric("Knowledge Gaps", "N/A")


def _render_skills_radar(df: pd.DataFrame):
    """Render team skills radar chart."""
    st.subheader("📊 Skills Radar (Team Average)")
    
    skill_cols = {
        'agent_overall_score': 'Overall',
        'empathy_score': 'Empathy',
        'agent_response_speed': 'Response Speed',
        'agent_product_knowledge': 'Product Knowledge',
        'agent_communication': 'Communication',
        'agent_closing_skill': 'Closing Skill',
        'agent_empathy': 'Empathy (AI)'
    }
    
    available_skills = {k: v for k, v in skill_cols.items() if k in df.columns}
    
    if not available_skills:
        st.info("No agent skill columns found")
        return
    
    skill_avgs = {}
    for k, v in available_skills.items():
        numeric_col = pd.to_numeric(df[k], errors='coerce')
        if numeric_col.notna().any():
            skill_avgs[v] = safe_float(numeric_col.mean())
    
    if not skill_avgs:
        st.info("No skill scores available")
        return
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(skill_avgs.values()),
        theta=list(skill_avgs.keys()),
        fill='toself',
        fillcolor='rgba(102, 126, 234, 0.3)',
        line=dict(color='#667eea', width=2),
        name='Team Average'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10]),
            bgcolor='rgba(0,0,0,0)'
        ),
        **create_chart_layout()
    )
    st.plotly_chart(fig, use_container_width=True, key='agent_radar')


def _render_disc_matching(df: pd.DataFrame):
    """Render DISC profiles for agent matching."""
    st.subheader("🎯 Customer DISC Profiles (for Agent Matching)")
    
    if 'disc_primary' not in df.columns:
        st.info("DISC column not found")
        return
    
    disc_counts = df['disc_primary'].dropna().value_counts()
    
    if disc_counts.empty:
        st.info("No DISC data")
        return
    
    fig = px.pie(
        values=disc_counts.values,
        names=disc_counts.index,
        color_discrete_sequence=['#e74c3c', '#f1c40f', '#2ecc71', '#3498db']
    )
    fig.update_layout(**create_chart_layout())
    st.plotly_chart(fig, use_container_width=True, key='agent_disc_pie')
    
    st.markdown("""
    **Agent Matching Tips:**
    - **D customers** → Be direct, focus on results
    - **I customers** → Be enthusiastic, build rapport
    - **S customers** → Be patient, provide reassurance
    - **C customers** → Provide data and details
    """)


def _render_quality_metrics(df: pd.DataFrame):
    """Render quality metrics row."""
    st.subheader("🔧 Quality Metrics")
    q1, q2, q3, q4 = st.columns(4)
    
    with q1:
        if 'recovery_quality' in df.columns:
            excellent = safe_int((df['recovery_quality'] == 'excellent').sum())
            total_recovery = safe_int(df['recovery_quality'].notna().sum())
            rate = safe_percentage(excellent, total_recovery)
            st.metric("Excellent Recovery Rate", f"{rate:.1f}%")
        else:
            st.metric("Recovery Rate", "N/A")
    
    with q2:
        if 'agent_strengths' in df.columns:
            has_strengths = df['agent_strengths'].notna().sum()
            st.metric("Strengths Identified", f"{has_strengths:,}")
        else:
            st.metric("Strengths", "N/A")
    
    with q3:
        if 'agent_improvements' in df.columns:
            has_improvements = df['agent_improvements'].notna().sum()
            st.metric("Improvements Needed", f"{has_improvements:,}")
        else:
            st.metric("Improvements", "N/A")
    
    with q4:
        if 'sarcasm_flag' in df.columns:
            sarcasm_detected = int(
                df['sarcasm_flag'].astype(str).str.lower()
                .isin(['true', '1', 'yes']).sum()
            )
            st.metric("⚠️ Sarcasm Detected", f"{sarcasm_detected:,}")
        else:
            st.metric("Sarcasm", "N/A")


def _render_strengths_improvements(df: pd.DataFrame):
    """Render agent strengths and improvements section."""
    if 'agent_strengths' not in df.columns and 'agent_improvements' not in df.columns:
        return
    
    st.divider()
    st.subheader("🎯 Agent Performance Insights")
    col1, col2 = st.columns(2)
    
    with col1:
        _render_strengths(df)
    
    with col2:
        _render_improvements(df)


def _render_strengths(df: pd.DataFrame):
    """Render agent strengths chart."""
    st.markdown("### 💪 Common Strengths")
    
    if 'agent_strengths' not in df.columns:
        st.info("agent_strengths column not found")
        return
    
    strengths_series = parse_list_column(df['agent_strengths'])
    
    if strengths_series.empty or len(strengths_series) == 0:
        st.info("No strength data yet - AI enrichment will populate this")
        return
    
    strengths = strengths_series.value_counts().head(8)
    
    if len(strengths) == 0 or strengths.sum() == 0:
        st.info("No strength data yet - AI enrichment will populate this")
        return
    
    fig = px.bar(
        y=strengths.index.tolist(),
        x=strengths.values.tolist(),
        orientation='h',
        color=strengths.values.tolist(),
        color_continuous_scale='Greens'
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(
        height=300,
        showlegend=False,
        xaxis_title="Occurrences",
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True, key='agent_strengths_bar')
    
    # Insight
    top_strength = strengths.index[0]
    top_pct = (strengths.iloc[0] / len(strengths_series)) * 100
    st.caption(f"🏆 Top strength: **{top_strength}** ({top_pct:.1f}%)")


def _render_improvements(df: pd.DataFrame):
    """Render agent improvements chart."""
    st.markdown("### 📈 Areas for Improvement")
    
    if 'agent_improvements' not in df.columns:
        st.info("agent_improvements column not found")
        return
    
    improvements_series = parse_list_column(df['agent_improvements'])
    
    if improvements_series.empty or len(improvements_series) == 0:
        st.info("No improvement data yet - AI enrichment will populate this")
        return
    
    improvements = improvements_series.value_counts().head(8)
    
    if len(improvements) == 0 or improvements.sum() == 0:
        st.info("No improvement data yet - AI enrichment will populate this")
        return
    
    fig = px.bar(
        y=improvements.index.tolist(),
        x=improvements.values.tolist(),
        orientation='h',
        color=improvements.values.tolist(),
        color_continuous_scale='Reds'
    )
    fig.update_layout(**create_chart_layout())
    fig.update_layout(
        height=300,
        showlegend=False,
        xaxis_title="Occurrences",
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True, key='agent_improvements_bar')
    
    # Insight
    top_improvement = improvements.index[0]
    top_count = improvements.iloc[0]
    st.caption(f"⚠️ Priority focus: **{top_improvement}** ({top_count:,} cases)")
    
    # Training recommendation
    improvement_tips = {
        'cham_tra_loi': '💡 Focus on response time training',
        'thieu_kien_thuc_trong': '💡 Schedule product training sessions',
        'khong_upsell': '💡 Train on upselling techniques',
        'chua_chot_don': '💡 Practice closing techniques',
        'khong_giai_dap_thac_mac': '💡 Improve FAQ knowledge',
        'thieu_follow_up': '💡 Implement follow-up reminders'
    }
    if top_improvement in improvement_tips:
        st.info(improvement_tips[top_improvement])
