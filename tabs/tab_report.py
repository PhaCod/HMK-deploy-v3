# -*- coding: utf-8 -*-
"""
Tab Daily Reports — Hiển thị báo cáo Markdown từ 04_daily_report.py
=====================================================================
Đọc file HMK_Daily_Report_YYYY-MM-DD.md từ Google Drive
và render trực tiếp trên Streamlit với date picker.
"""
import re
import streamlit as st
import pandas as pd
from datetime import datetime


# ── Regex nhận diện frontmatter YAML ──────────────────────────────────────
_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Tách YAML frontmatter (--- ... ---) ra khỏi nội dung báo cáo.
    Trả về (meta_dict, body_text).
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip()

    body = text[m.end():]
    return meta, body


def _sort_key(report: dict) -> str:
    """Sort key: dùng date string YYYY-MM-DD (đảo ngược để newest first)."""
    return report.get('date', '0000-00-00')


def render(reports: list):
    """
    Render Daily Reports tab.

    Args:
        reports: List of dicts — [{'date': 'YYYY-MM-DD',
                                   'filename': str,
                                   'content': str}, ...]
                 Truyền danh sách rỗng [] nếu chưa có báo cáo.
    """
    st.header("📋 Daily Reports")
    st.caption("Báo cáo hằng ngày được tạo bởi AI (qwen2.5:7b) từ Gold data")

    # ── Empty state ──────────────────────────────────────────────────────────
    if not reports:
        _render_empty_state()
        return

    # ── Sort newest first ─────────────────────────────────────────────────────
    reports_sorted = sorted(reports, key=_sort_key, reverse=True)

    # ── Summary bar ───────────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Số báo cáo", len(reports_sorted))
    with col_b:
        st.metric("Mới nhất", reports_sorted[0]['date'])
    with col_c:
        st.metric("Cũ nhất", reports_sorted[-1]['date'])

    st.divider()

    # ── Date selector + Report viewer ─────────────────────────────────────────
    col_left, col_right = st.columns([1, 3])

    with col_left:
        st.subheader("📅 Chọn ngày")

        date_options = [r['date'] for r in reports_sorted]
        selected_date = st.selectbox(
            "Ngày báo cáo",
            options=date_options,
            index=0,
            label_visibility="collapsed",
            key="report_date_select"
        )

        # Find selected report
        selected = next((r for r in reports_sorted if r['date'] == selected_date), None)

        if selected:
            meta, _ = _parse_frontmatter(selected['content'])

            st.divider()
            st.caption("**Thông tin**")

            if meta.get('model'):
                st.caption(f"🤖 Model: `{meta['model']}`")
            if meta.get('total_conversations'):
                st.caption(f"💬 Conversations: **{meta['total_conversations']}**")
            if meta.get('generated_at'):
                st.caption(f"🕐 Tạo lúc: {meta['generated_at']}")

            st.divider()

            # Download button
            st.download_button(
                label="⬇️ Tải .md",
                data=selected['content'].encode('utf-8'),
                file_name=selected['filename'],
                mime="text/markdown",
                use_container_width=True,
                key=f"dl_{selected_date}"
            )

    with col_right:
        if selected:
            _, body = _parse_frontmatter(selected['content'])
            st.markdown(body, unsafe_allow_html=False)
        else:
            st.info("Không tìm thấy báo cáo cho ngày đã chọn.")


def _render_empty_state():
    """Hiện hướng dẫn khi chưa có báo cáo nào."""
    st.info("""
**Chưa có Daily Report nào.**

Để tạo báo cáo:
1. Chạy Gold pipeline (`03_gold_ai_enrichment.py`) trước
2. Chạy: `%run 04_daily_report.py` trên Colab (hoặc `auto_pipeline.py`)
3. Báo cáo sẽ lưu vào: `lakehouse/reports/daily/HMK_Daily_Report_YYYY-MM-DD.md`
4. Chia sẻ folder `reports/daily` lên Google Drive (Anyone with link)
5. Copy **Folder ID** vào Streamlit Secrets:

```toml
REPORT_FOLDER_ID = "your_folder_id_here"
```

Sau đó nhấn **🔄 Refresh** để tải báo cáo.
""")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Thử lại", key="report_retry"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.caption("Nhấn sau khi đã cấu hình Secrets")
