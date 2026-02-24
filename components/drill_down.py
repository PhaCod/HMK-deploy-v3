# -*- coding: utf-8 -*-
"""
Drill-Down Component v8.0 — Professional DA Redesign
=====================================================
Design principles:
  1. Progressive disclosure: context bar → conversation list → detail
  2. Conversation cards (radio list), không dùng ugly ID dropdown
  3. AI scorecard (4 blocks), không dùng flat bullet list dài
  4. Flat layout, không có tabs-within-tabs
  5. Filter sạch: loại bỏ True/False/UUID/nan khỏi selector
  6. Context-aware: KPI chips phù hợp theo segment đang xem
"""
import streamlit as st
import pandas as pd
import os
import glob
from typing import Any, List, Optional

from data.loader import SILVER_DIR
# ── Màu sắc nhất quán ──────────────────────────────────────────────────────
_SENTIMENT_COLOR = {"positive": "#00c896", "neutral": "#f5a623", "negative": "#ef476f"}
_URGENCY_COLOR   = {"high": "#ef476f",     "medium": "#f5a623",  "low": "#00c896"}
_TRUST_COLOR     = {"high": "#00c896", "very_high": "#00c896",
                    "medium": "#f5a623", "low": "#ef476f", "very_low": "#ef476f"}
_DISC_COLOR      = {"D": "#ef476f", "I": "#f5a623", "S": "#00c896", "C": "#4cc9f0"}

def _score_color(v) -> str:
    try:
        n = float(v)
        return "#00c896" if n >= 7 else ("#f5a623" if n >= 4 else "#ef476f")
    except Exception:
        return "#888"

def _pick_color(val, hi, lo) -> str:
    return "#00c896" if val >= hi else ("#f5a623" if val >= lo else "#ef476f")



# ============================================================
# PUBLIC: DRILL SECTION  (thay thế multi-selector pattern cũ)
# ============================================================
def render_drill_section(
    df: pd.DataFrame,
    segments: list,
    key_prefix: str = "ds",
):
    """
    Nhóm drill-down gọn: 2-level selector thay vì nhiều dropdown song song.

    segments = list of (column, label, icon) ví dụ:
        [("intent_primary", "Intent", "🎯"),
         ("funnel_type", "Funnel Type", "📦")]

    Luồng UX:
      ① Chọn dimension  (radio hoặc selectbox)
      ② Chọn giá trị   (chỉ hiện dropdown của dimension đang chọn)
      ③ Panel drill-down duy nhất xuất hiện
    """
    if not segments:
        return

    st.divider()

    # Lọc ra các segment có dữ liệu hợp lệ
    valid_segments = []
    _SKIP = {"unknown", "Unknown", "", "none", "None", "n/a", "null",
             "true", "false", "True", "False", "nan", "NaN"}
    for col, label, icon in segments:
        if col in df.columns:
            vals = df[col].dropna().astype(str)
            vals = vals[~vals.isin(_SKIP)].pipe(lambda s: s[s.str.len() < 60])
            if not vals.empty:
                valid_segments.append((col, label, icon))

    if not valid_segments:
        return

    st.markdown(
        "<div style='font-size:13px;font-weight:700;color:#aaa;"
        "text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px'>"
        "🔍 Drill into Conversations</div>",
        unsafe_allow_html=True,
    )

    # Nếu chỉ có 1 segment → bỏ bước chọn dimension
    if len(valid_segments) == 1:
        col, label, icon = valid_segments[0]
        sel_val = render_drill_selector(df, col, f"{icon} {label}", key_prefix)
        if sel_val:
            render_drill_down_panel(
                df, col, sel_val,
                title=f"{icon} {label}: {sel_val}",
                key_prefix=f"{key_prefix}_dd",
            )
        return

    # Nhiều segments: chọn dimension trước bằng selectbox nhỏ
    dim_opts = [f"{icon} {label}" for _, label, icon in valid_segments]
    sel_dim = st.selectbox(
        "Phân tích theo",
        dim_opts,
        key=f"{key_prefix}_dim",
        label_visibility="collapsed",
        format_func=lambda x: f"📌 Phân tích theo: {x}",
    )
    dim_idx = dim_opts.index(sel_dim)
    col, label, icon = valid_segments[dim_idx]

    # Value selector + panel (chỉ 1 panel active tại một thời điểm)
    sel_val = render_drill_selector(df, col, f"Chọn {label}", f"{key_prefix}_{col}")
    if sel_val:
        render_drill_down_panel(
            df, col, sel_val,
            title=f"{icon} {label}: {sel_val}",
            key_prefix=f"{key_prefix}_{col}_dd",
        )


# ============================================================
# PUBLIC: SELECTOR
# ============================================================
def render_drill_selector(
    df: pd.DataFrame,
    column: str,
    label: str = "🔍 Chọn segment",
    key_prefix: str = "drill",
    top_n: int = 15,
) -> Optional[str]:
    """
    Selectbox gọn. Lọc sạch giá trị xấu (boolean, UUID, unknown…).
    Trả về raw value hoặc None.
    """
    if column not in df.columns:
        return None

    _SKIP = {"unknown", "Unknown", "", "none", "None", "n/a", "null",
             "true", "false", "True", "False", "nan", "NaN"}

    values = (
        df[column].dropna().astype(str)
        .pipe(lambda s: s[~s.isin(_SKIP)])
        .pipe(lambda s: s[s.str.len() < 60])   # bỏ UUID/chuỗi quá dài
    )
    if values.empty:
        return None

    counts = values.value_counts().head(top_n)
    options = ["— Chọn để xem chi tiết —"] + [
        f"{v}  ({c:,})" for v, c in zip(counts.index, counts.values)
    ]

    selected = st.selectbox(label, options, key=f"{key_prefix}_{column}_sel")
    if selected and selected != "— Chọn để xem chi tiết —":
        return selected.split("  (")[0]
    return None



# ============================================================
# PUBLIC: MAIN PANEL  (3 tầng, không có tabs-within-tabs)
# ============================================================
def render_drill_down_panel(
    df: pd.DataFrame,
    filter_column: str,
    filter_value: Any,
    title: str = "",
    key_prefix: str = "ddp",
    show_conversation: bool = True,
    extra_columns: Optional[List[str]] = None,
):
    """
    Panel drill-down 3 tầng:
      Tầng 1 ─ Context bar  (breadcrumb + 4 KPI chip + nút export)
      Tầng 2 ─ Conversation list  (card dạng radio list, scrollable)
      Tầng 3 ─ Detail view  (metadata ribbon | chat bubbles | AI scorecard)
    """
    if filter_value is None:
        return

    filtered = df[df[filter_column].astype(str) == str(filter_value)].copy()
    if filtered.empty:
        st.warning(f"Không có dữ liệu cho **{filter_column}** = `{filter_value}`")
        return

    _render_context_bar(filtered, filter_column, filter_value, title, key_prefix)
    st.divider()

    col_list, col_detail = st.columns([2, 3], gap="large")

    with col_list:
        selected_idx = _render_conversation_list(filtered, key_prefix)

    with col_detail:
        if selected_idx is not None:
            _render_conversation_detail(filtered.iloc[selected_idx], key_prefix)
        else:
            st.markdown(
                """<div style="height:200px;display:flex;align-items:center;
                justify-content:center;color:#666;font-size:14px;">
                ← Chọn một cuộc hội thoại để xem chi tiết</div>""",
                unsafe_allow_html=True,
            )


# ============================================================
# TẦNG 1 — CONTEXT BAR
# ============================================================
def _render_context_bar(
    filtered: pd.DataFrame,
    filter_column: str,
    filter_value: Any,
    title: str,
    key_prefix: str,
):
    count = len(filtered)
    display_title = title or f"{filter_column}: {filter_value}"

    hdr_col, exp_col = st.columns([5, 1])
    with hdr_col:
        st.markdown(
            f"<h4 style='margin:0;color:#c0c0ff'>{display_title} "
            f"<span style='font-size:14px;color:#888;font-weight:normal'>"
            f"— {count:,} conversations</span></h4>",
            unsafe_allow_html=True,
        )
    with exp_col:
        cols_to_export = [c for c in filtered.columns if c != "full_conversation"]
        csv_data = filtered[cols_to_export].to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Export", csv_data, "drill_down.csv", "text/csv",
            key=f"{key_prefix}_export", use_container_width=True,
        )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_chip("Conversations", f"{count:,}", "#667eea")
    with k2:
        pct = _pct_positive_sentiment(filtered)
        _kpi_chip("Sentiment ➕", f"{pct:.0f}%", _pick_color(pct, 60, 40))
    with k3:
        conv = _conversion_rate(filtered)
        _kpi_chip("Conversion", f"{conv:.0f}%", _pick_color(conv, 50, 30))
    with k4:
        score = _avg_agent_score(filtered)
        _kpi_chip("Agent Score", f"{score:.1f}/10" if score else "N/A",
                  _score_color(score) if score else "#888")


def _kpi_chip(label: str, value: str, color: str):
    st.markdown(
        f"""<div style="background:rgba(255,255,255,0.05);border-left:3px solid {color};
        padding:8px 12px;border-radius:0 6px 6px 0;margin:4px 0;">
        <div style="font-size:11px;color:#888;text-transform:uppercase;
        letter-spacing:.5px">{label}</div>
        <div style="font-size:18px;font-weight:700;color:{color}">{value}</div>
        </div>""",
        unsafe_allow_html=True,
    )


# ============================================================
# TẦNG 2 — CONVERSATION LIST (card radio)
# ============================================================
def _render_conversation_list(filtered: pd.DataFrame, key_prefix: str) -> Optional[int]:
    """
    Danh sách conversation dạng card radio — scrollable.
    Mỗi card: icon sentiment · date · intent · số tin.
    Trả về index (0-based) của conversation được chọn.
    """
    MAX_SHOW = 150
    shown = filtered.head(MAX_SHOW)

    st.markdown(
        f"<div style='font-size:12px;color:#888;margin-bottom:8px'>"
        f"Hiển thị {min(len(filtered), MAX_SHOW):,} / {len(filtered):,}</div>",
        unsafe_allow_html=True,
    )

    options = []
    for _, row in shown.iterrows():
        date  = str(row.get("conversation_date", ""))[:10]
        intent = _shorten(str(row.get("intent_primary", "—")), 20)
        sent   = str(row.get("sentiment_overall", "")).lower()
        dot    = "🟢" if sent == "positive" else ("🔴" if sent == "negative" else "🟡")
        msgs   = row.get("message_count") or row.get("total_messages") or "?"
        options.append(f"{dot} {date}  ·  {intent}  ·  {msgs} msgs")

    if not options:
        st.warning("Không có conversation nào.")
        return None

    st.markdown(
        "<style>.stRadio > div{max-height:500px;overflow-y:auto;"
        "border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:4px}</style>",
        unsafe_allow_html=True,
    )
    chosen = st.radio(
        "Chọn conversation",
        options,
        index=0,
        key=f"{key_prefix}_conv_radio",
        label_visibility="collapsed",
    )
    return options.index(chosen)


# ============================================================
# TẦNG 3 — CONVERSATION DETAIL
# ============================================================
def _render_conversation_detail(row: pd.Series, key_prefix: str):
    """Metadata ribbon → chat bubbles + AI scorecard → raw expander."""
    _render_metadata_ribbon(row)
    st.markdown("<hr style='margin:8px 0;border-color:rgba(255,255,255,0.1)'>",
                unsafe_allow_html=True)

    chat_col, score_col = st.columns([3, 2], gap="medium")

    with chat_col:
        st.markdown("**💬 Nội dung hội thoại**")
        conv_text = str(row.get("full_conversation", ""))
        if not conv_text or conv_text in ("nan", "", "None"):
            conv_text = _lookup_conversation_from_silver(
                str(row.get("conversation_id", ""))
            )
        if conv_text and conv_text not in ("nan", "", "None"):
            _render_chat_bubbles(conv_text)
        else:
            st.info("Chưa có nội dung hội thoại trong lakehouse.")

    with score_col:
        st.markdown("**🤖 AI Scorecard**")
        _render_ai_scorecard(row)

    with st.expander("🔧 Raw JSON (debug)", expanded=False):
        raw = {k: str(v) for k, v in row.items()
               if pd.notna(v) and str(v).strip() not in ("", "nan")}
        st.json(raw)


def _render_metadata_ribbon(row: pd.Series):
    """Một hàng badge nhỏ thể hiện thông tin chính của conversation."""
    badges = []

    date = str(row.get("conversation_date", ""))[:10]
    if date and date != "nan":
        badges.append(("📅", date, "#555"))

    intent = str(row.get("intent_primary", ""))
    if intent and intent not in ("nan", "unknown"):
        badges.append(("🎯", intent, "#667eea"))

    sent = str(row.get("sentiment_overall", "")).lower()
    if sent in _SENTIMENT_COLOR:
        badges.append(("●", sent, _SENTIMENT_COLOR[sent]))

    disc = str(row.get("disc_primary", "")).upper()
    if disc and disc not in ("NAN", "UNKNOWN", ""):
        badges.append(("🧠", f"DISC-{disc}", _DISC_COLOR.get(disc, "#888")))

    urg = str(row.get("urgency_level", "")).lower()
    if urg in _URGENCY_COLOR:
        badges.append(("⚡", urg, _URGENCY_COLOR[urg]))

    funnel = str(row.get("funnel_type", ""))
    if funnel and funnel not in ("nan", "unknown"):
        badges.append(("🔄", funnel, "#764ba2"))

    html = " ".join(
        f"""<span style="background:rgba(255,255,255,0.07);border:1px solid {c};
        color:{c};border-radius:12px;padding:2px 10px;font-size:12px;
        font-weight:600;white-space:nowrap">{icon} {label}</span>"""
        for icon, label, c in badges
    )
    st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:6px'>{html}</div>",
                unsafe_allow_html=True)


# ============================================================
# AI SCORECARD — 4 blocks gọn thay vì bullet list dài
# ============================================================
def _render_ai_scorecard(row: pd.Series):
    """
    4 blocks trực quan:
      [Phân loại]  [Hồ sơ KH]
      [Agent KPI]  [Chuyển đổi]
    """
    # Block 1: Phân loại
    _scorecard_block("🎯 Phân loại", [
        ("Intent",    row.get("intent_primary"),  None),
        ("Stage",     row.get("purchase_stage"),  None),
        ("Funnel",    row.get("funnel_type"),      None),
        ("Urgency",   row.get("urgency_level"),
                      lambda v: _URGENCY_COLOR.get(str(v).lower(), "#888")),
    ])

    # Block 2: Hồ sơ khách hàng
    _scorecard_block("🧠 Khách hàng", [
        ("DISC",      row.get("disc_primary"),
                      lambda v: _DISC_COLOR.get(str(v).upper(), "#888")),
        ("Sentiment", row.get("sentiment_overall"),
                      lambda v: _SENTIMENT_COLOR.get(str(v).lower(), "#888")),
        ("Trust",     row.get("trust_level"),
                      lambda v: _TRUST_COLOR.get(str(v).lower(), "#888")),
        ("Giá nhạy",  row.get("price_sensitivity"),  None),
        ("Đối thủ",   row.get("competitor_brand"),    None),
    ])

    # Block 3: Agent KPIs
    agent_items = []
    for field, label in [
        ("agent_overall_score", "Tổng"),
        ("empathy_score",       "Đồng cảm"),
        ("agent_closing_skill", "Chốt sale"),
        ("agent_upsell_skill",  "Upsell"),
    ]:
        val = row.get(field)
        try:
            num = float(val)
            agent_items.append((label, f"{num:.0f}/10",
                                lambda v: _score_color(str(v).split("/")[0])))
        except (TypeError, ValueError):
            pass
    if agent_items:
        _scorecard_block("👤 Agent", agent_items)

    # Block 4: Chuyển đổi
    conv_ok = str(row.get("funnel_is_successful", "")).lower() in ("true", "1", "1.0")
    conv_items = [
        ("Chuyển đổi",
         "✅ Thành công" if conv_ok else "❌ Chưa chốt",
         lambda v: "#00c896" if "✅" in str(v) else "#ef476f"),
    ]
    try:
        p = float(row.get("conversion_probability", "x")) * 100
        conv_items.append(("Xác suất", f"{p:.0f}%",
                           lambda v: _pick_color(float(str(v).replace("%", "")), 60, 30)))
    except Exception:
        pass
    try:
        csat = float(row.get("predicted_csat", "x"))
        conv_items.append(("CSAT dự báo", f"{csat:.1f}/5",
                           lambda v: _score_color(float(str(v).split("/")[0]) * 2)))
    except Exception:
        pass
    churn = row.get("churn_reason")
    if churn and str(churn) not in ("nan", "None", "unknown"):
        conv_items.append(("Lý do bỏ", _shorten(str(churn), 30),
                           lambda v: "#f5a623"))
    _scorecard_block("💰 Chuyển đổi", conv_items)


def _scorecard_block(title: str, items: list):
    """
    Block scorecard 2-cột đơn giản.
    items = list of (label, value, color_fn | None)
    """
    valid = []
    for item in items:
        label, val, color_fn = item
        if val is None:
            continue
        if not isinstance(val, str) and pd.isna(val):
            continue
        val_str = str(val).strip()
        if val_str in ("", "nan", "unknown", "Unknown", "None", "null"):
            continue
        color = "#c0c0ff"
        if color_fn:
            try:
                color = color_fn(val_str)
            except Exception:
                pass
        valid.append((label, val_str, color))

    if not valid:
        return

    rows_html = "".join(
        f"""<tr>
          <td style="color:#888;font-size:11px;padding:3px 6px;white-space:nowrap">
            {lbl}</td>
          <td style="color:{clr};font-size:12px;font-weight:600;padding:3px 6px">
            {_shorten(v, 28)}</td>
        </tr>"""
        for lbl, v, clr in valid
    )

    st.markdown(
        f"""<div style="background:rgba(255,255,255,0.04);border-radius:8px;
        padding:8px 10px;margin-bottom:8px">
        <div style="font-size:11px;font-weight:700;color:#aaa;
        text-transform:uppercase;letter-spacing:.6px;margin-bottom:4px">{title}</div>
        <table style="width:100%;border-collapse:collapse">{rows_html}</table>
        </div>""",
        unsafe_allow_html=True,
    )


# ============================================================
# CHAT BUBBLES
# ============================================================
def _render_chat_bubbles(conv_text: str):
    """Render conversation dưới dạng chat bubbles trong scrollable container."""
    lines = [l.strip() for l in conv_text.split("\n") if l.strip()]

    bubbles = []
    for line in lines:
        if line.startswith("[CUSTOMER]"):
            msg = _html_escape(line[10:].strip())
            bubbles.append(
                f'<div style="display:flex;justify-content:flex-start;margin:4px 0">'
                f'<div style="max-width:82%;background:rgba(0,200,150,0.12);'
                f'border-radius:0 10px 10px 10px;padding:6px 10px;">'
                f'<div style="font-size:10px;color:#00c896;font-weight:700;'
                f'margin-bottom:2px">👤 KHÁCH</div>'
                f'<div style="font-size:13px;color:#ddd">{msg}</div></div></div>'
            )
        elif line.startswith("[ADMIN]"):
            msg = _html_escape(line[7:].strip())
            bubbles.append(
                f'<div style="display:flex;justify-content:flex-end;margin:4px 0">'
                f'<div style="max-width:82%;background:rgba(102,126,234,0.15);'
                f'border-radius:10px 0 10px 10px;padding:6px 10px;">'
                f'<div style="font-size:10px;color:#667eea;font-weight:700;'
                f'text-align:right;margin-bottom:2px">ADMIN 💼</div>'
                f'<div style="font-size:13px;color:#ddd;text-align:right">{msg}</div>'
                f'</div></div>'
            )
        else:
            msg = _html_escape(line)
            bubbles.append(
                f'<div style="font-size:11px;color:#666;text-align:center;'
                f'margin:2px 0">{msg}</div>'
            )

    st.markdown(
        f'<div style="max-height:420px;overflow-y:auto;padding:8px;'
        f'border:1px solid rgba(255,255,255,0.07);border-radius:8px">'
        + "".join(bubbles)
        + '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# SILVER FALLBACK
# ============================================================
@st.cache_data(ttl=300)
def _load_silver_conversations() -> pd.DataFrame:
    """Load Silver conversations (cached 5 min) để fallback full_conversation."""
    silver_conv_path = SILVER_DIR
    try:
        if os.path.exists(silver_conv_path):
            from deltalake import DeltaTable
            dt = DeltaTable(silver_conv_path)
            return dt.to_pandas(columns=["conversation_id", "full_conversation"])
    except Exception:
        pass
    pattern = os.path.join(silver_conv_path, "**", "*.parquet")
    files = [f for f in glob.glob(pattern, recursive=True) if "_delta_log" not in f]
    if files:
        try:
            return pd.concat(
                [pd.read_parquet(f, columns=["conversation_id", "full_conversation"])
                 for f in files],
                ignore_index=True,
            )
        except Exception:
            pass
    return pd.DataFrame()


def _lookup_conversation_from_silver(conversation_id: str) -> str:
    if not conversation_id:
        return ""
    try:
        sdf = _load_silver_conversations()
        if sdf.empty:
            return ""
        match = sdf[sdf["conversation_id"] == conversation_id]
        if not match.empty:
            text = str(match.iloc[0]["full_conversation"])
            if text not in ("nan", "None", ""):
                return text
    except Exception:
        pass
    return ""


# ============================================================
# HELPERS
# ============================================================
def _shorten(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


def _html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _pct_positive_sentiment(df: pd.DataFrame) -> float:
    if "sentiment_overall" not in df.columns:
        return 0.0
    return (df["sentiment_overall"].astype(str) == "positive").mean() * 100


def _conversion_rate(df: pd.DataFrame) -> float:
    if "funnel_is_successful" not in df.columns:
        return 0.0
    try:
        return df["funnel_is_successful"].astype(float).mean() * 100
    except Exception:
        return 0.0


def _avg_agent_score(df: pd.DataFrame) -> Optional[float]:
    if "agent_overall_score" not in df.columns:
        return None
    try:
        v = pd.to_numeric(df["agent_overall_score"], errors="coerce").mean()
        return float(v) if pd.notna(v) else None
    except Exception:
        return None


# ============================================================
# LEGACY ALIASES (giữ backward-compat với tab files cũ)
# ============================================================
def _render_summary_table(filtered: pd.DataFrame, key_prefix: str):
    """[Legacy] Redirect → không cần nữa, nhưng giữ để tránh ImportError."""
    pass


def _render_conversation_detail_viewer(filtered: pd.DataFrame, key_prefix: str):
    """[Legacy] Redirect → dùng render_drill_down_panel thay thế."""
    pass


def _colorize_value(col: str, val: str) -> str:
    """[Legacy] Color-code giá trị AI cho hiển thị inline."""
    val_lower = val.lower().strip()
    if col in ("sentiment_overall", "sentiment_start", "sentiment_end"):
        icons = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}
        return f"{icons.get(val_lower, '⚪')} {val}"
    if col == "urgency_level":
        icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        return f"{icons.get(val_lower, '⚪')} {val}"
    if col in ("funnel_is_successful", "sarcasm_flag", "likely_to_return"):
        if val_lower in ("true", "1", "1.0", "yes"):
            return "✅ Có"
        elif val_lower in ("false", "0", "0.0", "no"):
            return "❌ Không"
    if "score" in col:
        try:
            n = float(val)
            return ("🟢 " if n >= 7 else "🟡 " if n >= 4 else "🔴 ") + val
        except ValueError:
            pass
    if col == "disc_primary":
        icons = {"D": "🔴", "I": "🟡", "S": "🟢", "C": "🔵"}
        return f"{icons.get(val.upper(), '⚪')} {val}"
    return val
