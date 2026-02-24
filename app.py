# -*- coding: utf-8 -*-
"""
Chat Analytics Dashboard v7.0 — Streamlit Cloud Edition
========================================================
Deploy: Streamlit Community Cloud (Free)
Data:   Google Drive → Gold Parquet files
AI:     Ollama qwen2.5:7b on Colab GPU

Usage:
    1. Push this folder to GitHub repo
    2. Connect repo to share.streamlit.io
    3. Set secrets: GOLD_FOLDER_ID, SILVER_FOLDER_ID
    4. Deploy!
"""
import streamlit as st
from datetime import datetime

# Internal imports
from config.settings import PAGE_CONFIG, TAB_NAMES, VERSION, APP_TITLE
from config.styles import apply_styles
from data.loader import load_all_data, get_data_status, refresh_data
from components.sidebar import render_sidebar
from tabs import (
    tab_executive,
    tab_customer_intel,
    tab_conversion,
    tab_sentiment,
    tab_agent,
    tab_revenue,
    tab_explorer
)


def main():
    """Main application entry point."""
    # Page Configuration
    st.set_page_config(**PAGE_CONFIG)

    # Apply Custom Styles
    apply_styles()

    # Load Data
    data_dict = load_all_data()
    df_gold = data_dict.get('ai_unified')

    if df_gold is None or df_gold.empty:
        _render_no_data_state()
        return

    # Render Sidebar (returns filtered df)
    filtered_df = render_sidebar(df_gold)

    # Main Content
    st.title(f"📊 {APP_TITLE}")

    # Render Data Status
    _render_data_status_bar(filtered_df, data_dict)

    # Create Tabs
    tabs = st.tabs(TAB_NAMES)

    # Render Each Tab
    with tabs[0]:
        tab_executive.render(filtered_df)

    with tabs[1]:
        tab_customer_intel.render(filtered_df)

    with tabs[2]:
        tab_conversion.render(filtered_df)

    with tabs[3]:
        tab_sentiment.render(filtered_df)

    with tabs[4]:
        tab_agent.render(filtered_df)

    with tabs[5]:
        tab_revenue.render(filtered_df)

    with tabs[6]:
        tab_explorer.render(filtered_df)

    # Footer
    _render_footer()


def _render_no_data_state():
    """Render empty state when no data is available."""
    st.error("⚠️ Chưa có dữ liệu")
    st.info("""
    **Để hiển thị dữ liệu, bạn cần:**
    1. Chạy pipeline trên Colab (Bronze → Silver → Gold)
    2. Chia sẻ folder Gold & Silver trên Google Drive (Anyone with link)
    3. Copy folder ID vào Streamlit Secrets

    **Cấu hình Secrets** (Settings → Secrets):
    ```toml
    GOLD_FOLDER_ID = "your_folder_id_here"
    SILVER_FOLDER_ID = "your_folder_id_here"
    ```
    """)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Thử lại"):
            refresh_data()
    with col2:
        st.caption("Nhấn sau khi cấu hình Secrets")


def _render_data_status_bar(df, data_dict):
    """Render data status indicator with quality info."""
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        if 'conversation_date' in df.columns:
            dates = df['conversation_date'].dropna()
            if len(dates) > 0:
                st.caption(f"📅 Data: {dates.min()} → {dates.max()}")
            else:
                st.caption("📅 Chưa có date")
        else:
            st.caption("📅 Date range unavailable")

    with col2:
        st.caption(f"📊 {len(df):,} records")

    with col3:
        ai_fields = ['intent_primary', 'sentiment_overall', 'disc_primary']
        processed_count = 0
        for col in ai_fields:
            if col in df.columns:
                processed_count = df[col].notna().sum()
                break
        processed_pct = (processed_count / len(df)) * 100 if len(df) > 0 else 0
        st.caption(f"🤖 AI: {processed_pct:.0f}%")

    with col4:
        if 'ai_quality_score' in df.columns:
            avg_score = df['ai_quality_score'].mean()
            st.caption(f"✅ Quality: {avg_score:.0f}/100")
        else:
            st.caption("✅ Quality: N/A")

    with col5:
        if st.button("🔄", help="Refresh data từ Google Drive"):
            refresh_data()


def _render_footer():
    """Render application footer."""
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.caption(f"📊 Dashboard v{VERSION}")

    with col2:
        st.caption(f"🕐 Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    with col3:
        st.caption("🤖 Powered by qwen2.5:7b on Colab GPU")


if __name__ == "__main__":
    main()
